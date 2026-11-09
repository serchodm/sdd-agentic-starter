[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python @ScriptArgs
    exit $LASTEXITCODE
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython @ScriptArgs
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 @ScriptArgs
    if ($LASTEXITCODE -eq 0) { exit 0 }
    & py -3 @ScriptArgs
    exit $LASTEXITCODE
}

& python @ScriptArgs
exit $LASTEXITCODE
