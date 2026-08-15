[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$skillRoot = Split-Path -Parent $PSScriptRoot
$skillDocument = Get-Content -Raw -LiteralPath (Join-Path $skillRoot 'SKILL.md')
$agentMetadata = Get-Content -Raw -LiteralPath (Join-Path $skillRoot 'agents\openai.yaml')

foreach ($requiredText in @(
    '## Keep same-turn continuation inside one execution cell',
    'while (result.session_id !== undefined)',
    'tools.write_stdin',
    'await functions.wait',
    'Never fire-and-forget this continuation',
    'Do not use the default short continuation window',
    'If the turn emits `final`, the cell is not a wake',
    '## Native collaboration fan-in',
    'Never build a short `wait_agent` loop',
    '## Codex App deferred terminal delivery',
    '`notify` is deferred delivery',
    'must continue that exact cell',
    'Do not switch that cell to `notify`',
    'manufacture liveness with timer calls',
    '## Choose the continuation owner',
    'The supervisor owns process observation only',
    'Use Goal mode for a durable multi-hour or multi-day objective',
    'Use a same-chat heartbeat automation only when the user asks',
    'valid waiting mechanism',
    'Pause or stop the Goal through',
    'automatic resume and zero idle',
    '## Do not bridge into an App-owned task out of process',
    'runtime `thread.status` is process-local',
    'it cannot prove exactly-once continuation',
    'never spend Goal turns checking supervisor state',
    'not an event bridge',
    '## Transport-yield fallback',
    'same-cell path described above',
    'On a later user message or separately authorized continuation',
    '-Action Poll -TaskDirectory $launch.taskDirectory -CompletedExitCode 0',
    '## Optional idle-only fan-in',
    'only when the main agent has no useful independent work',
    'one immutable generation',
    '-Action WaitMany',
    '-Action AckWatchEvent',
    '`AnyTerminal`',
    '`FailFastAll`',
    'Goal is optional and never drives',
    'leave the tasks running without caller observation'
)) {
    if (-not $skillDocument.Contains($requiredText, [StringComparison]::Ordinal)) {
        throw "Wake-only transport contract is missing: $requiredText"
    }
}

foreach ($requiredText in @(
    '$long-run-supervisor',
    'Start plus Wait',
    'one calibrated blocking call',
    'native wait_agent directly',
    'only after useful work is exhausted',
    'never promise post-final wake',
    'allow_implicit_invocation: true'
)) {
    if (-not $agentMetadata.Contains($requiredText, [StringComparison]::Ordinal)) {
        throw "Agent metadata is stale: $requiredText"
    }
}

[pscustomobject]@{
    codexAppNotifyContract = 'passed'
    transportResumeFallbackContract = 'passed'
    metadata = 'current'
} | ConvertTo-Json -Compress
