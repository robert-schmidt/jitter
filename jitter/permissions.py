"""Check and request macOS permissions. No-op on other platforms."""

import platform
import subprocess


def _is_trusted() -> bool:
    """Check accessibility permission without triggering a prompt."""
    try:
        from ApplicationServices import AXIsProcessTrusted
        return AXIsProcessTrusted()
    except ImportError:
        return True


def _prompt_accessibility():
    """Trigger the macOS accessibility permission prompt."""
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from Foundation import NSDictionary
        options = NSDictionary.dictionaryWithObject_forKey_(
            True, "AXTrustedCheckOptionPrompt"
        )
        AXIsProcessTrustedWithOptions(options)
    except ImportError:
        pass


def check_all() -> bool:
    """Run permission checks at startup. Returns True to continue launch."""
    if platform.system() != "Darwin":
        return True

    if _is_trusted():
        return True

    # Not trusted — trigger the system prompt and show guidance
    _prompt_accessibility()
    try:
        subprocess.run(
            ["osascript", "-e",
             'display dialog "Jitter needs two macOS permissions to work:\\n\\n'
             '1. Accessibility — to simulate keypresses\\n'
             '2. Input Monitoring — to detect real keyboard activity\\n\\n'
             'System Settings should have opened automatically.\\n'
             'Add Jitter to both lists under Privacy & Security, '
             'then relaunch the app." '
             'with title "Jitter — Permissions Required" '
             'buttons {"OK"} default button "OK" with icon caution'],
            capture_output=True, timeout=120,
        )
    except Exception:
        pass
    return False
