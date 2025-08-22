# KeePass Git Sync

A cross-platform system tray application that automatically synchronizes your KeePass database with a Git repository. Monitor your KeePass database for changes and automatically commit and push them to your remote Git repository.

![KeePass Git Sync Tray](keepass_icon.png)

## Features

- **System Tray Integration**: Runs quietly in the background with intuitive system tray controls
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Real-time Monitoring**: Watches your KeePass database file for changes
- **Configurable**: JSON-based configuration system for customizing behavior
- **Visual Status**: Color-coded tray icon (green=running, gray=stopped, yellow=syncing)
- **Desktop Notifications**: Optional notifications for sync events and errors
- **Git Integration**: Full Git workflow with pull, commit, and push operations
- **Standalone Executable**: Build self-contained executables with no external dependencies

## Quick Start

### Method 1: Use with Existing Password Repository (Recommended)

1. **Navigate to your password repository**:
   ```bash
   cd /path/to/your/password-repository
   ```

2. **Copy the KeePass Git Sync executable** to your password repository directory

3. **Run the setup command**:
   ```bash
   # If using the executable
   ./KeePassSyncTray --setup
   
   # If using Python source
   python /path/to/keepass-sync-tray.py --setup
   ```

4. **Run the application**:
   ```bash
   ./KeePassSyncTray
   ```

The setup command will:
- Create a `config.json` file with default settings
- Update your `.gitignore` to exclude the sync application files
- Check for your KeePass database
- Verify Git repository configuration

### Method 2: Fresh Setup

1. **Create and setup your password repository**:
   ```bash
   mkdir my-passwords
   cd my-passwords
   git init
   git remote add origin https://github.com/yourusername/your-passwords-repo.git
   ```

2. **Copy the KeePass Git Sync executable and your database** to the directory

3. **Run setup and start**:
   ```bash
   ./KeePassSyncTray --setup
   ./KeePassSyncTray
   ```

## Running the Application

#### From Source
```bash
# Install dependencies
pip install pystray pillow plyer

# Run the application
python keepass-sync-tray.py
```

#### From Executable (see Build Instructions below)
```bash
# Linux/macOS
./dist/KeePassSyncTray

# Windows
dist\KeePassSyncTray.exe
```

## Configuration

The application uses a `config.json` file for configuration. If no configuration file exists, default values are used.

### Configuration Options

```json
{
    "database": {
        "filename": "Passwords.kdbx",
        "monitor_interval": 2
    },
    "git": {
        "auto_pull": true,
        "auto_push": true,
        "commit_message_format": "Update from {hostname} at {timestamp}"
    },
    "notifications": {
        "enabled": true,
        "timeout": 3
    },
    "sync": {
        "timeout": 30
    }
}
```

### Configuration Details

- `database.filename`: Name of your KeePass database file
- `database.monitor_interval`: How often to check for changes (seconds)
- `git.auto_pull`: Whether to automatically pull changes before committing
- `git.auto_push`: Whether to automatically push commits to remote
- `git.commit_message_format`: Template for commit messages (`{hostname}` and `{timestamp}` are replaced)
- `notifications.enabled`: Whether to show desktop notifications
- `notifications.timeout`: How long notifications are displayed (seconds)
- `sync.timeout`: Maximum time to wait for sync operations (seconds)

## Building Standalone Executables

### Prerequisites

- Python 3.7 or higher
- Git installed and accessible from command line

### Linux/macOS

```bash
# Install build dependencies
pip install pystray pillow plyer pyinstaller

# Build executable
bash build-executable.sh
```

The executable will be created at `dist/KeePassSyncTray`.

### Windows

```batch
# Install build dependencies (if not already installed)
pip install pystray pillow plyer pyinstaller

# Build executable
build-windows.bat
```

The executable will be created at `dist\KeePassSyncTray.exe`.

### Manual Build with PyInstaller

```bash
pyinstaller --onefile \
    --windowed \
    --name "KeePassSyncTray" \
    --icon "keepass_icon.ico" \
    --add-data "sync-keepass.sh:." \
    --add-data "sync-keepass.bat:." \
    --add-data "keepass_icon.png:." \
    --add-data "keepass_icon.ico:." \
    --add-data "config.json.template:." \
    keepass-sync-tray.py
```

## Usage

### System Tray Controls

Right-click the system tray icon to access:

- **Start Sync**: Begin monitoring the database file
- **Stop Sync**: Stop monitoring
- **Sync Now**: Perform immediate synchronization
- **Status**: Show current application status
- **Last Sync**: Display information about the last sync operation
- **Exit**: Close the application

### Command Line Options

```bash
# Show help
./KeePassSyncTray --help

# Use custom configuration file
./KeePassSyncTray --config path/to/config.json

# Setup current directory for KeePass sync
./KeePassSyncTray --setup

# Create default configuration file
./KeePassSyncTray --create-config

# Python source equivalents
python keepass-sync-tray.py --help
python keepass-sync-tray.py --config path/to/config.json
python keepass-sync-tray.py --setup
python keepass-sync-tray.py --create-config
```

### Manual Sync Scripts

You can also run the sync scripts manually:

```bash
# Linux/macOS
bash sync-keepass.sh

# Windows
sync-keepass.bat
```

## How It Works

1. **File Monitoring**: The application continuously monitors the modification time of your KeePass database file
2. **Change Detection**: When a change is detected, the sync process is triggered
3. **Git Operations**: 
   - Pull latest changes from remote (if enabled)
   - Stage the database file
   - Commit with timestamp and hostname
   - Push to remote repository (if enabled)
4. **Notifications**: Desktop notifications inform you of sync success or failure

## Dependencies

### Runtime Dependencies
- **pystray**: System tray integration
- **Pillow (PIL)**: Image processing for tray icons
- **plyer**: Cross-platform desktop notifications

### System Dependencies
- **Git**: Must be installed and accessible from command line
- **Python 3.7+**: For running from source

### Optional Dependencies
- **jq**: For advanced JSON parsing in shell scripts (Linux/macOS)
- **PowerShell**: For JSON parsing on Windows (usually pre-installed)

## Troubleshooting

### Common Issues

**Git not found**
- Ensure Git is installed and in your system PATH
- Verify with `git --version`

**Python dependencies missing**
- Install with: `pip install pystray pillow plyer`

**Permission errors**
- Ensure the application has read/write access to the directory
- Check Git repository permissions

**Notification errors**
- Notifications may not work in all desktop environments
- Disable notifications in config if needed: `"enabled": false`

### Debug Mode

Run the application from terminal to see debug output:

```bash
python keepass-sync-tray.py
```

## Security Considerations

- The application only monitors and syncs your KeePass database file
- Git repository security depends on your remote repository configuration
- Consider using SSH keys for secure Git authentication
- Ensure your Git repository is private if it contains sensitive password databases

## File Structure

### Development Directory (keepass-git-sync/)
```
keepass-git-sync/
├── keepass-sync-tray.py      # Main application source
├── sync-keepass.sh           # Linux/macOS sync script  
├── sync-keepass.bat          # Windows sync script
├── build-executable.sh       # Linux build script
├── build-windows.bat         # Windows build script
├── KeePassSyncTray.spec      # PyInstaller spec file
├── keepass_icon.png          # Application icon
├── keepass_icon.ico          # Windows icon format
├── config.json.template      # Configuration template
├── .gitignore.template       # Gitignore template
├── README.md                 # This file
└── dist/                     # Built executables
    ├── KeePassSyncTray       # Linux executable
    └── KeePassSyncTray.exe   # Windows executable
```

### Your Password Repository (after setup)
```
your-password-repo/
├── KeePassSyncTray           # Sync application (in .gitignore)
├── config.json               # Sync configuration (in .gitignore)
├── Passwords.kdbx            # Your KeePass database (tracked by git)
├── .gitignore                # Updated to exclude sync app
└── .git/                     # Your git repository
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms if possible
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Changelog

### v2.0.0 (Current)
- Added JSON-based configuration system
- Made database filename configurable
- Added command-line argument support
- Removed hardcoded paths and PC-specific configurations
- Added `--setup` command for easy directory configuration
- Automatic .gitignore management to exclude sync application
- Improved cross-platform compatibility
- Enhanced error handling and logging
- Designed for deployment: copy executable to password repo and run

### v1.0.0
- Initial release with basic sync functionality
- System tray integration
- Cross-platform support