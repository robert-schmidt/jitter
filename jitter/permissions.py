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

    # Show dialog via native Python/tkinter (doesn't need Automation permission)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Jitter — Permissions",
            "Jitter works without permissions, but granting Accessibility "
            "enables additional idle reset methods (IOHIDPostEvent and "
            "cliclick mouse simulation).\n\n"
            "To grant: System Settings → Privacy & Security → Accessibility "
            "→ add Jitter.app\n\n"
            "Without Accessibility, Jitter still keeps Teams active using "
            "DeclareUserActivity and Teams window activation."
        )
        root.destroy()
    except Exception:
        # Fallback to osascript if tkinter unavailable
        try:
            subprocess.run(
                ["osascript", "-e",
                 'display dialog "Jitter works without permissions, but granting '
                 'Accessibility enables additional idle reset methods.\\n\\n'
                 'To grant: System Settings → Privacy & Security → Accessibility '
                 '→ add Jitter.app" '
                 'with title "Jitter" buttons {"OK"} default button "OK" '
                 'with icon note'],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass
