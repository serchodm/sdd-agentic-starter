@echo off
setlocal

set "CLI_SCRIPT=%~dp0scripts\sdd_cli.py"

where uv >nul 2>nul
if errorlevel 1 goto :try_venv
"uv" run python "%CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%

:try_venv
if not exist "%~dp0.venv\Scripts\python.exe" goto :try_py312
"%~dp0.venv\Scripts\python.exe" "%CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%

:try_py312
py -3.12 -c "" >nul 2>nul
if errorlevel 1 goto :try_py3
py -3.12 "%CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%

:try_py3
py -3 -c "" >nul 2>nul
if errorlevel 1 goto :try_python
py -3 "%CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%

:try_python
python "%CLI_SCRIPT%" %*
exit /b %ERRORLEVEL%
