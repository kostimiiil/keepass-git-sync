#!/usr/bin/env python3
"""
KeePass Auto-Sync System Tray Application
Monitors KeePass database for changes and auto-syncs with Git
"""

import os
import sys
import time
import threading
import subprocess
import json
import socket
from datetime import datetime
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
from plyer import notification

class KeePassSyncTray:
    def __init__(self, config_file=None):
        # Handle both development and PyInstaller bundled execution
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            # Scripts are bundled in temp dir, database stays in exe directory
            self.script_dir = Path(sys._MEIPASS)
            self.base_dir = Path(sys.executable).parent
        else:
            # Running as Python script - everything in same directory
            self.script_dir = Path(__file__).parent
            self.base_dir = Path(__file__).parent
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        self.db_file = self.base_dir / self.config['database']['filename']
        # Choose appropriate sync script based on platform
        import platform
        if platform.system() == "Windows":
            self.sync_script = self.script_dir / "sync-keepass.bat"
            self.shell_cmd = ["cmd", "/c"]
        else:
            self.sync_script = self.script_dir / "sync-keepass.sh"
            self.shell_cmd = ["bash"]
        
        self.is_running = False
        self.sync_thread = None
        self.last_sync_time = None
        self.sync_count = 0
        self.last_mtime = 0
        
        # Debug output for troubleshooting
        print(f"Base directory: {self.base_dir}")
        print(f"Database file: {self.db_file}")
        print(f"Sync script: {self.sync_script}")
        print(f"DB file exists: {self.db_file.exists()}")
        print(f"Sync script exists: {self.sync_script.exists()}")
        
        # Create icon
        self.icon = None
        self.create_icon()
    
    def load_config(self, config_file=None):
        """Load configuration from JSON file with defaults"""
        default_config = {
            "database": {
                "filename": "Passwords.kdbx",
                "monitor_interval": 2
            },
            "git": {
                "auto_pull": True,
                "auto_push": True,
                "commit_message_format": "Update from {hostname} at {timestamp}"
            },
            "notifications": {
                "enabled": True,
                "timeout": 3
            },
            "sync": {
                "timeout": 30
            }
        }
        
        if config_file is None:
            config_file = self.base_dir / "config.json"
        else:
            config_file = Path(config_file)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                config = default_config.copy()
                config.update(user_config)
                print(f"Loaded configuration from {config_file}")
                return config
            except Exception as e:
                print(f"Error loading config file {config_file}: {e}")
                print("Using default configuration")
        else:
            print(f"Config file {config_file} not found, using defaults")
            print(f"You can create {config_file} to customize settings")
        
        return default_config
    
    def create_icon(self):
        """Create system tray icon"""
        # Try to load the icon file, fall back to generated icon if not found
        try:
            # Load the created icon
            image = Image.open(self.base_dir / "keepass_icon.png")
            # Resize to 64x64 for tray icon
            image = image.resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            # Fallback to generated icon
            width = 64
            height = 64
            
            # Create image with transparent background
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Define colors
            bg_color = (0, 119, 204, 255)  # KeePass blue
            key_color = (255, 193, 7, 255)  # Golden yellow for key
            teeth_color = (255, 235, 59, 255)  # Lighter yellow for key teeth
            
            # Draw background circle
            padding = width // 16
            draw.ellipse([padding, padding, width-padding, height-padding], 
                        fill=bg_color)
            
            # Draw key
            key_width = width // 3
            key_height = height // 2
            key_x = width // 2 - key_width // 2
            key_y = height // 2 - key_height // 4
            
            # Key handle (circular part)
            handle_size = key_width // 2
            handle_x = key_x + key_width // 4
            handle_y = key_y
            draw.ellipse([handle_x, handle_y, 
                         handle_x + handle_size, handle_y + handle_size],
                        fill=key_color)
            
            # Key handle hole
            hole_size = handle_size // 2
            hole_x = handle_x + handle_size // 4
            hole_y = handle_y + handle_size // 4
            draw.ellipse([hole_x, hole_y,
                         hole_x + hole_size, hole_y + hole_size],
                        fill=(0, 0, 0, 0))  # Transparent hole
            
            # Key shaft
            shaft_width = key_width // 2
            shaft_height = key_height // 2
            shaft_x = handle_x + handle_size // 4
            shaft_y = handle_y + handle_size
            draw.rectangle([shaft_x, shaft_y,
                           shaft_x + shaft_width, shaft_y + shaft_height],
                          fill=key_color)
            
            # Key teeth
            teeth_width = shaft_width // 4
            teeth_height = shaft_height // 4
            for i in range(2):
                tooth_x = shaft_x + shaft_width - teeth_width
                tooth_y = shaft_y + shaft_height - (i+1) * teeth_height * 2
                draw.rectangle([tooth_x, tooth_y,
                              tooth_x + teeth_width, tooth_y + teeth_height],
                             fill=teeth_color)
        
        menu = pystray.Menu(
            pystray.MenuItem("KeePass Auto-Sync", self.show_status, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Sync", self.start_sync, visible=lambda item: not self.is_running),
            pystray.MenuItem("Stop Sync", self.stop_sync, visible=lambda item: self.is_running),
            pystray.MenuItem("Sync Now", self.sync_now, visible=lambda item: self.is_running),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status", self.show_status),
            pystray.MenuItem("Last Sync", self.show_last_sync),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.icon = pystray.Icon("keepass-sync", image, "KeePass Auto-Sync", menu)
    
    def update_icon_color(self, syncing=False):
        """Update icon color based on sync status"""
        try:
            # Load the base icon and apply color overlay
            base_icon = Image.open(self.base_dir / "keepass_icon.png")
            base_icon = base_icon.resize((64, 64), Image.Resampling.LANCZOS)
            
            # Create colored overlay
            if syncing:
                overlay_color = (255, 193, 7, 128)  # Semi-transparent yellow
            elif self.is_running:
                overlay_color = (76, 175, 80, 96)   # Semi-transparent green
            else:
                overlay_color = (158, 158, 158, 128)  # Semi-transparent gray
            
            # Apply color overlay
            overlay = Image.new('RGBA', (64, 64), overlay_color)
            image = Image.alpha_composite(base_icon.convert('RGBA'), overlay)
            
        except Exception:
            # Fallback to simple colored icons
            width = 64
            height = 64
            
            if syncing:
                bg_color = (255, 193, 7, 255)  # Yellow
                key_color = (255, 152, 0, 255)  # Orange
            elif self.is_running:
                bg_color = (76, 175, 80, 255)   # Green
                key_color = (56, 142, 60, 255)  # Dark green
            else:
                bg_color = (158, 158, 158, 255)  # Gray
                key_color = (97, 97, 97, 255)   # Dark gray
            
            # Create image with transparent background
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw background circle
            padding = width // 16
            draw.ellipse([padding, padding, width-padding, height-padding], 
                        fill=bg_color)
            
            # Draw simple key shape
            key_width = width // 3
            key_height = height // 2
            key_x = width // 2 - key_width // 2
            key_y = height // 2 - key_height // 4
            
            # Key handle
            handle_size = key_width // 2
            handle_x = key_x + key_width // 4
            handle_y = key_y
            draw.ellipse([handle_x, handle_y, 
                         handle_x + handle_size, handle_y + handle_size],
                        fill=key_color)
            
            # Key shaft
            shaft_width = key_width // 2
            shaft_height = key_height // 2
            shaft_x = handle_x + handle_size // 4
            shaft_y = handle_y + handle_size
            draw.rectangle([shaft_x, shaft_y,
                           shaft_x + shaft_width, shaft_y + shaft_height],
                          fill=key_color)
        
        self.icon.icon = image
    
    def start_sync(self, icon=None, item=None):
        """Start the auto-sync monitoring"""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.sync_thread.start()
            self.update_icon_color()
            self.notify("KeePass Auto-Sync", "Monitoring started")
    
    def stop_sync(self, icon=None, item=None):
        """Stop the auto-sync monitoring"""
        if self.is_running:
            self.is_running = False
            if self.sync_thread:
                self.sync_thread.join(timeout=3)
            self.update_icon_color()
            self.notify("KeePass Auto-Sync", "Monitoring stopped")
    
    def sync_now(self, icon=None, item=None):
        """Perform immediate sync"""
        threading.Thread(target=self.perform_sync, daemon=True).start()
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print(f"Starting KeePass database monitoring...")
        self.last_mtime = self.get_file_mtime()
        
        while self.is_running:
            try:
                current_mtime = self.get_file_mtime()
                
                if current_mtime and current_mtime != self.last_mtime:
                    print(f"Change detected in {self.db_file.name}")
                    self.perform_sync()
                    self.last_mtime = current_mtime
                
                time.sleep(self.config['database']['monitor_interval'])  # Check interval from config
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(5)
    
    def get_file_mtime(self):
        """Get file modification time"""
        try:
            if self.db_file.exists():
                return self.db_file.stat().st_mtime
        except Exception as e:
            print(f"Error checking file: {e}")
        return None
    
    def perform_sync(self):
        """Execute the sync script"""
        try:
            # Update icon to show syncing
            self.update_icon_color(syncing=True)
            
            print("Executing sync script...")
            print(f"Command: {self.shell_cmd + [str(self.sync_script)]}")
            print(f"Working directory: {self.base_dir}")
            print(f"Script exists: {self.sync_script.exists()}")
            
            result = subprocess.run(
                self.shell_cmd + [str(self.sync_script)],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=self.config['sync']['timeout']
            )
            
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            
            if result.returncode == 0:
                self.sync_count += 1
                self.last_sync_time = datetime.now()
                print("Sync completed successfully")
                self.notify("KeePass Sync", "Database synchronized successfully")
            else:
                print(f"Sync failed with return code {result.returncode}")
                print(f"Error output: {result.stderr}")
                self.notify("KeePass Sync Error", f"Sync failed (code {result.returncode}) - check console", urgency='critical')
            
            # Reset icon color
            self.update_icon_color(syncing=False)
            
        except subprocess.TimeoutExpired:
            print("Sync script timed out")
            self.notify("KeePass Sync Error", "Sync timed out", urgency='critical')
            self.update_icon_color(syncing=False)
        except Exception as e:
            print(f"Error during sync: {e}")
            self.notify("KeePass Sync Error", f"Error: {e}", urgency='critical')
            self.update_icon_color(syncing=False)
    
    def show_status(self, icon=None, item=None):
        """Show current status"""
        status = "Running" if self.is_running else "Stopped"
        msg = f"Status: {status}\nSync count: {self.sync_count}"
        if self.last_sync_time:
            msg += f"\nLast sync: {self.last_sync_time.strftime('%H:%M:%S')}"
        self.notify("KeePass Auto-Sync Status", msg)
    
    def show_last_sync(self, icon=None, item=None):
        """Show last sync time"""
        if self.last_sync_time:
            time_ago = datetime.now() - self.last_sync_time
            minutes = int(time_ago.total_seconds() / 60)
            if minutes < 1:
                msg = "Just now"
            elif minutes == 1:
                msg = "1 minute ago"
            else:
                msg = f"{minutes} minutes ago"
            self.notify("Last Sync", f"{msg}\n{self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.notify("Last Sync", "No syncs yet")
    
    def notify(self, title, message, urgency='normal'):
        """Show desktop notification"""
        if not self.config['notifications']['enabled']:
            return
            
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='KeePass Sync',
                timeout=self.config['notifications']['timeout']
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.stop_sync()
        self.icon.stop()
    
    def run(self):
        """Run the system tray application"""
        # Auto-start sync on launch
        self.start_sync()
        
        # Run the icon
        self.icon.run()

def create_config_file():
    """Create a default config.json file"""
    config_path = Path('config.json')
    if config_path.exists():
        print(f"Configuration file {config_path} already exists!")
        return False
    
    default_config = {
        "database": {
            "filename": "Passwords.kdbx",
            "monitor_interval": 2
        },
        "git": {
            "auto_pull": True,
            "auto_push": True,
            "commit_message_format": "Update from {hostname} at {timestamp}"
        },
        "notifications": {
            "enabled": True,
            "timeout": 3
        },
        "sync": {
            "timeout": 30
        }
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        print(f"✓ Created default configuration file: {config_path}")
        return True
    except Exception as e:
        print(f"Error creating config file: {e}")
        return False

def setup_directory():
    """Setup the current directory for KeePass sync"""
    print("Setting up KeePass Git Sync directory...")
    print("========================================")
    
    success_count = 0
    total_steps = 0
    
    # 1. Check if git repository exists
    git_dir = Path('.git')
    if not git_dir.exists():
        print("⚠ Warning: This directory is not a Git repository.")
        print("  You should run 'git init' and set up your remote repository first.")
        print("  Example:")
        print("    git init")
        print("    git remote add origin https://github.com/yourusername/your-passwords-repo.git")
        print()
    else:
        print("✓ Git repository detected")
    
    # 2. Create config.json
    total_steps += 1
    if create_config_file():
        success_count += 1
    else:
        print("  (config.json already exists, skipping)")
    
    # 3. Update .gitignore
    total_steps += 1
    gitignore_path = Path('.gitignore')
    gitignore_entries = [
        "# KeePass Git Sync Application Files",
        "KeePassSyncTray",
        "KeePassSyncTray.exe",
        "KeePassSyncTray-Debug.exe",
        "keepass-sync-tray.py",
        "sync-keepass.sh",
        "sync-keepass.bat",
        "build-*.sh",
        "build-*.bat",
        "*.spec",
        "keepass_icon.*",
        "__pycache__/",
        "*.py[cod]",
        "build/",
        "dist/"
    ]
    
    try:
        # Read existing .gitignore if it exists
        existing_content = ""
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # Check which entries are missing
        missing_entries = []
        for entry in gitignore_entries:
            if entry not in existing_content and not entry.startswith("#"):
                missing_entries.append(entry)
        
        if missing_entries:
            # Add missing entries
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                if existing_content and not existing_content.endswith('\n'):
                    f.write('\n')
                f.write('\n# KeePass Git Sync Application Files\n')
                for entry in missing_entries:
                    f.write(f'{entry}\n')
            print(f"✓ Updated .gitignore with {len(missing_entries)} new entries")
        else:
            print("✓ .gitignore already contains necessary entries")
        success_count += 1
    except Exception as e:
        print(f"✗ Error updating .gitignore: {e}")
    
    # 4. Check for KeePass database
    total_steps += 1
    config = load_default_config()
    db_filename = config['database']['filename']
    db_path = Path(db_filename)
    
    if db_path.exists():
        print(f"✓ Found KeePass database: {db_filename}")
        success_count += 1
    else:
        print(f"⚠ KeePass database not found: {db_filename}")
        print(f"  Please copy your KeePass database file to this directory.")
        print(f"  Or update the filename in config.json if it has a different name.")
    
    # Summary
    print()
    print(f"Setup completed: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 Directory is ready for KeePass Git Sync!")
        print("\nNext steps:")
        print("1. Place your KeePass database in this directory")
        print("2. Run the sync application: KeePassSyncTray (or python keepass-sync-tray.py)")
        print("3. The application will automatically sync changes to Git")
    else:
        print("⚠ Some setup steps need attention. Please review the messages above.")

def load_default_config():
    """Load default configuration"""
    return {
        "database": {
            "filename": "Passwords.kdbx",
            "monitor_interval": 2
        },
        "git": {
            "auto_pull": True,
            "auto_push": True,
            "commit_message_format": "Update from {hostname} at {timestamp}"
        },
        "notifications": {
            "enabled": True,
            "timeout": 3
        },
        "sync": {
            "timeout": 30
        }
    }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KeePass Auto-Sync System Tray Application')
    parser.add_argument('--config', type=str, help='Path to configuration file (default: config.json)')
    parser.add_argument('--create-config', action='store_true', help='Create a default config.json file')
    parser.add_argument('--setup', action='store_true', help='Setup the current directory for KeePass sync (create config, gitignore)')
    args = parser.parse_args()
    
    if args.create_config:
        create_config_file()
        sys.exit(0)
        
    if args.setup:
        setup_directory()
        sys.exit(0)
    
    app = KeePassSyncTray(args.config)
    
    print("KeePass Auto-Sync Tray Application")
    print("===================================")
    print("The app is running in the system tray.")
    print("Right-click the tray icon for options.")
    print()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()