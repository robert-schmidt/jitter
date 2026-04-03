"""Check macOS permissions on launch. Non-blocking."""

import logging
import os
import platform
import subprocess
import threading

_log = logging.getLogger("jitter.permissions")
_log.setLevel(logging.DEBUG)
_log_path = os.path.join(os.path.expanduser("~"), ".jitter", "debug.log")
os.makedirs(os.path.dirname(_log_path), exist_ok=True)
_fh = logging.FileHandler(_log_path, mode="a")
_fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
_log.addHandler(_fh)

_DIALOG_MSG = (
    "Jitter needs Accessibility permission to simulate mouse "
    "movement and keep Teams active.\\n\\n"
    "To grant: System Settings → Privacy & Security → Accessibility "
    "→ add Jitter.app\\n\\nThen relaunch Jitter."
)


def _show_dialog():
    """Show permission dialog in background thread — never blocks the app."""
    # osascript looks native and always appears on top
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display dialog "{_DIALOG_MSG}" '
             'with title "Jitter" buttons {"OK"} default button "OK" '
             'with icon caution'],
            capture_output=True, timeout=15,
        )
    except Exception:
        pass


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
        # Clear the "dialog shown" flag so it shows again if permission is revoked
        _dismissed_path = os.path.join(os.path.expanduser("~"), ".jitter", ".permissions_shown")
        if os.path.exists(_dismissed_path):
            os.remove(_dismissed_path)
        return

    _log.warning("Accessibility: NOT granted — IOHIDPostEvent and cliclick "
                 "may not work. Grant in System Settings → Privacy & Security "
                 "→ Accessibility → add Jitter.app")

    # Only show the dialog once — don't nag on every launch
    dismissed_path = os.path.join(os.path.expanduser("~"), ".jitter", ".permissions_shown")
    if os.path.exists(dismissed_path):
        _log.debug("Permission dialog already shown, skipping")
        return

    # Mark as shown before launching the dialog
    try:
        with open(dismissed_path, "w") as f:
            f.write("1")
    except OSError:
        pass

    # Show dialog in a background thread so it never blocks tray icon loading
    t = threading.Thread(target=_show_dialog, daemon=True)
    t.start()
