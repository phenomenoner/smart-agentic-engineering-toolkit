[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $PromptPath,
    [Parameter(Mandatory = $true)][string] $JsonSchemaPath,
    [string] $OutputPath,
    [string] $InvocationReceiptPath,
    [string] $Model = 'claude-opus-5',
    [ValidateSet('low','medium','high','xhigh','max')][string] $Effort = 'high',
    [AllowEmptyString()][string] $Tools = 'Read,Glob,Grep',
    [string] $ClaudePath = 'claude',
    [string] $PwshPath = 'pwsh'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Resolve-ExecutablePath([string] $Value, [string] $Label) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "$Label executable path is required" }
    $pathLike = $Value -match '^(?:[A-Za-z]:[\\/]|[\\/]{2})' -or $Value.Contains('\') -or $Value.Contains('/')
    if ($pathLike) {
        $full = [IO.Path]::GetFullPath($Value)
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "$Label executable is missing: $full" }
        return $full
    }
    $command = Get-Command -Name $Value -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) { throw "$Label executable was not found on PATH: $Value" }
    $resolved = [string]$command.Source
    if ([string]::IsNullOrWhiteSpace($resolved)) { $resolved = [string]$command.Path }
    if ([string]::IsNullOrWhiteSpace($resolved)) { throw "$Label executable has no filesystem path: $Value" }
    return [IO.Path]::GetFullPath($resolved)
}

if ($PSVersionTable.PSEdition -ne 'Core') {
    $PwshPath = Resolve-ExecutablePath $PwshPath 'PowerShell'
    $forwardTools = if ([string]::IsNullOrEmpty($Tools)) { '__CLAUDE_NO_TOOLS__' } else { $Tools }
    $forward = @(
        '-NoLogo','-NoProfile','-File',$PSCommandPath,
        '-PromptPath',$PromptPath,
        '-JsonSchemaPath',$JsonSchemaPath,
        '-Model',$Model,
        '-Effort',$Effort,
        '-Tools',$forwardTools,
        '-ClaudePath',$ClaudePath,
        '-PwshPath',$PwshPath
    )
    if (-not [string]::IsNullOrWhiteSpace($OutputPath)) { $forward += @('-OutputPath',$OutputPath) }
    if (-not [string]::IsNullOrWhiteSpace($InvocationReceiptPath)) { $forward += @('-InvocationReceiptPath',$InvocationReceiptPath) }
    & $PwshPath @forward
    $childExitCode = $LASTEXITCODE
    if ($childExitCode -ne 0) { throw "PowerShell 7 Claude wrapper exited $childExitCode" }
    return
}

$ClaudePath = Resolve-ExecutablePath $ClaudePath 'Claude'

foreach ($inputFile in @($PromptPath,$JsonSchemaPath,$ClaudePath)) {
    if (-not (Test-Path -LiteralPath $inputFile -PathType Leaf)) { throw "Required file is missing: $inputFile" }
}
if (-not [string]::IsNullOrWhiteSpace($OutputPath) -and (Test-Path -LiteralPath $OutputPath)) {
    throw "Claude output already exists: $OutputPath"
}
if (-not [string]::IsNullOrWhiteSpace($InvocationReceiptPath) -and (Test-Path -LiteralPath $InvocationReceiptPath)) {
    throw "Claude invocation receipt already exists: $InvocationReceiptPath"
}
if (-not [string]::IsNullOrWhiteSpace($OutputPath) -and -not [string]::IsNullOrWhiteSpace($InvocationReceiptPath) -and [IO.Path]::GetFullPath($OutputPath).Equals([IO.Path]::GetFullPath($InvocationReceiptPath),[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Claude output and invocation receipt paths must differ'
}

function Get-FileIdentity([string] $Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $item = Get-Item -LiteralPath $full -Force
    [ordered]@{path=$full;length=[int64]$item.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash.ToUpperInvariant()}
}

function Get-BytesSha256([byte[]] $Bytes) {
    ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))).ToUpperInvariant()
}

function Write-InvocationReceipt([string] $Status, [string] $TerminalClassifier, [int] $ExitCode, [string] $Stdout, [string] $Stderr, $EnvelopeSummary) {
    if ([string]::IsNullOrWhiteSpace($InvocationReceiptPath)) { return }
    $finishedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
    $receipt = [ordered]@{
        schema='codex.claude-readonly-review-invocation.v1'
        status=$Status
        provider='anthropic'
        model=$Model
        effort=$Effort
        tools=$effectiveTools
        safety=[ordered]@{safeMode=$true;sessionPersistence=$false;permissionMode='plan'}
        startedAtUtc=$script:claudeInvocationStartedAtUtc
        finishedAtUtc=$finishedAtUtc
        exitCode=$ExitCode
        terminalClassifier=$TerminalClassifier
        commandDescriptorSha256=$script:claudeCommandDescriptorSha256
        wrapper=$script:claudeWrapperIdentity
        executable=$script:claudeExecutableIdentity
        prompt=$script:claudePromptIdentity
        jsonSchema=$script:claudeSchemaIdentity
        stdout=[ordered]@{length=[int64]([Text.UTF8Encoding]::new($false).GetByteCount($Stdout));sha256=Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($Stdout))}
        stderr=[ordered]@{length=[int64]([Text.UTF8Encoding]::new($false).GetByteCount($Stderr));sha256=Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($Stderr))}
        envelope=$EnvelopeSummary
        payloadsRedacted=$true
    }
    $full = [IO.Path]::GetFullPath($InvocationReceiptPath)
    $parent = Split-Path -Parent $full
    if ([string]::IsNullOrWhiteSpace($parent)) { throw 'Claude invocation receipt has no parent directory' }
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($receipt | ConvertTo-Json -Depth 12 -Compress) + "`n")
    $stream = [IO.FileStream]::new($full,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}

$prompt = Get-Content -Raw -LiteralPath $PromptPath
$schemaObject = Get-Content -Raw -LiteralPath $JsonSchemaPath | ConvertFrom-Json
$schemaObject.PSObject.Properties.Remove('$schema')
$schemaObject.PSObject.Properties.Remove('$id')
$schema = $schemaObject | ConvertTo-Json -Depth 100 -Compress
$effectiveTools = if ($Tools -ceq '__CLAUDE_NO_TOOLS__') { '' } else { $Tools }
$script:claudeInvocationStartedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
$script:claudeWrapperIdentity = Get-FileIdentity $PSCommandPath
$script:claudeExecutableIdentity = Get-FileIdentity $ClaudePath
$script:claudePromptIdentity = Get-FileIdentity $PromptPath
$script:claudeSchemaIdentity = Get-FileIdentity $JsonSchemaPath
$commandDescriptor = [ordered]@{
    executable=$script:claudeExecutableIdentity
    arguments=@('-p','--model',$Model,'--effort',$Effort,'--safe-mode','--no-session-persistence','--permission-mode','plan','--tools',$effectiveTools,'--output-format','json','--json-schema',('sha256:' + (Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes($schema)))),('prompt-sha256:' + [string]$script:claudePromptIdentity.sha256))
}
$script:claudeCommandDescriptorSha256 = Get-BytesSha256 ([Text.UTF8Encoding]::new($false).GetBytes(($commandDescriptor | ConvertTo-Json -Depth 10 -Compress)))

$start = [Diagnostics.ProcessStartInfo]::new()
$start.FileName = [IO.Path]::GetFullPath($ClaudePath)
$start.UseShellExecute = $false
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$start.CreateNoWindow = $true
foreach ($argument in @(
    '-p',
    '--model',$Model,
    '--effort',$Effort,
    '--safe-mode',
    '--no-session-persistence',
    '--permission-mode','plan',
    '--tools',$effectiveTools,
    '--output-format','json',
    '--json-schema',$schema,
    $prompt
)) {
    [void]$start.ArgumentList.Add([string]$argument)
}

$process = [Diagnostics.Process]::new()
$process.StartInfo = $start
if (-not $process.Start()) { throw 'Claude process did not start' }
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
$exitCode = $process.ExitCode
$process.Dispose()

if ($exitCode -ne 0) {
    $failure = ($stderr + "`n" + $stdout).Trim()
    $label = if ($failure -match "(?i)(you(?:'|’)ve\s+hit\s+your\s+(session|usage|quota)\s+limit|(session|usage|quota)\s+(limit|cap)(?:\s+(reached|exceeded))?|rate[_ -]?limit[^\r\n]{0,80}(reached|exceeded))") { 'CLAUDE_QUOTA_LIMIT' } else { 'CLAUDE_REVIEW_FAILED' }
    $failureEnvelope = $null
    try {
        $parsedFailureEnvelope = $stdout | ConvertFrom-Json -ErrorAction Stop
        $failureEnvelope = [ordered]@{apiErrorStatus=$parsedFailureEnvelope.api_error_status;terminalReason=[string]$parsedFailureEnvelope.terminal_reason;subtype=[string]$parsedFailureEnvelope.subtype;isError=[bool]$parsedFailureEnvelope.is_error}
    } catch {
        $failureEnvelope = [ordered]@{apiErrorStatus=$null;terminalReason=$null;subtype=$null;isError=$true}
    }
    Write-InvocationReceipt -Status $label -TerminalClassifier $label -ExitCode $exitCode -Stdout $stdout -Stderr $stderr -EnvelopeSummary $failureEnvelope
    if ($failure.Length -gt 2000) { $failure = $failure.Substring(0,2000) }
    throw "${label}: exit $exitCode; $failure"
}
if (-not [string]::IsNullOrWhiteSpace($stderr)) {
    Write-InvocationReceipt -Status 'CLAUDE_REVIEW_FAILED' -TerminalClassifier 'UNEXPECTED_STDERR' -ExitCode $exitCode -Stdout $stdout -Stderr $stderr -EnvelopeSummary $null
    throw "Claude wrote unexpected stderr: $stderr"
}

$envelope = $stdout | ConvertFrom-Json
if ([bool]$envelope.is_error -or [string]$envelope.subtype -cne 'success' -or [string]$envelope.terminal_reason -cne 'completed') {
    throw 'Claude returned a non-success JSON envelope'
}
$usage = $envelope.modelUsage.PSObject.Properties[$Model]
if ($null -eq $usage -or [string]$usage.Value.canonicalModel -cne $Model) {
    throw "Claude result does not contain canonical model usage for $Model"
}
if ($null -eq $envelope.structured_output) { throw 'Claude result has no structured_output' }
$reportText = [string]$envelope.result
if ([string]::IsNullOrWhiteSpace($reportText)) { throw 'Claude result has no report text' }
$reportObject = $reportText | ConvertFrom-Json
$structuredText = $envelope.structured_output | ConvertTo-Json -Depth 100 -Compress
$reportCanonical = $reportObject | ConvertTo-Json -Depth 100 -Compress
if ($structuredText -cne $reportCanonical) { throw 'Claude result and structured_output differ' }
Write-InvocationReceipt -Status 'COMPLETED' -TerminalClassifier 'CLAUDE_REVIEW_COMPLETED' -ExitCode $exitCode -Stdout $stdout -Stderr $stderr -EnvelopeSummary ([ordered]@{apiErrorStatus=$null;terminalReason=[string]$envelope.terminal_reason;subtype=[string]$envelope.subtype;isError=[bool]$envelope.is_error;canonicalModel=[string]$usage.Value.canonicalModel})

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $fullOutput = [IO.Path]::GetFullPath($OutputPath)
    $parent = Split-Path -Parent $fullOutput
    if ([string]::IsNullOrWhiteSpace($parent)) { throw 'Claude output has no parent directory' }
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($reportText)
    $stream = [IO.FileStream]::new($fullOutput,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    } finally {
        $stream.Dispose()
    }
}

$reportText
