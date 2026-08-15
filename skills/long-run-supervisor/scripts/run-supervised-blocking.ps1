[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $CommandFile,

    [ValidateRange(5, 10080)]
    [int] $ExpectedMinutes = 15,

    [ValidateRange(5, 20160)]
    [int] $DeadlineMinutes = 60,

    [ValidateRange(5, 1440)]
    [int] $StallMinutes = 15,

    [ValidateRange(1, 3600)]
    [int] $HeartbeatSeconds = 10,

    [string] $TaskRoot
)

$ErrorActionPreference = 'Stop'
$supervisor = Join-Path $PSScriptRoot 'long-run-supervisor.ps1'
$resolvedCommandFile = [IO.Path]::GetFullPath($CommandFile)

if (-not (Test-Path -LiteralPath $resolvedCommandFile -PathType Leaf)) {
    throw "Command file is absent or not a regular file: $resolvedCommandFile"
}

$startParameters = @{
    Action = 'Start'
    CommandFile = $resolvedCommandFile
    ExpectedMinutes = $ExpectedMinutes
    DeadlineMinutes = $DeadlineMinutes
    StallMinutes = $StallMinutes
    HeartbeatSeconds = $HeartbeatSeconds
}
if (-not [string]::IsNullOrWhiteSpace($TaskRoot)) {
    $startParameters.TaskRoot = [IO.Path]::GetFullPath($TaskRoot)
}

$started = [DateTimeOffset]::UtcNow
$launchOutput = @(& $supervisor @startParameters)
$launchSucceeded = $?
$launchExitCode = if ($launchSucceeded) { 0 } elseif ($null -ne $LASTEXITCODE) { [int] $LASTEXITCODE } else { 1 }
if (-not $launchSucceeded) {
    throw "Supervisor Start failed with exit $launchExitCode"
}

$launch = ($launchOutput -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
if ([string]::IsNullOrWhiteSpace([string] $launch.taskDirectory)) {
    throw 'Supervisor Start did not return a task directory.'
}

$waitOutput = @(
    & $supervisor `
        -Action Wait `
        -TaskDirectory ([string] $launch.taskDirectory) `
        -CompletedExitCode 0
)
$waitSucceeded = $?
$waitExitCode = if ($waitSucceeded) { 0 } elseif ($null -ne $LASTEXITCODE) { [int] $LASTEXITCODE } else { 1 }
$receipt = ($waitOutput -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
$ended = [DateTimeOffset]::UtcNow

[ordered]@{
    schemaVersion = 1
    kind = 'long-run-supervisor.blocking-run'
    startedUtc = $started.ToString('o')
    endedUtc = $ended.ToString('o')
    elapsedSeconds = [Math]::Round(($ended - $started).TotalSeconds, 3)
    launch = $launch
    receipt = $receipt
} | ConvertTo-Json -Depth 12

if ($waitExitCode -ne 0) {
    exit $waitExitCode
}
