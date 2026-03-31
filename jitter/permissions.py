"""Check macOS permissions on launch. Non-blocking — app runs regardless."""

import platform
import subprocess


def check_all():
    """Show a hint if permissions are missing. Never blocks the app."""
    if platform.system() != "Darwin":
        return

    # On corporate/non-admin Macs, permissions may not be grantable.
    # The app still works via osascript + System Events fallback,
    # so we just show a non-blocking hint.
    missing = []

    # Check Accessibility
    try:
        from ApplicationServices import AXIsProcessTrusted
        if not AXIsProcessTrusted():
            missing.append("Accessibility")
    except ImportError:
        pass

    # Check Input Monitoring (try to start a listener)
    try:
        import time
        from pynput.keyboard import Listener
        listener = Listener(on_press=lambda k: None)
        listener.daemon = True
        listener.start()
        time.sleep(0.3)
        if not listener.running:
            missing.append("Input Monitoring")
        listener.stop()
    except Exception:
        missing.append("Input Monitoring")

    if not missing:
        return

    missing_str = " and ".join(missing)
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display dialog "Jitter works best with {missing_str} permissions '
             f'in System Settings → Privacy & Security.\\n\\n'
             f'Without them, Jitter will use fallback methods that '
             f'still work on most setups." '
             f'with title "Jitter" '
             f'buttons {{"OK"}} default button "OK" with icon note'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
