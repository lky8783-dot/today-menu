@echo off
setlocal

set "REPO_ROOT=%~dp0"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "SCRIPT_PATH=%REPO_ROOT%scripts\run_menu_update.ps1"

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] Cannot find script:
    echo %SCRIPT_PATH%
    exit /b 1
)

echo [INFO] Running menu update...
"%POWERSHELL_EXE%" -ExecutionPolicy Bypass -File "%SCRIPT_PATH%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Menu update failed with exit code %EXIT_CODE%.
    exit /b %EXIT_CODE%
)

echo [INFO] Menu update completed successfully.
exit /b 0
