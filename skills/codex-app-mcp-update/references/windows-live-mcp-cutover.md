# Windows live MCP cutover

Use this only after the main skill selects a controlled in-App cutover. The safer default is to
close Codex and run the update from an external terminal.

## Preconditions

- Bind an exact artifact SHA-256 and expected package/plugin versions.
- Resolve the exact MCP shim or executable path plus every declared lifecycle owner, such as a
  detached supervisor and its stable runtime home.
- Confirm the user authorized interruption of this MCP transport.
- Preserve unrelated tasks and processes. Never match only `python.exe` or a broad name fragment.
- Ensure the active marketplace source already contains the expected plugin cachebuster.

## Read-only inventory

Use product-specific paths and selectors:

```powershell
uv tool list
codex plugin marketplace list
codex plugin list --json

$targetMcp = [IO.Path]::GetFullPath('<absolute-mcp-executable>')
Get-CimInstance Win32_Process |
  Where-Object {
    $_.ExecutablePath -and
    [IO.Path]::GetFullPath($_.ExecutablePath).Equals(
      $targetMcp,
      [StringComparison]::OrdinalIgnoreCase
    )
  } |
  Select-Object ProcessId, ParentProcessId, ExecutablePath, CommandLine
```

Snapshot the selected roots and recursively enumerate descendants from the same process snapshot.
Reject the cutover if any descendant executable is outside the exact tool environment or its bound
managed interpreter. Stop descendants before roots and validate PID plus executable path again at
the action boundary.

When the MCP frontend attaches to a persistent supervisor, read its product discovery record and
verify the native process-start identity before selecting it. Include its workers in the descendant
inventory. Prefer the product's exact graceful stop operation when available, then verify the owner
and descendants exited; otherwise apply the same exact-path/PID tree rule. Closing only the stdio
frontend is insufficient evidence that package locks are gone.

Do not stop:

- all `python.exe` processes;
- the Codex host process unless the user explicitly chose a full App restart;
- WSL or another host's MCP merely because its command line contains the same package name;
- an unverified PID from an earlier snapshot.

## Clean rebuild

After every selected process exits, confirm the MCP did not immediately respawn. Then use the
package manager's normal removal/install path for the one exact tool:

```powershell
uv tool uninstall <distribution-name>
uv tool install --python <bound-python> <exact-wheel-path>
uv pip check --python <tool-environment-python>
```

Run the product setup command or the verified Codex CLI reinstall flow. Do not manually rewrite
Codex config or marketplace JSON.

## Partial-install failure rule

Treat `uv tool install --force` failure as potentially non-atomic. Immediately check all three:

```powershell
uv tool list
& <tool-environment-python> -c "import importlib.metadata as m; print(m.version('<distribution-name>'))"
uv pip check --python <tool-environment-python>
```

If package import, metadata, or dependencies are missing, do not keep adding packages into the live
environment. Once locks are gone, remove and rebuild the exact tool environment. A locked compiled
module can make a layered repair fail again while leaving a mixed environment.

## Completion evidence

Require all of the following before saying the local update is installed:

- exact installed package version and full entrypoint set;
- dependency check success;
- enabled plugin with exact new cachebuster and intended resolved marketplace root;
- source/cached skill and MCP declaration bytes matching that root;
- real installed-executable MCP preflight using the declaration's exact command and arguments;
- lifecycle-owner mode and process identity readback matching the installed declaration;
- `restart_required` or equivalent setup result.

Then fully restart Codex and use a new task for one native capability call. If the host defers MCP
tools, its exact native tool-search step may load the capability tool, but the search result is not
evidence; require the subsequent MCP response. The old task's catalog and transport are
intentionally not part of the new-version proof.
