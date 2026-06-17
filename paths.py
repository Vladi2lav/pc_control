import os
import sys
import shutil
from pathlib import Path

# Check if running in a frozen PyInstaller bundle
IS_FROZEN = getattr(sys, 'frozen', False)

# App directory (where the executable/script resides)
if IS_FROZEN:
    APP_DIR = Path(sys.executable).parent.resolve()
else:
    APP_DIR = Path(__file__).parent.resolve()

# Check for portable mode
PORTABLE_FILE = APP_DIR / "portable.txt"
IS_PORTABLE = PORTABLE_FILE.exists()

if IS_PORTABLE:
    # Portable mode: save settings and modules locally in the app directory under data/
    DATA_DIR = APP_DIR / "data"
    SETTINGS_DIR = DATA_DIR / "settings"
    MODULES_DIR = DATA_DIR / "modules"
else:
    # Installed mode: save settings and modules in platform-specific standard directories
    if sys.platform == "win32":
        # Windows configuration: %APPDATA%\Lumen
        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = Path.home() / "AppData" / "Roaming"
        SETTINGS_DIR = Path(appdata) / "Lumen"
        
        # Windows dynamic modules/data: %LOCALAPPDATA%\Lumen
        local_appdata = os.environ.get("LOCALAPPDATA")
        if not local_appdata:
            local_appdata = Path.home() / "AppData" / "Local"
        DATA_DIR = Path(local_appdata) / "Lumen"
    else:
        # Linux configuration: ~/.config/lumen
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if not config_home:
            config_home = Path.home() / ".config"
        SETTINGS_DIR = Path(config_home) / "lumen"
        
        # Linux dynamic modules/data: ~/.local/share/lumen
        data_home = os.environ.get("XDG_DATA_HOME")
        if not data_home:
            data_home = Path.home() / ".local" / "share"
        DATA_DIR = Path(data_home) / "lumen"
        
    MODULES_DIR = DATA_DIR / "modules"

# Ensure directories exist
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
MODULES_DIR.mkdir(parents=True, exist_ok=True)

# Helper files
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

def initialize_user_directories():
    """
    Initializes user directories (settings, modules) by copying default assets
    from the application directory if they do not already exist in the user data directory.
    """
    # 1. Initialize settings.json if missing
    default_settings_src = APP_DIR / "settings.json"
    if not SETTINGS_FILE.exists():
        if default_settings_src.exists():
            try:
                shutil.copy2(default_settings_src, SETTINGS_FILE)
            except Exception as e:
                print(f"Error copying default settings: {e}", file=sys.stderr)
        else:
            # Create a fallback settings file
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    f.write('{"theme": "dark", "default_encoding": "utf-8"}')
            except Exception as e:
                print(f"Error creating fallback settings: {e}", file=sys.stderr)

    # 2. Initialize default modules if MODULES_DIR is empty
    # In frozen mode, default modules are placed in a 'default_modules' folder next to the app
    # In dev mode, they are read directly from the 'primer' folder in the root source directory
    default_modules_src = APP_DIR / ("default_modules" if IS_FROZEN else "primer")
    
    if default_modules_src.exists() and default_modules_src.is_dir():
        # Check if modules folder has any subfolders (meaning it's already initialized)
        existing_mods = [d for d in MODULES_DIR.iterdir() if d.is_dir()]
        if not existing_mods:
            for item in default_modules_src.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        shutil.copytree(item, MODULES_DIR / item.name, dirs_exist_ok=True)
                    except Exception as e:
                        print(f"Error copying default module {item.name}: {e}", file=sys.stderr)
