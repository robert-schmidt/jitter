"""Check macOS permissions on launch. Non-blocking."""

import platform
import subprocess


def _has_accessibility() -> bool:
    try:
        from ApplicationServices import AXIsProcessTrusted
        return AXIsProcessTrusted()
    except ImportError:
        return True  # can't check, assume OK


def _has_automation() -> bool:
    """Test Automation permission by sending a harmless Apple Event."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to return name'],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return True  # can't check, assume OK


def check_all():
    """Show a hint only if permissions are actually missing."""
    if platform.system() != "Darwin":
        return

    has_acc = _has_accessibility()
    has_auto = _has_automation()

    if has_acc and has_auto:
        return

    missing = []
    if not has_acc:
        missing.append("Accessibility — for simulating input")
    if not has_auto:
        missing.append("Automation → System Events — for sending keystrokes")

    missing_text = "\\n".join(f"{i+1}. {m}" for i, m in enumerate(missing))

    try:
        subprocess.run(
            ["osascript", "-e",
             f'display dialog "Jitter needs these permissions in System Settings → Privacy & Security:\\n\\n'
             f'{missing_text}\\n\\n'
             f'Grant them, then relaunch." '
             f'with title "Jitter" '
             f'buttons {{"OK"}} default button "OK" with icon note'],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass
