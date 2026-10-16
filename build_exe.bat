@echo off
echo ========================================================
echo Building SBI Live Balance Desktop Widget for Windows
echo ========================================================

rem Ensure we are using project virtual environment
if exist .venv\Scripts\pyinstaller.exe (
    set PYINSTALLER=.venv\Scripts\pyinstaller.exe
) else (
    set PYINSTALLER=pyinstaller
)

echo Using PyInstaller: %PYINSTALLER%

%PYINSTALLER% --noconsole --name "SBIBalanceWidget" --clean ^
    --collect-all playwright ^
    --collect-all keyring ^
    --collect-all pystray ^
    --collect-all PIL ^
    --add-data "app;app" ^
    run_widget.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo Build SUCCESSFUL!
    echo Executable located in: dist\SBIBalanceWidget\SBIBalanceWidget.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Build FAILED! Check output above for errors.
    echo ========================================================
)
