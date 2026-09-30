@echo off
setlocal
set "YTD_HOME=%~dp0"
if exist "%YTD_HOME%ytd.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%YTD_HOME%ytd.ps1" %*
    exit /b %ERRORLEVEL%
)
echo ERROR: YTD installation is incomplete.
exit /b 1
