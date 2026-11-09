[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$cliScript = Join-Path $PSScriptRoot "scripts\sdd_cli.py"

# Si no se pasan argumentos o el primer argumento es un comando del CLI, invocar sdd_cli.py
if ($ScriptArgs.Count -eq 0 -or ($ScriptArgs[0] -notlike "*.py" -and $ScriptArgs[0] -notlike "*\*")) {
    $targetArgs = @($cliScript) + $ScriptArgs
} else {
    $targetArgs = $ScriptArgs
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python @targetArgs
    exit $LASTEXITCODE
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    & $venvPython @targetArgs
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 @targetArgs
    if ($LASTEXITCODE -eq 0) { exit 0 }
    & py -3 @targetArgs
    exit $LASTEXITCODE
}

& python @targetArgs
exit $LASTEXITCODE
