"""Check macOS permissions on launch. Non-blocking."""

import logging
import platform
import subprocess

_log = logging.getLogger("jitter.permissions")


def check_all():
    """Check permissions and show a hint if Accessibility is missing."""
    if platform.system() != "Darwin":
        return

    # Check if THIS process has Accessibility (not cliclick's own entry)
    trusted = False
    try:
        from ApplicationServices import AXIsProcessTrusted
        trusted = AXIsProcessTrusted()
    except ImportError:
        return

    if trusted:
        _log.info("Accessibility: granted")
        return

    _log.warning("Accessibility: NOT granted — IOHIDPostEvent and cliclick "
                 "may not work. Grant in System Settings → Privacy & Security "
                 "→ Accessibility → add Jitter.app")

    # Show dialog — try osascript first (looks native), fall back to tkinter
    shown = False
    try:
        r = subprocess.run(
            ["osascript", "-e",
             'display dialog "Jitter needs Accessibility permission to '
             'simulate mouse movement and keep Teams active.\\n\\n'
             'To grant: System Settings → Privacy & Security → Accessibility '
             '→ add Jitter.app\\n\\nThen relaunch Jitter." '
             'with title "Jitter" buttons {"OK"} default button "OK" '
             'with icon caution'],
            capture_output=True, timeout=15,
        )
        shown = r.returncode == 0
    except Exception:
        pass

    if not shown:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            # Force to front — LSUIElement apps have no dock presence
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
            messagebox.showwarning(
                "Jitter — Accessibility Required",
                "Jitter needs Accessibility permission to simulate mouse "
                "movement and keep Teams active.\n\n"
                "To grant:\n"
                "System Settings → Privacy & Security → Accessibility "
                "→ add Jitter.app\n\n"
                "Then relaunch Jitter."
            )
            root.destroy()
        except Exception:
            pass
