[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $TargetRoot,

    [string] $Profile = 'core',

    [string] $Python = 'python',

    [switch] $Apply
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    (Join-Path $PSScriptRoot 'install_toolkit.py'),
    '--source-root', $repositoryRoot,
    '--target-root', $TargetRoot,
    '--profile', $Profile
)
if ($Apply) {
    $arguments += '--apply'
}

& $Python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Toolkit installer failed with exit code $LASTEXITCODE."
}
