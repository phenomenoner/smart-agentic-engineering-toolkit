[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (Test-Path Variable:\PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$skillRoot = Split-Path -Parent $PSScriptRoot
$supervisor = Join-Path $skillRoot 'scripts\long-run-supervisor.ps1'
$source = Join-Path $PSScriptRoot 'fixtures\command-file-byte-identity.ps1'
$fixtureRoot = Join-Path $skillRoot ('.command-file-smoke-' + [Guid]::NewGuid().ToString('N'))
$taskRoot = Join-Path $fixtureRoot 'tasks'
$hostPath = (Get-Process -Id $PID).Path
$cleanupSafe = $false

try {
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $launch = & $supervisor -Action Start -CommandFile $source -TaskRoot $taskRoot `
        -ExpectedMinutes 5 -DeadlineMinutes 10 -StallMinutes 5 -HeartbeatSeconds 2 | ConvertFrom-Json
    $waitOutput = @(& $hostPath -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $supervisor `
        -Action Wait -TaskDirectory $launch.taskDirectory -CompletedExitCode 0)
    if ($LASTEXITCODE -ne 0 -or $waitOutput.Count -ne 1) { throw 'Command-file identity task did not complete.' }
    $receipt = (($waitOutput -join "`n") | ConvertFrom-Json)
    if ([string]$receipt.condition -cne 'completed') { throw 'Command-file identity task returned a non-completed receipt.' }

    $stdoutPath = Join-Path $launch.taskDirectory 'stdout.log'
    $matches = @([regex]::Matches([IO.File]::ReadAllText($stdoutPath), '(?m)^COMMAND_FILE_SHA256=(?<hash>[A-F0-9]{64})\r?$'))
    if ($matches.Count -ne 1 -or [string]$matches[0].Groups['hash'].Value -cne $sourceHash) {
        throw 'Private command-file bytes differ from the supplied source.'
    }
    $state = Get-Content -Raw -LiteralPath (Join-Path $launch.taskDirectory 'state.json') | ConvertFrom-Json
    if ([string]$state.status -cne 'completed' -or [bool]$state.commandMaterialPresent) {
        throw 'Command-file identity task did not clean terminal command material.'
    }
    $cleanupSafe = $true
    [ordered]@{status='PASS';sourceSha256=$sourceHash;privateCopySha256=[string]$matches[0].Groups['hash'].Value;commandMaterialPresent=$false} | ConvertTo-Json -Compress
}
finally {
    if ($cleanupSafe -and (Test-Path -LiteralPath $fixtureRoot -PathType Container)) {
        $resolvedSkill = [IO.Path]::GetFullPath($skillRoot).TrimEnd('\') + '\'
        $resolvedFixture = [IO.Path]::GetFullPath($fixtureRoot).TrimEnd('\')
        if (-not $resolvedFixture.StartsWith($resolvedSkill, [StringComparison]::OrdinalIgnoreCase) -or
            [IO.Path]::GetFileName($resolvedFixture) -notlike '.command-file-smoke-*') {
            throw "Refusing cleanup of unexpected path: $resolvedFixture"
        }
        Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
    }
}

$global:LASTEXITCODE = 0
