[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (Test-Path Variable:\PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$skillRoot = Split-Path -Parent $PSScriptRoot
$supervisor = Join-Path $skillRoot 'scripts\long-run-supervisor.ps1'
$fixtureRoot = Join-Path $skillRoot ('.fan-in-smoke-' + [Guid]::NewGuid().ToString('N'))
$taskRoot = Join-Path $fixtureRoot 'tasks'
$watchRoot = Join-Path $fixtureRoot 'watch-sets'
$hostPath = (Get-Process -Id $PID).Path
$launches = @()
$cleanupSafe = $false

function Invoke-WaitMany {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $output = @(& $hostPath -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $supervisor `
        -Action WaitMany -WatchSetDirectory $Directory -PollSeconds 2 -CompletedExitCode 0)
    [pscustomobject]@{
        Output = $output
        WrapperExitCode = $LASTEXITCODE
        Event = (($output -join "`n") | ConvertFrom-Json -Depth 30)
    }
}

try {
    $first = & $supervisor -Action Start -Command 'Start-Sleep -Seconds 2; exit 0' `
        -TaskRoot $taskRoot -ExpectedMinutes 5 -DeadlineMinutes 10 -StallMinutes 5 -HeartbeatSeconds 2 | ConvertFrom-Json
    $second = & $supervisor -Action Start -Command 'Start-Sleep -Seconds 8; exit 0' `
        -TaskRoot $taskRoot -ExpectedMinutes 5 -DeadlineMinutes 10 -StallMinutes 5 -HeartbeatSeconds 2 | ConvertFrom-Json
    $launches = @($first, $second)

    $generation1 = & $supervisor -Action CreateWatchSet `
        -TaskDirectory @($first.taskDirectory, $second.taskDirectory) `
        -WatchSetRoot $watchRoot -FanInMode AnyTerminal | ConvertFrom-Json -Depth 30
    $event1Result = Invoke-WaitMany $generation1.watchSetDirectory
    $event1 = $event1Result.Event
    if ($event1Result.WrapperExitCode -ne 0 -or $event1Result.Output.Count -ne 1 -or
        [string]$event1.condition -cne 'any_terminal' -or @($event1.receipts).Count -ne 1 -or
        @($event1.remaining).Count -ne 1) {
        throw 'AnyTerminal generation did not return one receipt and one remaining task.'
    }
    if ([string]$event1.watchSetManifestSha256 -cne [string]$generation1.manifestSha256) {
        throw 'AnyTerminal event manifest binding differs.'
    }
    $ack1 = & $supervisor -Action AckWatchEvent -WatchSetDirectory $generation1.watchSetDirectory `
        -EventId ([string]$event1.eventId) | ConvertFrom-Json -Depth 30
    if ([string]$ack1.eventId -cne [string]$event1.eventId -or [string]$ack1.cursor -cne [string]$event1.cursor) {
        throw 'Generation 1 acknowledgement differs from its event.'
    }

    $remainingDirectory = [string]@($event1.remaining)[0].taskDirectory
    $generation2 = & $supervisor -Action CreateWatchSet -TaskDirectory $remainingDirectory `
        -WatchSetRoot $watchRoot -FanInMode FailFastAll `
        -PreviousWatchSetDirectory $generation1.watchSetDirectory | ConvertFrom-Json -Depth 30
    $manifest2 = Get-Content -Raw -LiteralPath (Join-Path $generation2.watchSetDirectory 'watch-set.json') | ConvertFrom-Json -Depth 30
    if ([string]$generation2.watchGroupId -cne [string]$generation1.watchGroupId -or
        [int]$generation2.generation -ne 2 -or [string]$manifest2.previousGenerationId -cne [string]$generation1.generationId -or
        [string]$manifest2.previousCursor -cne [string]$event1.cursor) {
        throw 'Watch generation or cursor continuity differs after re-arm.'
    }

    $event2Result = Invoke-WaitMany $generation2.watchSetDirectory
    $event2 = $event2Result.Event
    if ($event2Result.WrapperExitCode -ne 0 -or $event2Result.Output.Count -ne 1 -or
        [string]$event2.condition -cne 'all_completed' -or @($event2.receipts).Count -ne 1 -or
        @($event2.remaining).Count -ne 0) {
        throw 'FailFastAll generation did not return all_completed.'
    }
    $ack2 = & $supervisor -Action AckWatchEvent -WatchSetDirectory $generation2.watchSetDirectory `
        -EventId ([string]$event2.eventId) | ConvertFrom-Json -Depth 30
    if ([string]$ack2.eventId -cne [string]$event2.eventId -or [string]$ack2.cursor -cne [string]$event2.cursor) {
        throw 'Generation 2 acknowledgement differs from its event.'
    }

    # Replay both now-terminal tasks in descending ID order. This proves event-ID
    # canonicalization is identical before and after JSON serialization when one
    # event contains multiple receipts.
    $terminalDirectories = @($launches | Sort-Object taskId -Descending | ForEach-Object taskDirectory)
    $generation3 = & $supervisor -Action CreateWatchSet -TaskDirectory $terminalDirectories `
        -WatchSetRoot $watchRoot -FanInMode FailFastAll `
        -PreviousWatchSetDirectory $generation2.watchSetDirectory | ConvertFrom-Json -Depth 30
    $event3Result = Invoke-WaitMany $generation3.watchSetDirectory
    $event3 = $event3Result.Event
    if ($event3Result.WrapperExitCode -ne 0 -or $event3Result.Output.Count -ne 1 -or
        [string]$event3.condition -cne 'all_completed' -or @($event3.receipts).Count -ne 2 -or
        @($event3.remaining).Count -ne 0) {
        throw 'Multi-receipt replay generation did not return all_completed.'
    }
    $ack3 = & $supervisor -Action AckWatchEvent -WatchSetDirectory $generation3.watchSetDirectory `
        -EventId ([string]$event3.eventId) | ConvertFrom-Json -Depth 30
    if ([string]$ack3.eventId -cne [string]$event3.eventId -or [string]$ack3.cursor -cne [string]$event3.cursor) {
        throw 'Generation 3 acknowledgement differs from its event.'
    }

    foreach ($launch in $launches) {
        $state = Get-Content -Raw -LiteralPath (Join-Path $launch.taskDirectory 'state.json') | ConvertFrom-Json
        if ([string]$state.status -cne 'completed' -or [bool]$state.commandMaterialPresent) {
            throw "Underlying task is not cleanly completed: $($launch.taskId)"
        }
        $worker = Get-Process -Id ([int]$state.workerPid) -ErrorAction SilentlyContinue
        if ($null -ne $worker) { Wait-Process -Id $worker.Id -Timeout 5 -ErrorAction SilentlyContinue }
        if ($null -ne (Get-Process -Id ([int]$state.workerPid) -ErrorAction SilentlyContinue)) {
            throw "Underlying worker remains active: $($state.workerPid)"
        }
    }

    $cleanupSafe = $true
    [ordered]@{
        status = 'PASS'
        generation1 = [ordered]@{mode='AnyTerminal';condition=[string]$event1.condition;receipts=@($event1.receipts).Count;remaining=@($event1.remaining).Count;eventId=[string]$event1.eventId}
        generation2 = [ordered]@{mode='FailFastAll';condition=[string]$event2.condition;receipts=@($event2.receipts).Count;remaining=@($event2.remaining).Count;eventId=[string]$event2.eventId}
        generation3 = [ordered]@{mode='FailFastAll';condition=[string]$event3.condition;receipts=@($event3.receipts).Count;remaining=@($event3.remaining).Count;eventId=[string]$event3.eventId}
        cursorChained = [string]$manifest2.previousCursor -ceq [string]$event1.cursor
        commandMaterialPresent = $false
    } | ConvertTo-Json -Depth 8 -Compress
}
finally {
    if ($cleanupSafe -and (Test-Path -LiteralPath $fixtureRoot -PathType Container)) {
        $resolvedSkill = [IO.Path]::GetFullPath($skillRoot).TrimEnd('\') + '\'
        $resolvedFixture = [IO.Path]::GetFullPath($fixtureRoot).TrimEnd('\')
        if (-not $resolvedFixture.StartsWith($resolvedSkill, [StringComparison]::OrdinalIgnoreCase) -or
            [IO.Path]::GetFileName($resolvedFixture) -notlike '.fan-in-smoke-*') {
            throw "Refusing cleanup of unexpected path: $resolvedFixture"
        }
        Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
    }
}

$global:LASTEXITCODE = 0
