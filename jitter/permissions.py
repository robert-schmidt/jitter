"""Check and request macOS permissions. No-op on other platforms."""

import platform
import subprocess


def _can_simulate_keypress() -> bool:
    """Actually try to press F15. If it works, we have Accessibility."""
    try:
        from pynput.keyboard import Key, Controller
        kb = Controller()
        kb.press(Key.f15)
        kb.release(Key.f15)
        return True
    except Exception:
        return False


def _can_listen_keyboard() -> bool:
    """Start a listener briefly. If it works, we have Input Monitoring."""
    try:
        import threading
        from pynput.keyboard import Listener

        started = threading.Event()
        ok = [False]

        def _on_start():
            ok[0] = True
            started.set()

        listener = Listener(on_press=lambda k: None)
        listener.daemon = True
        listener.start()
        # Give it a moment to either start or fail
        import time
        time.sleep(0.3)
        ok[0] = listener.running
        listener.stop()
        return ok[0]
    except Exception:
        return False


def check_all():
    """Check permissions on launch. Show guidance only if something is missing."""
    if platform.system() != "Darwin":
        return

    has_accessibility = _can_simulate_keypress()
    has_input_monitoring = _can_listen_keyboard()

    if has_accessibility and has_input_monitoring:
        return

    missing = []
    if not has_accessibility:
        missing.append("• Accessibility — to simulate keypresses")
    if not has_input_monitoring:
        missing.append("• Input Monitoring — to detect real keyboard activity")

    missing_text = "\\n".join(missing)

    try:
        # Also trigger the system prompt for accessibility
        if not has_accessibility:
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
             'display dialog "Jitter is missing permissions:\\n\\n'
             f'{missing_text}'
             '\\n\\nGo to System Settings → Privacy & Security '
             'and add Jitter to the lists above, '
             'then relaunch the app." '
             'with title "Jitter — Permissions Required" '
             'buttons {"OK"} default button "OK" with icon caution'],
            capture_output=True, timeout=120,
        )
    except Exception:
        pass
