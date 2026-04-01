"""Check macOS permissions on launch. Non-blocking."""

import platform
import subprocess


def check_all():
    """Show a hint if Accessibility is missing. Never blocks the app."""
    if platform.system() != "Darwin":
        return

    try:
        from ApplicationServices import AXIsProcessTrusted
        if AXIsProcessTrusted():
            return
    except ImportError:
        return

    try:
        subprocess.run(
            ["osascript", "-e",
             'display dialog "Jitter needs these permissions in System Settings → Privacy & Security:\\n\\n'
             '1. Accessibility — for simulating input\\n'
             '2. Automation → System Events — for sending keystrokes\\n\\n'
             'Grant both, then relaunch." '
             'with title "Jitter" '
             'buttons {"OK"} default button "OK" with icon note'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
