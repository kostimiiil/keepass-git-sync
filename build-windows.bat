@echo off
REM Build Windows executable for KeePass Sync Tray

echo Building KeePass Sync Tray executable for Windows...

REM Find Python installation
set PYTHON_CMD=python
where python >nul 2>&1 || set PYTHON_CMD=py
where %PYTHON_CMD% >nul 2>&1 || (
    echo Error: Python not found in PATH
    echo Please install Python and ensure it's in your PATH
    exit /b 1
)

echo Using Python: %PYTHON_CMD%

REM Install dependencies if not present
%PYTHON_CMD% -m pip install pystray pillow plyer pyinstaller

REM Build with PyInstaller for Windows
%PYTHON_CMD% -m PyInstaller --onefile ^
    --windowed ^
    --name "KeePassSyncTray" ^
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
    --add-data "config.json.template;." ^
    --add-data ".gitignore.template;." ^
    keepass-sync-tray.py

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Executable created at: dist\KeePassSyncTray.exe
    echo.
    echo To run the application:
    echo   dist\KeePassSyncTray.exe
    echo.
    echo The executable includes all dependencies - no Python or libraries needed!
    echo Move the executable to the main directory to use with your database.
) else (
    echo Build failed!
    exit /b 1
)