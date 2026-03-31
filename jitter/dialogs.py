"""About window and quit confirmation dialog."""

import tkinter as tk
from tkinter import messagebox

_about_window: tk.Tk | None = None

VERSION = "1.0.0"
REPO = "https://github.com/robert-schmidt/jitter"
COFFEE = "https://buymeacoffee.com/robbschmidt"

ABOUT_TEXT = """\
Jitter v{version}

A tiny system tray app that keeps Microsoft Teams
(and other apps) from marking you as "Away."

Sends a silent F15 keypress every 3 minutes.
After 60 minutes of no real input, inserts a
10-minute skip to mimic natural activity.

No network. No telemetry. No data collection.
Just a ghost key and peace of mind.

{repo}
""".format(version=VERSION, repo=REPO)


def _center(win: tk.Tk, w: int, h: int):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 3  # slightly above center looks better
    win.geometry(f"{w}x{h}+{x}+{y}")


def show_about():
    global _about_window
    if _about_window is not None:
        try:
            _about_window.lift()
            _about_window.focus_force()
            return
        except tk.TclError:
            _about_window = None

    win = tk.Tk()
    _about_window = win
    win.title("About Jitter")
    win.resizable(False, False)
    win.attributes("-topmost", True)

    label = tk.Label(win, text=ABOUT_TEXT, justify="center", padx=20, pady=15)
    label.pack(expand=True, fill="both")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=(0, 15))

    tk.Button(btn_frame, text="OK", width=10, command=win.destroy).pack()

    def _on_close():
        global _about_window
        _about_window = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)
    _center(win, 360, 310)
    win.mainloop()


def confirm_quit() -> bool:
    root = tk.Tk()
    root.withdraw()
    root.update_idletasks()
    root.attributes("-topmost", True)
    # Center the hidden root so the messagebox spawns centered
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"+{screen_w // 2}+{screen_h // 3}")
    result = messagebox.askyesno(
        "Quit Jitter",
        "Are you sure you want to quit Jitter?\n\nTeams will be able to detect idle status.",
        parent=root,
    )
    root.destroy()
    return result
