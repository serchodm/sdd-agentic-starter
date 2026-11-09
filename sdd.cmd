@echo off
setlocal

set "CLI_SCRIPT=%~dp0scripts\sdd_cli.py"
set "FIRST_ARG=%~1"
set "TARGET_ARGS=%*"

if "%FIRST_ARG%"=="" (
    set "TARGET_ARGS="%CLI_SCRIPT%""
) else (
    echo %FIRST_ARG% | findstr /I "\.py \\ \/" >nul
    if errorlevel 1 (
        set "TARGET_ARGS="%CLI_SCRIPT%" %*"
    )
)

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run python %TARGET_ARGS%
    exit /b %ERRORLEVEL%
)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" %TARGET_ARGS%
    exit /b %ERRORLEVEL%
)
py -3.12 %TARGET_ARGS% 2>nul
if %ERRORLEVEL% equ 0 exit /b 0
py -3 %TARGET_ARGS% 2>nul
if %ERRORLEVEL% equ 0 exit /b 0
python %TARGET_ARGS%
exit /b %ERRORLEVEL%
