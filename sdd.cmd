@echo off
setlocal
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run python %*
    exit /b %ERRORLEVEL%
)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" %*
    exit /b %ERRORLEVEL%
)
py -3.12 %* 2>nul
if %ERRORLEVEL% equ 0 exit /b 0
py -3 %* 2>nul
if %ERRORLEVEL% equ 0 exit /b 0
python %*
exit /b %ERRORLEVEL%
