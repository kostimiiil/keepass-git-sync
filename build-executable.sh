#!/bin/bash

# Build standalone executable for KeePass Sync Tray

echo "Building KeePass Sync Tray executable..."

# Build with PyInstaller
pyinstaller --onefile \
    --windowed \
    --name "KeePassSyncTray" \
    --icon "keepass_icon.ico" \
    --hidden-import pystray \
    --hidden-import PIL \
    --hidden-import plyer \
    --hidden-import plyer.platforms.linux \
    --hidden-import plyer.platforms.linux.notification \
    --add-data "sync-keepass.sh:." \
    --add-data "keepass_icon.png:." \
    --add-data "keepass_icon.ico:." \
    --add-data "config.json.template:." \
    --add-data ".gitignore.template:." \
    keepass-sync-tray.py

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Executable created at: dist/KeePassSyncTray"
    echo ""
    echo "To run the application:"
    echo "  ./dist/KeePassSyncTray"
    echo ""
    echo "The executable includes all dependencies - no Python or libraries needed!"
else
    echo "Build failed!"
    exit 1
fi