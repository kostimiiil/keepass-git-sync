@echo off
REM Windows version of KeePass sync script

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git is not installed or not in PATH
    exit /b 1
)

REM Load configuration or use defaults
set "DB=Passwords.kdbx"
set "COMMIT_FORMAT=Update from {hostname} at {timestamp}"
set "AUTO_PULL=true"
set "AUTO_PUSH=true"

if exist "config.json" (
    echo Loading configuration from config.json...
    REM Simple config parsing for Windows - check if PowerShell is available
    powershell -Command "Get-Command Get-Content" >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%i in ('powershell -Command "try { $c = Get-Content 'config.json' | ConvertFrom-Json; $c.database.filename } catch { 'Passwords.kdbx' }"') do set "DB=%%i"
        for /f "delims=" %%i in ('powershell -Command "try { $c = Get-Content 'config.json' | ConvertFrom-Json; $c.git.commit_message_format } catch { 'Update from {hostname} at {timestamp}' }"') do set "COMMIT_FORMAT=%%i"
        for /f "delims=" %%i in ('powershell -Command "try { $c = Get-Content 'config.json' | ConvertFrom-Json; $c.git.auto_pull } catch { 'true' }"') do set "AUTO_PULL=%%i"
        for /f "delims=" %%i in ('powershell -Command "try { $c = Get-Content 'config.json' | ConvertFrom-Json; $c.git.auto_push } catch { 'true' }"') do set "AUTO_PUSH=%%i"
    ) else (
        echo PowerShell not available, using default settings
    )
) else (
    echo No config.json found, using defaults
)

echo Using database: %DB%

REM Pull latest changes first (if enabled)
if "%AUTO_PULL%"=="true" (
    echo Pulling latest changes...
    git pull origin main
    if %errorlevel% neq 0 (
        echo Warning: Failed to pull latest changes, continuing anyway...
    )
) else (
    echo Auto-pull disabled, skipping pull
)

REM Check if there are any changes to commit
git diff-index --quiet HEAD --
if %errorlevel% equ 0 (
    echo No changes to commit
    exit /b 0
)

REM Get current timestamp and hostname
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "MIN=%dt:~10,2%" & set "SS=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD% %HH%:%MIN%:%SS%"

REM Add database changes
git add "%DB%"

REM Format commit message
set "formatted_msg=%COMMIT_FORMAT:{hostname}=%COMPUTERNAME%"
set "formatted_msg=%formatted_msg:{timestamp}=%timestamp%"

REM Commit with formatted message
git commit -m "%formatted_msg%"
if %errorlevel% neq 0 (
    echo Error: Failed to commit changes
    exit /b 1
)

REM Push to remote repository (if enabled)
if "%AUTO_PUSH%"=="true" (
    echo Pushing changes to remote...
    git push origin main
    if %errorlevel% neq 0 (
        echo Error: Failed to push changes
        exit /b 1
    )
) else (
    echo Auto-push disabled, changes committed locally only
)

echo Sync completed successfully!