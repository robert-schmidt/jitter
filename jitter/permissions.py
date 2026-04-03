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
             'display dialog "Jitter works without permissions, but granting Accessibility '
             'in System Settings → Privacy & Security enables additional idle reset methods '
             '(IOHIDPostEvent and cliclick mouse simulation).\\n\\n'
             'To grant: System Settings → Privacy & Security → Accessibility → add Jitter.app\\n\\n'
             'Without Accessibility, Jitter still keeps Teams active using DeclareUserActivity '
             'and Teams window activation." '
             'with title "Jitter" '
             'buttons {"OK"} default button "OK" with icon note'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
