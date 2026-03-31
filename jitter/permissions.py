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
             'display dialog "Jitter works best with Accessibility permission '
             'in System Settings → Privacy & Security → Accessibility.\\n\\n'
             'Without it, some activity simulation methods may not work." '
             'with title "Jitter" '
             'buttons {"OK"} default button "OK" with icon note'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
