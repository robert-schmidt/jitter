"""Check and request macOS permissions. No-op on other platforms."""

import platform
import sys


def check_accessibility() -> bool:
    """Check if accessibility is granted. On macOS, prompts the user if not.
    Returns True if granted or not on macOS."""
    if platform.system() != "Darwin":
        return True

    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        from Foundation import NSDictionary

        options = NSDictionary.dictionaryWithObject_forKey_(
            True, "AXTrustedCheckOptionPrompt"
        )
        return AXIsProcessTrustedWithOptions(options)
    except ImportError:
        return True


def check_all() -> bool:
    """Run all permission checks at startup. Returns True if all granted."""
    if platform.system() != "Darwin":
        return True

    trusted = check_accessibility()

    if not trusted:
        # Show a guidance dialog since the system prompt can be easy to miss
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            messagebox.showwarning(
                "Jitter — Permissions Required",
                "Jitter needs two macOS permissions to work:\n\n"
                "1. Accessibility — to simulate keypresses\n"
                "2. Input Monitoring — to detect real keyboard activity\n\n"
                "System Settings should have opened automatically.\n"
                "Add Jitter to both lists under Privacy & Security,\n"
                "then relaunch the app.",
                parent=root,
            )
            root.destroy()
        except Exception:
            pass
        return False

    return True
