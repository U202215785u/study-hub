@echo off
cd /d "%~dp0"

set PYTHON=

:: Check known real Python paths first (skip WindowsApps stub)
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "C:\Python312"
    "C:\Python311"
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python312"
) do (
    if exist "%%d\python.exe" (
        set PYTHON="%%d\python.exe"
        goto :found
    )
)

:: Fallback to PATH (but skip WindowsApps)
for %%p in (python.exe python3.exe) do (
    for /f "delims=" %%f in ('where %%p 2^>nul') do (
        echo %%f | findstr /i /c:"WindowsApps" >nul
        if errorlevel 1 (
            set PYTHON="%%f"
            goto :found
        )
    )
)

echo Python not found. Install Python 3 from python.org
pause
exit /b 1

:found
echo AI Fanwen starting...
echo Log at %~dp0error.log
%PYTHON% "%~dp0ai-fanwen.py" > "%~dp0error.log" 2>&1
