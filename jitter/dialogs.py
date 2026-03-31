"""About window and quit confirmation dialog."""

import platform
import subprocess

VERSION = "1.0.0"
REPO = "https://github.com/robert-schmidt/jitter"

ABOUT_LINES = [
    f"Jitter v{VERSION}",
    "",
    "A tiny system tray app that keeps Microsoft Teams",
    '(and other apps) from marking you as "Away."',
    "",
    "Sends a silent activity pulse every 3 minutes",
    "to keep your status active. After 60 minutes of",
    "no real input, inserts a 10-minute skip to mimic",
    "natural human activity.",
    "",
    "No network. No telemetry. No data collection.",
    "Just a ghost key and peace of mind.",
    "",
    REPO,
]

ABOUT_TEXT = "\n".join(ABOUT_LINES)


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
    tk.Label(win, text=ABOUT_TEXT, justify="center", padx=20, pady=15).pack(expand=True, fill="both")
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
        osa_text = ABOUT_TEXT.replace('"', '\\"').replace("\n", "\\n")
        result = _osascript(
            f'display dialog "{osa_text}" with title "About Jitter" '
            'buttons {"GitHub", "OK"} default button "OK"'
        )
        if "GitHub" in result:
            subprocess.Popen(["open", REPO])
    else:
        _tk_about()


def confirm_quit() -> bool:
    if platform.system() == "Darwin":
        try:
            proc = subprocess.run(
                ["osascript", "-e",
                 'display dialog "Are you sure you want to quit Jitter?\\n\\n'
                 'Teams will be able to detect idle status." '
                 'with title "Quit Jitter" '
                 'buttons {"Cancel", "Quit"} default button "Cancel"'],
                capture_output=True, text=True, timeout=120,
            )
            # osascript returns exit code 1 when user clicks Cancel
            # and exit code 0 with "button returned:Quit" on Quit
            if proc.returncode == 0:
                return "Quit" in proc.stdout
            return False
        except Exception:
            # If osascript fails entirely, allow quit so the app isn't stuck
            return True
    else:
        return _tk_confirm_quit()
