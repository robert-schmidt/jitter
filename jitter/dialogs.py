"""About window and quit confirmation dialog."""

import platform
import subprocess

VERSION = "1.0.0"
REPO = "https://github.com/robert-schmidt/jitter"

ABOUT_TEXT = (
    f"Jitter v{VERSION}\\n\\n"
    "A tiny system tray app that keeps Microsoft Teams "
    "(and other apps) from marking you as \\"Away.\\"\\n\\n"
    "Sends a silent F15 keypress every 3 minutes. "
    "After 60 minutes of no real input, inserts a "
    "10-minute skip to mimic natural activity.\\n\\n"
    "No network. No telemetry. No data collection.\\n"
    f"Just a ghost key and peace of mind.\\n\\n{REPO}"
)


def _osascript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=120,
    )
    return result.stdout.strip()


def _tk_about():
    import tkinter as tk
    win = tk.Tk()
    win.title("About Jitter")
    win.resizable(False, False)
    text = ABOUT_TEXT.replace("\\n", "\n").replace('\\"', '"')
    tk.Label(win, text=text, justify="center", padx=20, pady=15).pack(expand=True, fill="both")
    tk.Button(win, text="OK", width=10, command=win.destroy).pack(pady=(0, 15))
    win.mainloop()


def _tk_confirm_quit() -> bool:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno(
        "Quit Jitter",
        "Are you sure you want to quit Jitter?\n\nTeams will be able to detect idle status.",
    )
    root.destroy()
    return result


def show_about():
    if platform.system() == "Darwin":
        _osascript(
            f'display dialog "{ABOUT_TEXT}" with title "About Jitter" '
            'buttons {{"OK"}} default button "OK"'
        )
    else:
        _tk_about()


def confirm_quit() -> bool:
    if platform.system() == "Darwin":
        try:
            result = _osascript(
                'display dialog "Are you sure you want to quit Jitter?\\n\\n'
                'Teams will be able to detect idle status." '
                'with title "Quit Jitter" '
                'buttons {"Cancel", "Quit"} default button "Cancel" cancel button "Cancel"'
            )
            return "Quit" in result
        except subprocess.TimeoutExpired:
            return False
    else:
        return _tk_confirm_quit()
