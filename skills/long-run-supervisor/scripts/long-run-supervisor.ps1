[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Start', 'Poll', 'Wait', 'Interrupt', 'Worker', 'CreateWatchSet', 'PollMany', 'WaitMany', 'AckWatchEvent')]
    [string]$Action,

    [string]$Command,
    [string]$CommandFile,
    [string]$TaskRoot,
    [string[]]$TaskDirectory,
    [string]$WatchSetRoot,
    [string]$WatchSetDirectory,
    [string]$PreviousWatchSetDirectory,
    [ValidateSet('AnyTerminal', 'FailFastAll')]
    [string]$FanInMode = 'AnyTerminal',
    [string]$EventId,
    [ValidateRange(5, 10080)]
    [int]$ExpectedMinutes = 15,
    [ValidateRange(0, 40320)]
    [int]$DeadlineMinutes = 0,
    [ValidateRange(0, 1440)]
    [int]$StallMinutes = 0,
    [ValidateRange(2, 300)]
    [int]$HeartbeatSeconds = 5,
    [ValidateRange(2, 3600)]
    [int]$PollSeconds = 15,
    [ValidateSet(0, 10)]
    [int]$CompletedExitCode = 10,
    [switch]$AsJson
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:SchemaVersion = 1
$script:ExitCodes = @{
    completed   = 10
    failed      = 11
    stalled     = 12
    deadline    = 13
    interrupted = 14
}

function Get-UtcNowText {
    [DateTimeOffset]::UtcNow.ToString('o')
}

function Resolve-AbsolutePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'Path must not be empty.' }
    [IO.Path]::GetFullPath($Path)
}

function Assert-SafeRoot {
    param([Parameter(Mandatory = $true)][string]$Path)
    $resolved = Resolve-AbsolutePath $Path
    if ($resolved.StartsWith('\\')) { throw "Task root must not be a network path: $resolved" }
    $root = [IO.Path]::GetPathRoot($resolved).TrimEnd('\')
    if ($resolved.TrimEnd('\') -eq $root) { throw "Task root must not be a drive root: $resolved" }
    $probe = $resolved
    while (-not (Test-Path -LiteralPath $probe)) {
        $parent = Split-Path -Parent $probe
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $probe) { break }
        $probe = $parent
    }
    while (Test-Path -LiteralPath $probe) {
        $ancestor = Get-Item -LiteralPath $probe -Force
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Task path must not traverse a reparse point: $($ancestor.FullName)"
        }
        $parent = Split-Path -Parent $ancestor.FullName
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $ancestor.FullName) { break }
        $probe = $parent
    }
    if (Test-Path -LiteralPath $resolved) {
        $item = Get-Item -LiteralPath $resolved -Force
        if (-not $item.PSIsContainer) { throw "Task root is not a directory: $resolved" }
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Task root must not be a reparse point: $resolved"
        }
        if (Test-Path -LiteralPath (Join-Path $resolved '.git')) {
            throw "Task root must not be a repository root: $resolved"
        }
    }
    $resolved
}

function Resolve-PrivateTaskDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $resolved = Assert-SafeRoot $Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Container)) { throw "Task directory does not exist: $resolved" }
    $acl = Get-Acl -LiteralPath $resolved
    if (-not $acl.AreAccessRulesProtected) { throw "Task directory ACL inheritance is enabled: $resolved" }
    $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $allowedSids = @($currentSid, 'S-1-5-18')
    $rules = $acl.GetAccessRules($true, $true, [Security.Principal.SecurityIdentifier])
    foreach ($rule in $rules) {
        if ($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and $allowedSids -notcontains $rule.IdentityReference.Value) {
            throw "Task directory grants access to an unexpected SID: $($rule.IdentityReference.Value)"
        }
    }
    $resolved
}

function Get-SingleTaskDirectory {
    $values = @($TaskDirectory)
    if ($values.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$values[0])) {
        throw "$Action requires exactly one -TaskDirectory."
    }
    [string]$values[0]
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $temporary = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    $backup = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).replace-backup"
    try {
        $json = $Value | ConvertTo-Json -Depth 12 -Compress
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json)
        $stream = [IO.FileStream]::new(
            $temporary,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None,
            4096,
            [IO.FileOptions]::WriteThrough
        )
        try {
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush($true)
        }
        finally {
            $stream.Dispose()
            [Array]::Clear($bytes, 0, $bytes.Length)
        }

        # File.Replace gives readers an old-or-new view with no missing-file
        # window. The non-null same-directory backup avoids PowerShell's null
        # argument conversion and is removed best-effort after publication.
        # A foreign reader may temporarily omit FileShare.Delete, so retry that
        # transient IOException without ever publishing a partial destination.
        $maximumAttempts = 100
        for ($attempt = 1; $attempt -le $maximumAttempts; $attempt++) {
            try {
                if ([IO.File]::Exists($Path)) {
                    [IO.File]::Replace($temporary, $Path, $backup)
                }
                else {
                    [IO.File]::Move($temporary, $Path)
                }
                return
            }
            catch [IO.IOException] {
                if ($attempt -eq $maximumAttempts) { throw }
                Start-Sleep -Milliseconds 25
            }
        }
    }
    finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
        if (Test-Path -LiteralPath $backup) {
            try { Remove-Item -LiteralPath $backup -Force -ErrorAction Stop } catch { }
        }
    }
}

function Write-JsonCreateOnce {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $temporary = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        $json = $Value | ConvertTo-Json -Depth 30 -Compress
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json)
        $stream = [IO.FileStream]::new(
            $temporary,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None,
            4096,
            [IO.FileOptions]::WriteThrough
        )
        try {
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush($true)
        }
        finally {
            $stream.Dispose()
            [Array]::Clear($bytes, 0, $bytes.Length)
        }
        [IO.File]::Move($temporary, $Path)
    }
    finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Get-TextSha256 {
    param([Parameter(Mandatory = $true)][string]$Text)
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose(); [Array]::Clear($bytes, 0, $bytes.Length) }
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)
    $share = [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete
    $maximumAttempts = 100
    $stream = $null
    for ($attempt = 1; $attempt -le $maximumAttempts; $attempt++) {
        try {
            $stream = [IO.FileStream]::new($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, $share)
            break
        }
        catch [IO.IOException] {
            if ($attempt -eq $maximumAttempts) { throw }
            Start-Sleep -Milliseconds 10
        }
    }
    try {
        $reader = [IO.StreamReader]::new($stream, [Text.UTF8Encoding]::new($false), $true)
        try { $raw = $reader.ReadToEnd() }
        finally { $reader.Dispose() }
    }
    finally { $stream.Dispose() }
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $raw | ConvertFrom-Json -DateKind String
    }
    else { $raw | ConvertFrom-Json }
}

function Get-PowerShellHostPath {
    $current = (Get-Process -Id $PID).Path
    if ([IO.Path]::GetFileName($current) -in @('pwsh.exe', 'powershell.exe')) { return $current }
    foreach ($candidate in @('pwsh.exe', 'powershell.exe')) {
        $commandInfo = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $commandInfo) { return $commandInfo.Source }
    }
    throw 'Cannot locate pwsh.exe or powershell.exe.'
}

function Add-WalEvent {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Event,
        [Parameter(Mandatory = $true)]$Data
    )
    $record = [ordered]@{
        schemaVersion = $script:SchemaVersion
        utc = Get-UtcNowText
        event = $Event
        data = $Data
    } | ConvertTo-Json -Depth 8 -Compress
    Add-Content -LiteralPath (Join-Path $Directory 'events.jsonl') -Value $record -Encoding UTF8
}

function Set-PrivateTaskAcl {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($null -eq $identity.User) { throw 'Cannot resolve the current Windows SID.' }
    $systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true, $false)
    $inheritance = [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    $propagation = [Security.AccessControl.PropagationFlags]::None
    $allow = [Security.AccessControl.AccessControlType]::Allow
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($identity.User, 'FullControl', $inheritance, $propagation, $allow))
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($systemSid, 'FullControl', $inheritance, $propagation, $allow))
    Set-Acl -LiteralPath $Directory -AclObject $acl
}

function Get-ProcessIdentity {
    param(
        [Parameter(Mandatory = $true)][int]$Id,
        [Parameter(Mandatory = $true)][string]$ExpectedStartUtc
    )
    try {
        $process = Get-Process -Id $Id -ErrorAction Stop
        $actual = [DateTimeOffset]$process.StartTime.ToUniversalTime()
        $expected = [DateTimeOffset]::Parse($ExpectedStartUtc)
        if ([Math]::Abs(($actual - $expected).TotalSeconds) -gt 2) { return $null }
        $process
    }
    catch { $null }
}

function Get-TreeMetrics {
    param(
        [Parameter(Mandatory = $true)][int]$RootPid,
        [Parameter(Mandatory = $true)][string]$RootStartUtc
    )
    $rootProcess = Get-ProcessIdentity -Id $RootPid -ExpectedStartUtc $RootStartUtc
    if ($null -eq $rootProcess) {
        return [pscustomobject]@{ Pids = @(); CpuSeconds = 0.0 }
    }

    $ids = [Collections.Generic.HashSet[int]]::new()
    [void]$ids.Add($RootPid)
    try {
        $rows = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, CreationDate -ErrorAction Stop)
        $minimum = [DateTimeOffset]::Parse($RootStartUtc).UtcDateTime.AddSeconds(-2)
        $changed = $true
        while ($changed) {
            $changed = $false
            foreach ($row in $rows) {
                $pidValue = [int]$row.ProcessId
                $parentValue = [int]$row.ParentProcessId
                if (-not $ids.Contains($pidValue) -and $ids.Contains($parentValue)) {
                    $created = if ($row.CreationDate -is [DateTime]) {
                        ([DateTime]$row.CreationDate).ToUniversalTime()
                    }
                    elseif ($row.CreationDate -is [DateTimeOffset]) {
                        ([DateTimeOffset]$row.CreationDate).UtcDateTime
                    }
                    elseif ($null -ne $row.CreationDate) {
                        [Management.ManagementDateTimeConverter]::ToDateTime([string]$row.CreationDate).ToUniversalTime()
                    }
                    else { $minimum }
                    if ($created -ge $minimum) {
                        [void]$ids.Add($pidValue)
                        $changed = $true
                    }
                }
            }
        }
    }
    catch {
        # Root identity remains sufficient for a conservative CPU heartbeat.
    }

    $cpu = 0.0
    foreach ($id in @($ids)) {
        try { $cpu += [double](Get-Process -Id $id -ErrorAction Stop).CPU } catch { }
    }
    [pscustomobject]@{ Pids = @($ids); CpuSeconds = $cpu }
}

function Stop-OwnedTree {
    param(
        [Parameter(Mandatory = $true)][int]$RootPid,
        [Parameter(Mandatory = $true)][string]$RootStartUtc
    )
    $metrics = Get-TreeMetrics -RootPid $RootPid -RootStartUtc $RootStartUtc
    if ($metrics.Pids.Count -eq 0) { return $false }
    $descendants = @($metrics.Pids | Where-Object { $_ -ne $RootPid } | Sort-Object -Descending)
    foreach ($id in $descendants) {
        try { Stop-Process -Id $id -Force -ErrorAction Stop } catch { }
    }
    $verifiedRoot = Get-ProcessIdentity -Id $RootPid -ExpectedStartUtc $RootStartUtc
    if ($null -ne $verifiedRoot) { Stop-Process -Id $RootPid -Force -ErrorAction Stop }
    $true
}

function Get-FileLength {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return [int64](Get-Item -LiteralPath $Path).Length }
    [int64]0
}

function Write-Wake {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Condition,
        [Parameter(Mandatory = $true)][string]$Reason
    )
    $wake = [ordered]@{
        schemaVersion = $script:SchemaVersion
        taskId = [string]$State.taskId
        blindedCommandDigest = [string]$State.blindedCommandDigest
        condition = $Condition
        reason = $Reason
        observedUtc = Get-UtcNowText
        exitCode = $State.exitCode
        taskDirectory = $Directory
    }
    Write-JsonAtomic -Path (Join-Path $Directory 'wake.json') -Value $wake
    [pscustomobject]$wake
}

function Get-WakeDecision {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $statePath = Join-Path $Directory 'state.json'
    try {
        $state = Read-JsonFile $statePath
        if ([int]$state.schemaVersion -ne $script:SchemaVersion) { throw 'Unsupported state schema.' }
        if ([string]::IsNullOrWhiteSpace([string]$state.taskId)) { throw 'State has no taskId.' }
        $requiredProperties = @('blindedCommandDigest', 'status', 'reason', 'createdUtc', 'deadlineUtc', 'heartbeatIntervalSeconds', 'heartbeatUtc', 'workerPid', 'workerStartUtc', 'exitCode')
        foreach ($property in $requiredProperties) {
            if ($state.PSObject.Properties.Name -notcontains $property) { throw "State is missing required property: $property" }
        }
    }
    catch {
        $fallback = [pscustomobject]@{ taskId = 'unknown'; blindedCommandDigest = 'unknown'; exitCode = $null }
        $wake = Write-Wake -Directory $Directory -State $fallback -Condition 'failed' -Reason ('invalid_state: ' + $_.Exception.Message)
        return [pscustomobject]@{ Wake = $true; ExitCode = 11; WakeRecord = $wake; State = $null }
    }

    $wakePath = Join-Path $Directory 'wake.json'
    if (Test-Path -LiteralPath $wakePath -PathType Leaf) {
        try {
            $existingWake = Read-JsonFile $wakePath
            if ([string]$existingWake.taskId -eq [string]$state.taskId -and $script:ExitCodes.ContainsKey([string]$existingWake.condition)) {
                return [pscustomobject]@{ Wake = $true; ExitCode = $script:ExitCodes[[string]$existingWake.condition]; WakeRecord = $existingWake; State = $state }
            }
        }
        catch { }
    }

    $status = [string]$state.status
    if ($script:ExitCodes.ContainsKey($status)) {
        $wake = Write-Wake -Directory $Directory -State $state -Condition $status -Reason ([string]$state.reason)
        return [pscustomobject]@{ Wake = $true; ExitCode = $script:ExitCodes[$status]; WakeRecord = $wake; State = $state }
    }

    $now = [DateTimeOffset]::UtcNow
    if ($now -ge [DateTimeOffset]::Parse([string]$state.deadlineUtc)) {
        $wake = Write-Wake -Directory $Directory -State $state -Condition 'deadline' -Reason 'deadline_observed_by_poll'
        return [pscustomobject]@{ Wake = $true; ExitCode = 13; WakeRecord = $wake; State = $state }
    }

    if ([int]$state.workerPid -le 0 -or [string]::IsNullOrWhiteSpace([string]$state.workerStartUtc)) {
        $launchAge = ($now - [DateTimeOffset]::Parse([string]$state.createdUtc)).TotalSeconds
        if ($launchAge -le 60) {
            return [pscustomobject]@{ Wake = $false; ExitCode = 0; WakeRecord = $null; State = $state }
        }
        $wake = Write-Wake -Directory $Directory -State $state -Condition 'stalled' -Reason 'worker_launch_stale'
        return [pscustomobject]@{ Wake = $true; ExitCode = 12; WakeRecord = $wake; State = $state }
    }

    $worker = Get-ProcessIdentity -Id ([int]$state.workerPid) -ExpectedStartUtc ([string]$state.workerStartUtc)
    if ($null -eq $worker) {
        $wake = Write-Wake -Directory $Directory -State $state -Condition 'stalled' -Reason 'worker_identity_lost'
        return [pscustomobject]@{ Wake = $true; ExitCode = 12; WakeRecord = $wake; State = $state }
    }

    $heartbeatAge = ($now - [DateTimeOffset]::Parse([string]$state.heartbeatUtc)).TotalSeconds
    $staleAfter = [Math]::Max(30, 3 * [int]$state.heartbeatIntervalSeconds)
    if ($heartbeatAge -gt $staleAfter) {
        $wake = Write-Wake -Directory $Directory -State $state -Condition 'stalled' -Reason 'heartbeat_stale'
        return [pscustomobject]@{ Wake = $true; ExitCode = 12; WakeRecord = $wake; State = $state }
    }

    [pscustomobject]@{ Wake = $false; ExitCode = 0; WakeRecord = $null; State = $state }
}

function Get-BoundWatchTask {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $resolved = Resolve-PrivateTaskDirectory $Directory
    $state = Read-JsonFile (Join-Path $resolved 'state.json')
    if ([int]$state.schemaVersion -ne $script:SchemaVersion) { throw "Task state schema is unsupported: $resolved" }
    $taskId = [string]$state.taskId
    $digest = [string]$state.blindedCommandDigest
    if ($taskId -cnotmatch '^[a-f0-9]{32}$') { throw "Task ID is invalid: $resolved" }
    if ($digest -cnotmatch '^hmac-sha256:[a-f0-9]{64}$') { throw "Task digest is invalid: $resolved" }
    [ordered]@{
        taskDirectory = $resolved
        taskId = $taskId
        blindedCommandDigest = $digest
    }
}

function Get-WatchSetContext {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $resolved = Resolve-PrivateTaskDirectory $Directory
    $leaf = [IO.Path]::GetFileName($resolved)
    if ($leaf -cnotmatch '^(?<generationId>[a-f0-9]{32})-(?<manifestSha>[a-f0-9]{64})$') {
        throw 'Watch-set directory name does not bind a generation ID and manifest SHA-256.'
    }
    $generationIdFromPath = [string]$Matches.generationId
    $manifestShaFromPath = [string]$Matches.manifestSha
    $manifestPath = Join-Path $resolved 'watch-set.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'Watch-set manifest is missing.' }
    $manifestSha = Get-FileSha256 $manifestPath
    if ($manifestSha -cne $manifestShaFromPath) { throw 'Watch-set manifest hash differs from the immutable directory binding.' }
    $manifest = Read-JsonFile $manifestPath
    if ([int]$manifest.schemaVersion -ne $script:SchemaVersion -or [string]$manifest.kind -cne 'long-run-supervisor.watch-set') {
        throw 'Watch-set manifest schema or kind is invalid.'
    }
    if ([string]$manifest.generationId -cne $generationIdFromPath) { throw 'Watch-set generation ID differs from its directory binding.' }
    if ([string]$manifest.watchGroupId -cnotmatch '^[a-f0-9]{32}$' -or [int]$manifest.generation -lt 1) {
        throw 'Watch-set group or generation is invalid.'
    }
    if ([string]$manifest.mode -notin @('AnyTerminal', 'FailFastAll')) { throw 'Watch-set fan-in mode is invalid.' }
    $tasks = @($manifest.tasks)
    if ($tasks.Count -lt 1) { throw 'Watch-set manifest has no tasks.' }
    $paths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($binding in $tasks) {
        $path = Resolve-AbsolutePath ([string]$binding.taskDirectory)
        if (-not $paths.Add($path)) { throw 'Watch-set manifest contains a duplicate task path.' }
        if ([string]$binding.taskId -cnotmatch '^[a-f0-9]{32}$' -or -not $ids.Add([string]$binding.taskId)) {
            throw 'Watch-set manifest contains an invalid or duplicate task ID.'
        }
        if ([string]$binding.blindedCommandDigest -cnotmatch '^hmac-sha256:[a-f0-9]{64}$') {
            throw 'Watch-set manifest contains an invalid task digest.'
        }
    }
    [pscustomobject]@{
        Directory = $resolved
        ManifestPath = $manifestPath
        ManifestSha256 = $manifestSha
        Manifest = $manifest
    }
}

function Get-WatchEventId {
    param(
        [Parameter(Mandatory = $true)]$Context,
        [Parameter(Mandatory = $true)][string]$Condition,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Receipts,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$InvalidBindings
    )
    # Project before sorting. Get-WatchObservation returns ordered dictionaries,
    # while a persisted event is read back as PSCustomObject. Sort-Object's
    # property-name form does not order those two representations identically.
    $receiptMaterial = @($Receipts | ForEach-Object {
        [pscustomobject][ordered]@{
            taskId = [string]$_.taskId
            blindedCommandDigest = [string]$_.blindedCommandDigest
            wakeReceiptSha256 = [string]$_.wakeReceiptSha256
        }
    } | Sort-Object taskId)
    $invalidMaterial = @($InvalidBindings | ForEach-Object {
        [pscustomobject][ordered]@{
            taskId = [string]$_.taskId
            blindedCommandDigest = [string]$_.blindedCommandDigest
            reason = [string]$_.reason
        }
    } | Sort-Object taskId)
    $material = [ordered]@{
        generationId = [string]$Context.Manifest.generationId
        watchSetManifestSha256 = [string]$Context.ManifestSha256
        condition = $Condition
        receipts = $receiptMaterial
        invalidBindings = $invalidMaterial
    }
    'sha256:' + (Get-TextSha256 ($material | ConvertTo-Json -Depth 12 -Compress))
}

function Get-ValidatedWatchEvent {
    param([Parameter(Mandatory = $true)]$Context)
    $eventPath = Join-Path $Context.Directory 'event.json'
    if (-not (Test-Path -LiteralPath $eventPath -PathType Leaf)) { throw 'Watch event is missing.' }
    $event = Read-JsonFile $eventPath
    if ([int]$event.schemaVersion -ne $script:SchemaVersion -or [string]$event.kind -cne 'long-run-supervisor.watch-event') {
        throw 'Watch event schema or kind is invalid.'
    }
    foreach ($field in @('watchGroupId', 'generation', 'generationId', 'mode')) {
        if ([string]$event.$field -cne [string]$Context.Manifest.$field) { throw "Watch event differs from its manifest: $field" }
    }
    if ([string]$event.watchSetManifestSha256 -cne [string]$Context.ManifestSha256) { throw 'Watch event manifest binding differs.' }
    if ([string]$event.condition -notin @('any_terminal', 'fail_fast', 'all_completed', 'invalid_watch_binding')) { throw 'Watch event condition is invalid.' }
    if (-not [bool]$event.ackRequired -or [string]$event.cursor -cne [string]$event.eventId) { throw 'Watch event acknowledgement contract is invalid.' }

    $bindingMap = @{}
    foreach ($binding in @($Context.Manifest.tasks)) { $bindingMap[[string]$binding.taskId]=$binding }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($record in @(@($event.receipts) + @($event.invalidBindings) + @($event.remaining))) {
        $taskId = [string]$record.taskId
        if (-not $bindingMap.ContainsKey($taskId) -or -not $seen.Add($taskId)) { throw 'Watch event task coverage is invalid or duplicated.' }
        $binding = $bindingMap[$taskId]
        if ([string]$record.blindedCommandDigest -cne [string]$binding.blindedCommandDigest -or
            -not ([string]$record.taskDirectory).Equals([string]$binding.taskDirectory, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Watch event task binding differs: $taskId"
        }
    }
    if ($seen.Count -ne @($Context.Manifest.tasks).Count) { throw 'Watch event does not cover every bound task exactly once.' }
    foreach ($receipt in @($event.receipts)) {
        if ([string]$receipt.condition -notin @($script:ExitCodes.Keys) -or [string]$receipt.wakeReceiptSha256 -cnotmatch '^[a-f0-9]{64}$') {
            throw 'Watch event contains an invalid wake receipt.'
        }
        if ([string]$receipt.wakeReceipt.taskId -cne [string]$receipt.taskId -or
            [string]$receipt.wakeReceipt.blindedCommandDigest -cne [string]$receipt.blindedCommandDigest -or
            [string]$receipt.wakeReceipt.condition -cne [string]$receipt.condition) {
            throw 'Watch event embedded wake receipt differs from its binding.'
        }
    }
    $expectedId = Get-WatchEventId -Context $Context -Condition ([string]$event.condition) -Receipts @($event.receipts) -InvalidBindings @($event.invalidBindings)
    if ([string]$event.eventId -cne $expectedId) { throw 'Watch event ID is invalid.' }
    $event
}

function Get-ValidatedWatchAck {
    param(
        [Parameter(Mandatory = $true)]$Context,
        [Parameter(Mandatory = $true)]$Event
    )
    $ackPath = Join-Path $Context.Directory 'ack.json'
    if (-not (Test-Path -LiteralPath $ackPath -PathType Leaf)) { throw 'Watch acknowledgement is missing.' }
    $ack = Read-JsonFile $ackPath
    if ([int]$ack.schemaVersion -ne $script:SchemaVersion -or [string]$ack.kind -cne 'long-run-supervisor.watch-ack') {
        throw 'Watch acknowledgement schema or kind is invalid.'
    }
    foreach ($field in @('watchGroupId', 'generation', 'generationId', 'eventId', 'cursor')) {
        $expected = if ($field -in @('eventId', 'cursor')) { [string]$Event.$field } else { [string]$Context.Manifest.$field }
        if ([string]$ack.$field -cne $expected) { throw "Watch acknowledgement differs: $field" }
    }
    $ack
}

function Get-WatchObservation {
    param([Parameter(Mandatory = $true)]$Binding)
    try {
        $directory = Resolve-PrivateTaskDirectory ([string]$Binding.taskDirectory)
        if (-not $directory.Equals([string]$Binding.taskDirectory, [StringComparison]::OrdinalIgnoreCase)) { throw 'Resolved task path differs.' }
        $decision = Get-WakeDecision -Directory $directory
        $state = $decision.State
        if ($null -eq $state -or [string]$state.taskId -cne [string]$Binding.taskId -or
            [string]$state.blindedCommandDigest -cne [string]$Binding.blindedCommandDigest) {
            throw 'Task state identity differs from the immutable watch binding.'
        }
        if (-not $decision.Wake) {
            return [ordered]@{
                kind = 'running'
                taskId = [string]$Binding.taskId
                blindedCommandDigest = [string]$Binding.blindedCommandDigest
                taskDirectory = $directory
                status = [string]$state.status
            }
        }
        $wakePath = Join-Path $directory 'wake.json'
        $shaBefore = Get-FileSha256 $wakePath
        $wake = Read-JsonFile $wakePath
        $shaAfter = Get-FileSha256 $wakePath
        if ($shaBefore -cne $shaAfter) { throw 'Wake receipt changed while it was being bound.' }
        if ([string]$wake.taskId -cne [string]$Binding.taskId -or
            [string]$wake.blindedCommandDigest -cne [string]$Binding.blindedCommandDigest -or
            [string]$wake.condition -notin @($script:ExitCodes.Keys) -or
            -not ([string]$wake.taskDirectory).Equals($directory, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Wake receipt identity differs from the immutable watch binding.'
        }
        [ordered]@{
            kind = 'receipt'
            taskId = [string]$Binding.taskId
            blindedCommandDigest = [string]$Binding.blindedCommandDigest
            taskDirectory = $directory
            condition = [string]$wake.condition
            wakeReceiptSha256 = $shaAfter
            wakeReceipt = $wake
        }
    }
    catch {
        [ordered]@{
            kind = 'invalid_binding'
            taskId = [string]$Binding.taskId
            blindedCommandDigest = [string]$Binding.blindedCommandDigest
            taskDirectory = [string]$Binding.taskDirectory
            reason = 'invalid_watch_binding: ' + $_.Exception.Message
        }
    }
}

function Publish-WatchEvent {
    param(
        [Parameter(Mandatory = $true)]$Context,
        [Parameter(Mandatory = $true)][string]$Condition,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Receipts,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$InvalidBindings,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Remaining
    )
    $eventPath = Join-Path $Context.Directory 'event.json'
    $eventId = Get-WatchEventId -Context $Context -Condition $Condition -Receipts $Receipts -InvalidBindings $InvalidBindings
    $event = [ordered]@{
        schemaVersion = $script:SchemaVersion
        kind = 'long-run-supervisor.watch-event'
        watchGroupId = [string]$Context.Manifest.watchGroupId
        generation = [int]$Context.Manifest.generation
        generationId = [string]$Context.Manifest.generationId
        watchSetManifestSha256 = [string]$Context.ManifestSha256
        mode = [string]$Context.Manifest.mode
        condition = $Condition
        observedUtc = Get-UtcNowText
        eventId = $eventId
        cursor = $eventId
        ackRequired = $true
        receipts = @($Receipts)
        invalidBindings = @($InvalidBindings)
        remaining = @($Remaining)
    }
    try { Write-JsonCreateOnce -Path $eventPath -Value $event }
    catch [IO.IOException] {
        if (-not (Test-Path -LiteralPath $eventPath -PathType Leaf)) { throw }
    }
    Get-ValidatedWatchEvent -Context $Context
}

function Get-WatchAggregateDecision {
    param([Parameter(Mandatory = $true)]$Context)
    $eventPath = Join-Path $Context.Directory 'event.json'
    $ackPath = Join-Path $Context.Directory 'ack.json'
    if (Test-Path -LiteralPath $ackPath -PathType Leaf) {
        if (-not (Test-Path -LiteralPath $eventPath -PathType Leaf)) { throw 'Acknowledged watch generation has no event.' }
        $event = Get-ValidatedWatchEvent -Context $Context
        [void](Get-ValidatedWatchAck -Context $Context -Event $event)
        throw 'watch_generation_acknowledged_rearm_required'
    }
    if (Test-Path -LiteralPath $eventPath -PathType Leaf) {
        return [pscustomobject]@{ Wake=$true; Event=(Get-ValidatedWatchEvent -Context $Context) }
    }

    $observations = @($Context.Manifest.tasks | ForEach-Object { Get-WatchObservation $_ } | Sort-Object taskId)
    $invalid = @($observations | Where-Object kind -ceq 'invalid_binding')
    $receipts = @($observations | Where-Object kind -ceq 'receipt')
    $remaining = @($observations | Where-Object kind -ceq 'running')
    $attention = @($receipts | Where-Object condition -cne 'completed')
    $allCompleted = $receipts.Count -eq $observations.Count -and $attention.Count -eq 0
    $condition = $null
    if ($invalid.Count -gt 0) { $condition = 'invalid_watch_binding' }
    elseif ([string]$Context.Manifest.mode -ceq 'AnyTerminal' -and $receipts.Count -gt 0) { $condition = 'any_terminal' }
    elseif ([string]$Context.Manifest.mode -ceq 'FailFastAll' -and $attention.Count -gt 0) { $condition = 'fail_fast' }
    elseif ([string]$Context.Manifest.mode -ceq 'FailFastAll' -and $allCompleted) { $condition = 'all_completed' }
    if ($null -eq $condition) { return [pscustomobject]@{ Wake=$false; Event=$null } }
    $event = Publish-WatchEvent -Context $Context -Condition $condition -Receipts $receipts -InvalidBindings $invalid -Remaining $remaining
    [pscustomobject]@{ Wake=$true; Event=$event }
}

function Emit-WatchEventAndExit {
    param([Parameter(Mandatory = $true)]$Event)
    $Event | ConvertTo-Json -Depth 30 -Compress | Write-Output
    if ([string]$Event.condition -ceq 'invalid_watch_binding') { exit 11 }
    $attention = @($Event.receipts | Where-Object condition -cne 'completed' | Sort-Object taskId)
    if ($attention.Count -gt 0) { exit $script:ExitCodes[[string]$attention[0].condition] }
    exit $CompletedExitCode
}

function Invoke-CreateWatchSetAction {
    $requestedTasks = @($TaskDirectory)
    if ($requestedTasks.Count -lt 1 -or @($requestedTasks | Where-Object { [string]::IsNullOrWhiteSpace([string]$_) }).Count -gt 0) {
        throw 'CreateWatchSet requires one or more -TaskDirectory values.'
    }
    if ([string]::IsNullOrWhiteSpace($WatchSetRoot)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is unavailable; specify -WatchSetRoot.' }
        $selectedRoot = Join-Path $env:LOCALAPPDATA 'Codex\long-run-supervisor\watch-sets'
    }
    else { $selectedRoot = $WatchSetRoot }
    $selectedRoot = Assert-SafeRoot $selectedRoot
    if (-not (Test-Path -LiteralPath $selectedRoot)) { New-Item -ItemType Directory -Path $selectedRoot -Force | Out-Null }

    $previous = $null
    if (-not [string]::IsNullOrWhiteSpace($PreviousWatchSetDirectory)) {
        $previousContext = Get-WatchSetContext $PreviousWatchSetDirectory
        $previousEvent = Get-ValidatedWatchEvent $previousContext
        $previousAck = Get-ValidatedWatchAck -Context $previousContext -Event $previousEvent
        $previous = [pscustomobject]@{
            WatchGroupId = [string]$previousContext.Manifest.watchGroupId
            Generation = [int]$previousContext.Manifest.generation
            GenerationId = [string]$previousContext.Manifest.generationId
            Cursor = [string]$previousAck.cursor
        }
    }

    $pathSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $idSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $bindings = @($requestedTasks | ForEach-Object {
        $binding = Get-BoundWatchTask ([string]$_)
        if (-not $pathSet.Add([string]$binding.taskDirectory)) { throw 'CreateWatchSet received a duplicate task path.' }
        if (-not $idSet.Add([string]$binding.taskId)) { throw 'CreateWatchSet received a duplicate task ID.' }
        $binding
    } | Sort-Object taskId)
    $watchGroupId = if ($null -eq $previous) { [Guid]::NewGuid().ToString('N') } else { $previous.WatchGroupId }
    $generation = if ($null -eq $previous) { 1 } else { $previous.Generation + 1 }
    $generationId = [Guid]::NewGuid().ToString('N')
    $manifest = [ordered]@{
        schemaVersion = $script:SchemaVersion
        kind = 'long-run-supervisor.watch-set'
        watchGroupId = $watchGroupId
        generation = $generation
        generationId = $generationId
        previousGenerationId = if ($null -eq $previous) { $null } else { $previous.GenerationId }
        previousCursor = if ($null -eq $previous) { $null } else { $previous.Cursor }
        createdUtc = Get-UtcNowText
        mode = $FanInMode
        tasks = $bindings
    }
    $manifestJson = $manifest | ConvertTo-Json -Depth 30 -Compress
    $manifestSha = Get-TextSha256 $manifestJson
    $directory = Join-Path $selectedRoot "$generationId-$manifestSha"
    if (Test-Path -LiteralPath $directory) { throw "Fresh watch-set directory already exists: $directory" }
    New-Item -ItemType Directory -Path $directory | Out-Null
    Set-PrivateTaskAcl $directory
    [void](Resolve-PrivateTaskDirectory $directory)
    $manifestPath = Join-Path $directory 'watch-set.json'
    Write-JsonCreateOnce -Path $manifestPath -Value $manifest
    if ((Get-FileSha256 $manifestPath) -cne $manifestSha) { throw 'Published watch-set manifest differs from its directory binding.' }
    [ordered]@{
        watchSetDirectory = $directory
        watchGroupId = $watchGroupId
        generation = $generation
        generationId = $generationId
        manifestSha256 = $manifestSha
        mode = $FanInMode
        tasks = $bindings
        waitManyCommand = "& '$PSCommandPath' -Action WaitMany -WatchSetDirectory '$directory' -CompletedExitCode 0"
    } | ConvertTo-Json -Depth 10 -Compress | Write-Output
}

function Invoke-ManyAction {
    param([Parameter(Mandatory = $true)][bool]$Block)
    if ([string]::IsNullOrWhiteSpace($WatchSetDirectory)) { throw "$Action requires -WatchSetDirectory." }
    while ($true) {
        $context = Get-WatchSetContext $WatchSetDirectory
        $decision = Get-WatchAggregateDecision $context
        if ($decision.Wake) { Emit-WatchEventAndExit $decision.Event }
        if (-not $Block) { exit 0 }
        Start-Sleep -Seconds $PollSeconds
    }
}

function Invoke-AckWatchEventAction {
    if ([string]::IsNullOrWhiteSpace($WatchSetDirectory) -or [string]::IsNullOrWhiteSpace($EventId)) {
        throw 'AckWatchEvent requires -WatchSetDirectory and -EventId.'
    }
    $context = Get-WatchSetContext $WatchSetDirectory
    $event = Get-ValidatedWatchEvent $context
    if ([string]$event.eventId -cne $EventId) { throw 'Event ID does not match the persisted watch event.' }
    $ackPath = Join-Path $context.Directory 'ack.json'
    if (Test-Path -LiteralPath $ackPath -PathType Leaf) {
        $existing = Get-ValidatedWatchAck -Context $context -Event $event
        $existing | ConvertTo-Json -Depth 10 -Compress | Write-Output
        return
    }
    $ack = [ordered]@{
        schemaVersion = $script:SchemaVersion
        kind = 'long-run-supervisor.watch-ack'
        watchGroupId = [string]$context.Manifest.watchGroupId
        generation = [int]$context.Manifest.generation
        generationId = [string]$context.Manifest.generationId
        eventId = [string]$event.eventId
        cursor = [string]$event.cursor
        acknowledgedUtc = Get-UtcNowText
    }
    try { Write-JsonCreateOnce -Path $ackPath -Value $ack }
    catch [IO.IOException] {
        if (-not (Test-Path -LiteralPath $ackPath -PathType Leaf)) { throw }
    }
    (Get-ValidatedWatchAck -Context $context -Event $event) | ConvertTo-Json -Depth 10 -Compress | Write-Output
}

function Emit-WakeAndExit {
    param([Parameter(Mandatory = $true)]$Decision)
    if ($Decision.Wake) {
        $Decision.WakeRecord | ConvertTo-Json -Depth 8 -Compress | Write-Output
        $wakeExitCode = [int]$Decision.ExitCode
        if ([string]$Decision.WakeRecord.condition -eq 'completed') {
            $wakeExitCode = $CompletedExitCode
        }
        exit $wakeExitCode
    }
    if ($AsJson) { $Decision.State | ConvertTo-Json -Depth 10 -Compress | Write-Output }
    exit 0
}

function Invoke-StartAction {
    $sourceCommandBytes = $null
    if ([string]::IsNullOrWhiteSpace($Command) -eq [string]::IsNullOrWhiteSpace($CommandFile)) {
        throw 'Specify exactly one of -Command or -CommandFile.'
    }
    if (-not [string]::IsNullOrWhiteSpace($CommandFile)) {
        $sourceCommandFile = Resolve-AbsolutePath $CommandFile
        if (-not (Test-Path -LiteralPath $sourceCommandFile -PathType Leaf)) { throw "Command file does not exist: $sourceCommandFile" }
        $sourceCommandBytes = [IO.File]::ReadAllBytes($sourceCommandFile)
        $commandText = [IO.File]::ReadAllText($sourceCommandFile)
    }
    else { $commandText = $Command }
    if ([string]::IsNullOrWhiteSpace($commandText)) { throw 'Command must not be empty.' }

    if ([string]::IsNullOrWhiteSpace($TaskRoot)) {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is unavailable; specify -TaskRoot.' }
        $selectedRoot = Join-Path $env:LOCALAPPDATA 'Codex\long-run-supervisor\tasks'
    }
    else { $selectedRoot = $TaskRoot }
    $selectedRoot = Assert-SafeRoot $selectedRoot
    if (-not (Test-Path -LiteralPath $selectedRoot)) { New-Item -ItemType Directory -Path $selectedRoot -Force | Out-Null }

    $effectiveDeadline = if ($DeadlineMinutes -gt 0) { $DeadlineMinutes } else { [Math]::Max(60, 4 * $ExpectedMinutes) }
    $effectiveStall = if ($StallMinutes -gt 0) { $StallMinutes } else { [Math]::Min(60, [Math]::Max(15, $ExpectedMinutes)) }
    if ($effectiveStall -ge $effectiveDeadline) { throw 'StallMinutes must be less than DeadlineMinutes.' }

    $taskId = [Guid]::NewGuid().ToString('N')
    $directory = Join-Path $selectedRoot $taskId
    New-Item -ItemType Directory -Path $directory | Out-Null
    try {
        Set-PrivateTaskAcl $directory
        [void](Resolve-PrivateTaskDirectory $directory)
    }
    catch { Remove-Item -LiteralPath $directory -Force; throw }

    $hmacKey = [byte[]]::new(32)
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($hmacKey) } finally { $rng.Dispose() }
    $commandBytes = if ($null -ne $sourceCommandBytes) { $sourceCommandBytes } else { [Text.Encoding]::UTF8.GetBytes($commandText) }
    $hmac = [Security.Cryptography.HMACSHA256]::new($hmacKey)
    try { $digestBytes = $hmac.ComputeHash($commandBytes) } finally { $hmac.Dispose(); [Array]::Clear($hmacKey, 0, $hmacKey.Length) }
    $digest = 'hmac-sha256:' + ([BitConverter]::ToString($digestBytes).Replace('-', '').ToLowerInvariant())
    $privateCommandPath = Join-Path $directory 'command.private.ps1'
    if ($null -ne $sourceCommandBytes) {
        [IO.File]::WriteAllBytes($privateCommandPath, $sourceCommandBytes)
    } else {
        [IO.File]::WriteAllText($privateCommandPath, $commandText, [Text.UTF8Encoding]::new($true))
    }
    [Array]::Clear($commandBytes, 0, $commandBytes.Length)
    $sourceCommandBytes = $null
    $commandText = $null
    $created = [DateTimeOffset]::UtcNow
    $deadline = $created.AddMinutes($effectiveDeadline)
    $launch = [ordered]@{
        schemaVersion = $script:SchemaVersion
        taskId = $taskId
        blindedCommandDigest = $digest
        commandFile = $privateCommandPath
        createdUtc = $created.ToString('o')
        deadlineUtc = $deadline.ToString('o')
        heartbeatIntervalSeconds = $HeartbeatSeconds
        stallAfterSeconds = $effectiveStall * 60
    }
    Write-JsonAtomic -Path (Join-Path $directory 'launch.private.json') -Value $launch

    $state = [pscustomobject][ordered]@{
        schemaVersion = $script:SchemaVersion
        taskId = $taskId
        blindedCommandDigest = $digest
        status = 'running'
        reason = 'worker_launching'
        shouldWake = $false
        createdUtc = $created.ToString('o')
        startUtc = $null
        deadlineUtc = $deadline.ToString('o')
        heartbeatIntervalSeconds = $HeartbeatSeconds
        stallAfterSeconds = $effectiveStall * 60
        workerPid = 0
        workerStartUtc = $null
        childPid = $null
        childStartUtc = $null
        heartbeatUtc = $created.ToString('o')
        progressUtc = $created.ToString('o')
        cpuDeltaSeconds = 0.0
        cpuTotalSeconds = 0.0
        stdoutOffset = 0
        stderrOffset = 0
        exitCode = $null
        endUtc = $null
        commandMaterialPresent = $true
    }
    Write-JsonAtomic -Path (Join-Path $directory 'state.json') -Value $state
    Add-WalEvent -Directory $directory -Event 'launch_prepared' -Data @{ createdUtc = $state.createdUtc }

    $hostPath = Get-PowerShellHostPath
    $scriptPath = $PSCommandPath
    $workerArgs = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', ('"{0}"' -f $scriptPath), '-Action', 'Worker', '-TaskDirectory', ('"{0}"' -f $directory)
    )
    try {
        $startInfo = [Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $hostPath
        $startInfo.Arguments = $workerArgs -join ' '
        $startInfo.WorkingDirectory = $directory
        $startInfo.UseShellExecute = $true
        $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
        $startInfo.ErrorDialog = $false
        $worker = [Diagnostics.Process]::Start($startInfo)
        if ($null -eq $worker) { throw 'Worker process did not start.' }
    }
    catch {
        Complete-Worker -Directory $directory -State $state -Status 'failed' -Reason ('worker_launch_failed: ' + $_.Exception.Message) -ProcessExitCode 1
        throw
    }

    [ordered]@{
        taskId = $taskId
        blindedCommandDigest = $digest
        taskDirectory = $directory
        workerPid = $worker.Id
        deadlineUtc = $deadline.ToString('o')
        stallAfterMinutes = $effectiveStall
        pollCommand = "& '$scriptPath' -Action Poll -TaskDirectory '$directory'"
        waitCommand = "& '$scriptPath' -Action Wait -TaskDirectory '$directory' -CompletedExitCode 0"
    } | ConvertTo-Json -Depth 5 -Compress | Write-Output
}

function Complete-Worker {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Reason,
        $ProcessExitCode
    )
    $originalStatus = $Status
    $commandPath = Join-Path $Directory 'command.private.ps1'
    $launchPath = Join-Path $Directory 'launch.private.json'
    foreach ($sensitivePath in @($commandPath, $launchPath)) {
        if (Test-Path -LiteralPath $sensitivePath) {
            try { Remove-Item -LiteralPath $sensitivePath -Force -ErrorAction Stop } catch { $Status = 'failed'; $Reason = 'private_launch_cleanup_failed' }
        }
    }
    $end = [DateTimeOffset]::UtcNow
    $State.status = $Status
    $State.reason = $Reason
    $State.shouldWake = $true
    $State.heartbeatUtc = $end.ToString('o')
    $State.endUtc = $end.ToString('o')
    $State.exitCode = $ProcessExitCode
    $State.commandMaterialPresent = (Test-Path -LiteralPath $commandPath) -or (Test-Path -LiteralPath $launchPath)
    Write-JsonAtomic -Path (Join-Path $Directory 'state.json') -Value $State
    $receipt = [ordered]@{
        schemaVersion = $script:SchemaVersion
        taskId = [string]$State.taskId
        blindedCommandDigest = [string]$State.blindedCommandDigest
        status = $Status
        originalStatus = $originalStatus
        reason = $Reason
        processExitCode = $ProcessExitCode
        workerPid = $State.workerPid
        workerStartUtc = $State.workerStartUtc
        childPid = $State.childPid
        childStartUtc = $State.childStartUtc
        startUtc = $State.startUtc
        endUtc = $State.endUtc
        deadlineUtc = $State.deadlineUtc
        cpuTotalSeconds = $State.cpuTotalSeconds
        stdoutBytes = $State.stdoutOffset
        stderrBytes = $State.stderrOffset
        commandMaterialPresent = $State.commandMaterialPresent
    }
    Write-JsonAtomic -Path (Join-Path $Directory 'exit.json') -Value $receipt
    Add-WalEvent -Directory $Directory -Event 'terminal' -Data @{ status = $Status; reason = $Reason; processExitCode = $ProcessExitCode }
    [void](Write-Wake -Directory $Directory -State $State -Condition $Status -Reason $Reason)
}

function Invoke-WorkerAction {
    $directory = Resolve-PrivateTaskDirectory (Get-SingleTaskDirectory)
    $launchPath = Join-Path $directory 'launch.private.json'
    $statePath = Join-Path $directory 'state.json'
    $state = $null
    try {
        $state = Read-JsonFile $statePath
        $claimPath = Join-Path $directory 'worker.claim.json'
        try {
            $claimStream = [IO.File]::Open($claimPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        }
        catch { exit 1 }
        $workerStart = ([DateTimeOffset](Get-Process -Id $PID).StartTime.ToUniversalTime()).ToString('o')
        try {
            $claim = [ordered]@{ schemaVersion = $script:SchemaVersion; taskId = [string]$state.taskId; workerPid = $PID; workerStartUtc = $workerStart } | ConvertTo-Json -Compress
            $claimBytes = [Text.Encoding]::UTF8.GetBytes($claim)
            $claimStream.Write($claimBytes, 0, $claimBytes.Length)
            $claimStream.Flush($true)
        }
        finally { $claimStream.Dispose() }
        $state.workerPid = $PID
        $state.workerStartUtc = $workerStart
        $state.heartbeatUtc = Get-UtcNowText
        $state.reason = 'worker_started'
        Write-JsonAtomic -Path $statePath -Value $state
        Add-WalEvent -Directory $directory -Event 'worker_launched' -Data @{ workerPid = $PID; workerStartUtc = $workerStart }
        $launch = Read-JsonFile $launchPath
        if ([string]$launch.taskId -ne [string]$state.taskId) { throw 'Launch and state task IDs do not match.' }
        $commandPath = [string]$launch.commandFile
        if (-not (Test-Path -LiteralPath $commandPath -PathType Leaf)) { throw 'Private command file is missing.' }
        $stdoutPath = Join-Path $directory 'stdout.log'
        $stderrPath = Join-Path $directory 'stderr.log'
        $hostPath = Get-PowerShellHostPath
        $childArgs = @('-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $commandPath))
        $child = Start-Process -FilePath $hostPath -ArgumentList $childArgs -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -WindowStyle Hidden -PassThru
        $childStart = ([DateTimeOffset]$child.StartTime.ToUniversalTime()).ToString('o')
        $now = [DateTimeOffset]::UtcNow
        $state.startUtc = $now.ToString('o')
        $state.heartbeatUtc = $now.ToString('o')
        $state.progressUtc = $now.ToString('o')
        $state.childPid = $child.Id
        $state.childStartUtc = $childStart
        $state.reason = 'child_running'
        Write-JsonAtomic -Path $statePath -Value $state
        Add-WalEvent -Directory $directory -Event 'child_started' -Data @{ childPid = $child.Id; childStartUtc = $childStart }

        $previousCpu = 0.0
        $previousOut = [int64]0
        $previousErr = [int64]0
        $wasStalled = $false
        while (-not $child.HasExited) {
            Start-Sleep -Seconds ([int]$launch.heartbeatIntervalSeconds)
            $child.Refresh()
            $now = [DateTimeOffset]::UtcNow
            $metrics = Get-TreeMetrics -RootPid $child.Id -RootStartUtc $childStart
            $outLength = Get-FileLength $stdoutPath
            $errLength = Get-FileLength $stderrPath
            $delta = [Math]::Max(0.0, [double]$metrics.CpuSeconds - $previousCpu)
            $madeProgress = ($delta -ge 0.05) -or ($outLength -ne $previousOut) -or ($errLength -ne $previousErr)
            if ($madeProgress) { $state.progressUtc = $now.ToString('o') }
            $state.heartbeatUtc = $now.ToString('o')
            $state.cpuDeltaSeconds = [Math]::Round($delta, 6)
            $state.cpuTotalSeconds = [Math]::Round([double]$metrics.CpuSeconds, 6)
            $state.stdoutOffset = $outLength
            $state.stderrOffset = $errLength

            $interruptPath = Join-Path $directory 'interrupt.request.json'
            if (Test-Path -LiteralPath $interruptPath -PathType Leaf) {
                if (-not (Stop-OwnedTree -RootPid $child.Id -RootStartUtc $childStart)) { throw 'Interrupt requested but child ownership could not be proven.' }
                try { $child.WaitForExit(10000) | Out-Null } catch { }
                Complete-Worker -Directory $directory -State $state -Status 'interrupted' -Reason 'user_interruption' -ProcessExitCode 130
                return
            }
            if ($now -ge [DateTimeOffset]::Parse([string]$launch.deadlineUtc)) {
                if (-not (Stop-OwnedTree -RootPid $child.Id -RootStartUtc $childStart)) { throw 'Deadline reached but child ownership could not be proven.' }
                try { $child.WaitForExit(10000) | Out-Null } catch { }
                Complete-Worker -Directory $directory -State $state -Status 'deadline' -Reason 'deadline_reached' -ProcessExitCode 124
                return
            }

            $stalled = ($now - [DateTimeOffset]::Parse([string]$state.progressUtc)).TotalSeconds -ge [int]$launch.stallAfterSeconds
            if ($stalled) {
                $state.status = 'stalled'
                $state.reason = 'no_cpu_or_output_progress'
                $state.shouldWake = $true
                if (-not $wasStalled) {
                    Add-WalEvent -Directory $directory -Event 'stalled' -Data @{ progressUtc = $state.progressUtc }
                    [void](Write-Wake -Directory $directory -State $state -Condition 'stalled' -Reason $state.reason)
                }
                $wasStalled = $true
            }
            else {
                $state.status = 'running'
                $state.reason = 'child_running'
                $state.shouldWake = $false
                if ($wasStalled) {
                    Add-WalEvent -Directory $directory -Event 'resumed' -Data @{ progressUtc = $state.progressUtc }
                    $wakePath = Join-Path $directory 'wake.json'
                    if (Test-Path -LiteralPath $wakePath) { Remove-Item -LiteralPath $wakePath -Force }
                }
                $wasStalled = $false
            }
            Write-JsonAtomic -Path $statePath -Value $state
            $previousCpu = [double]$metrics.CpuSeconds
            $previousOut = $outLength
            $previousErr = $errLength
        }

        $child.WaitForExit()
        $state.stdoutOffset = Get-FileLength $stdoutPath
        $state.stderrOffset = Get-FileLength $stderrPath
        $processExitCode = $child.ExitCode
        if ($processExitCode -eq 0) {
            Complete-Worker -Directory $directory -State $state -Status 'completed' -Reason 'process_exit_zero' -ProcessExitCode 0
        }
        else {
            Complete-Worker -Directory $directory -State $state -Status 'failed' -Reason 'process_exit_nonzero' -ProcessExitCode $processExitCode
        }
    }
    catch {
        if ($null -ne $state) {
            try { Complete-Worker -Directory $directory -State $state -Status 'failed' -Reason ('worker_error: ' + $_.Exception.Message) -ProcessExitCode 1 } catch { }
        }
        exit 1
    }
}

function Invoke-InterruptAction {
    $directory = Resolve-PrivateTaskDirectory (Get-SingleTaskDirectory)
    $decision = Get-WakeDecision -Directory $directory
    if ($decision.Wake) { Emit-WakeAndExit $decision }
    $state = $decision.State
    $worker = Get-ProcessIdentity -Id ([int]$state.workerPid) -ExpectedStartUtc ([string]$state.workerStartUtc)
    if ($null -eq $worker) {
        $wake = Write-Wake -Directory $directory -State $state -Condition 'stalled' -Reason 'interrupt_refused_worker_identity_lost'
        Emit-WakeAndExit ([pscustomobject]@{ Wake = $true; ExitCode = 12; WakeRecord = $wake; State = $state })
    }
    $request = [ordered]@{
        schemaVersion = $script:SchemaVersion
        taskId = [string]$state.taskId
        requestedUtc = Get-UtcNowText
        requesterSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    }
    Write-JsonAtomic -Path (Join-Path $directory 'interrupt.request.json') -Value $request
    $limit = [DateTimeOffset]::UtcNow.AddSeconds([Math]::Max(15, 3 * [int]$state.heartbeatIntervalSeconds))
    while ([DateTimeOffset]::UtcNow -lt $limit) {
        Start-Sleep -Seconds 1
        $decision = Get-WakeDecision -Directory $directory
        if ($decision.Wake) { Emit-WakeAndExit $decision }
    }
    $wake = Write-Wake -Directory $directory -State $state -Condition 'stalled' -Reason 'interrupt_request_not_acknowledged'
    Emit-WakeAndExit ([pscustomobject]@{ Wake = $true; ExitCode = 12; WakeRecord = $wake; State = $state })
}

switch ($Action) {
    'Start' { Invoke-StartAction; break }
    'Poll' {
        $directory = Resolve-PrivateTaskDirectory (Get-SingleTaskDirectory)
        Emit-WakeAndExit (Get-WakeDecision -Directory $directory)
    }
    'Wait' {
        $directory = Resolve-PrivateTaskDirectory (Get-SingleTaskDirectory)
        while ($true) {
            $decision = Get-WakeDecision -Directory $directory
            if ($decision.Wake) { Emit-WakeAndExit $decision }
            Start-Sleep -Seconds $PollSeconds
        }
    }
    'Interrupt' { Invoke-InterruptAction; break }
    'Worker' { Invoke-WorkerAction; break }
    'CreateWatchSet' { Invoke-CreateWatchSetAction; break }
    'PollMany' { Invoke-ManyAction -Block $false; break }
    'WaitMany' { Invoke-ManyAction -Block $true; break }
    'AckWatchEvent' { Invoke-AckWatchEventAction; break }
}
