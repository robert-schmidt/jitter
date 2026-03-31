"""Check and request macOS permissions. No-op on other platforms."""

import os
import platform
import subprocess

# Marker file so we only show the permission hint once
_MARKER = os.path.join(os.path.expanduser("~"), ".jitter_permissions_prompted")


def _already_prompted() -> bool:
    return os.path.exists(_MARKER)


def _mark_prompted():
    try:
        open(_MARKER, "w").close()
    except OSError:
        pass


def check_all():
    """Show permission guidance on first launch only (macOS)."""
    if platform.system() != "Darwin":
        return
    if _already_prompted():
        return

    # First launch — trigger the system accessibility prompt and show guidance
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from Foundation import NSDictionary
        options = NSDictionary.dictionaryWithObject_forKey_(
            True, "AXTrustedCheckOptionPrompt"
        )
        AXIsProcessTrustedWithOptions(options)
    except ImportError:
        pass

    try:
        subprocess.run(
            ["osascript", "-e",
             'display dialog "Jitter needs two macOS permissions to work:\\n\\n'
             '1. Accessibility — to simulate keypresses\\n'
             '2. Input Monitoring — to detect real keyboard activity\\n\\n'
             'System Settings should have opened automatically.\\n'
             'Add Jitter to both lists under Privacy & Security, '
             'then relaunch the app." '
             'with title "Jitter — Permissions Required" '
             'buttons {"OK"} default button "OK" with icon caution'],
            capture_output=True, timeout=120,
        )
    except Exception:
        pass

    _mark_prompted()
