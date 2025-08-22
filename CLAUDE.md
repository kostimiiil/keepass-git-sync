# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a KeePass password database (`Passwords.kdbx`) with a professional system tray application for automatic Git synchronization across multiple devices.

## Architecture

The system consists of a cross-platform system tray application with supporting build scripts:

### Core Application
**keepass-sync-tray.py**: Professional system tray application built with `pystray`
- Monitors `Passwords.kdbx` file for changes (2-second polling)
- Provides system tray icon with color-coded status (green=running, gray=stopped, yellow=syncing)
- Right-click menu with start/stop/sync controls and status information
- Desktop notifications for sync events and errors
- Cross-platform detection automatically chooses appropriate sync script
- Custom KeePass-themed icon with status overlays

### Sync Scripts
- **sync-keepass.sh**: Linux/macOS Git synchronization using bash
- **sync-keepass.bat**: Windows Git synchronization using cmd

Both scripts follow the same pattern: pull → commit with timestamp → push

### Build System
- **build-executable.sh**: Creates standalone Linux executable using PyInstaller
- **build-windows.bat**: Creates standalone Windows `.exe` using PyInstaller
- Both embed all dependencies, icons, and sync scripts into single executable

## Common Commands

### Run the system tray application
```bash
# From Python source
python3 keepass-sync-tray.py

# From built executable
./dist/KeePassSyncTray        # Linux
dist\KeePassSyncTray.exe      # Windows
```

### Build standalone executables
```bash
# Linux
bash build-executable.sh

# Windows (run on Windows machine)
build-windows.bat
```

### Manual sync operations
```bash
# Linux/macOS
bash sync-keepass.sh

# Windows
sync-keepass.bat

# Check sync status
git status
git log --oneline -5
```

### Development dependencies
```bash
pip install pystray pillow plyer pyinstaller
```

## Technical Details

- **Dependencies**: Uses `pystray` for system tray, `PIL` for icon handling, `plyer` for notifications
- **Platform Detection**: Automatically selects Windows (`sync-keepass.bat` + `cmd /c`) vs Unix (`sync-keepass.sh` + `bash`)
- **Icon System**: Loads `keepass_icon.png` with fallback to programmatically generated icon
- **Error Handling**: Graceful fallbacks for missing icons, sync script failures, and notification errors
- **Thread Safety**: Uses daemon threads for file monitoring and sync operations

## Repository Configuration

- Remote: `git@github.com:kostimiiil/keepass-passwords.git`
- Database: `Passwords.kdbx` (KeePass 2.x format)
- Commit format: "Update from {hostname} at {timestamp}"
- Only commits when actual changes detected