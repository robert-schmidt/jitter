"""Manage launch-at-login for macOS (LaunchAgent) and Windows (registry)."""

import os
import platform
import sys

_PLIST_NAME = "com.jitter.app.plist"
_PLIST_DIR = os.path.expanduser("~/Library/LaunchAgents")
_PLIST_PATH = os.path.join(_PLIST_DIR, _PLIST_NAME)

_WIN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_WIN_REG_NAME = "Jitter"


def _get_app_path() -> str:
    """Get the path to the running executable."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        exe = sys.executable
        # For macOS .app, we want the .app path, not the binary inside
        if platform.system() == "Darwin" and ".app/" in exe:
            return exe.split(".app/")[0] + ".app"
        return exe
    else:
        # Running from source
        return sys.executable


def is_enabled() -> bool:
    if platform.system() == "Darwin":
        return os.path.exists(_PLIST_PATH)
    elif platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, _WIN_REG_NAME)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False
    return False


def enable():
    app_path = _get_app_path()

    if platform.system() == "Darwin":
        os.makedirs(_PLIST_DIR, exist_ok=True)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jitter.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>open</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        with open(_PLIST_PATH, "w") as f:
            f.write(plist)

    elif platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, _WIN_REG_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
            winreg.CloseKey(key)
        except OSError:
            pass


def disable():
    if platform.system() == "Darwin":
        try:
            os.remove(_PLIST_PATH)
        except FileNotFoundError:
            pass

    elif platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WIN_REG_KEY, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, _WIN_REG_NAME)
            winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            pass


def set_enabled(enabled: bool):
    if enabled:
        enable()
    else:
        disable()
