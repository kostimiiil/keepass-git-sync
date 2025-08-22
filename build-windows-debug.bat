@echo off
REM Build Windows executable for KeePass Sync Tray (DEBUG VERSION WITH CONSOLE)

echo Building KeePass Sync Tray executable for Windows (DEBUG)...

REM Find Python installation
set PYTHON_CMD=python
where python >nul 2>&1 || set PYTHON_CMD=py
where %PYTHON_CMD% >nul 2>&1 || set PYTHON_CMD=C:\Users\adamk\AppData\Local\Microsoft\WindowsApps\python.exe

echo Using Python: %PYTHON_CMD%

REM Install dependencies if not present
%PYTHON_CMD% -m pip install pystray pillow plyer pyinstaller

REM Build with PyInstaller for Windows (NO --windowed flag for console output)
%PYTHON_CMD% -m PyInstaller --onefile ^
    --name "KeePassSyncTray-Debug" ^
    --icon "keepass_icon.ico" ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import plyer ^
    --hidden-import plyer.platforms.win ^
    --hidden-import plyer.platforms.win.notification ^
    --add-data "sync-keepass.sh;." ^
    --add-data "sync-keepass.bat;." ^
    --add-data "keepass_icon.png;." ^
    --add-data "keepass_icon.ico;." ^
    keepass-sync-tray.py

if %ERRORLEVEL% EQU 0 (
    echo Debug build successful!
    echo Executable created at: dist\KeePassSyncTray-Debug.exe
    echo.
    echo To run the debug application:
    echo   dist\KeePassSyncTray-Debug.exe
    echo.
    echo This version will show console output for debugging!
    echo Move the executable to the main directory to use with your database.
) else (
    echo Build failed!
    exit /b 1
)