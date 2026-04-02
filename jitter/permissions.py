"""Check macOS permissions on launch. Non-blocking."""

import platform
import shutil
import subprocess


def _cliclick_works() -> bool:
    """Quick check: can cliclick send a no-op key event?"""
    for path in [shutil.which("cliclick"),
                 "/opt/homebrew/bin/cliclick",
                 "/usr/local/bin/cliclick"]:
        if path:
            try:
                r = subprocess.run([path, "kp:f15"], capture_output=True, timeout=3)
                if r.returncode == 0:
                    return True
            except Exception:
                pass
    return False


def check_all():
    """Show a hint if Accessibility is missing. Never blocks the app."""
    if platform.system() != "Darwin":
        return

    # If cliclick can send events, permissions are working
    if _cliclick_works():
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
