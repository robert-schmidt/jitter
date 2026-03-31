#!/usr/bin/env python3
"""Standalone settings window. Runs as a separate process."""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".jitter")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "schedule_enabled": True,
    "schedule_start": "09:00",
    "schedule_end": "18:00",
    "schedule_days": [0, 1, 2, 3, 4],
    "pulse_interval": 180,
    "afk_threshold": 3600,
    "afk_skip": 600,
}


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            stored = json.load(f)
        return {**DEFAULTS, **stored}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def main():
    cfg = load_config()
    win = tk.Tk()
    win.title("Jitter Settings")
    win.resizable(False, False)
    win.attributes("-topmost", True)

    # --- Schedule section ---
    schedule_frame = ttk.LabelFrame(win, text="Active Schedule", padding=10)
    schedule_frame.pack(fill="x", padx=15, pady=(15, 5))

    schedule_var = tk.BooleanVar(value=cfg["schedule_enabled"])
    ttk.Checkbutton(
        schedule_frame, text="Only run during scheduled hours",
        variable=schedule_var,
    ).pack(anchor="w", padx=5)

    # Start time
    start_frame = ttk.Frame(schedule_frame)
    start_frame.pack(fill="x", padx=20, pady=(8, 0))
    ttk.Label(start_frame, text="Start time:", width=12, anchor="w").pack(side="left")
    sh, sm = cfg["schedule_start"].split(":")
    hour_vals = [f"{i:02d}" for i in range(24)]
    min_vals = [f"{i:02d}" for i in range(0, 60, 15)]
    start_h = ttk.Spinbox(start_frame, values=hour_vals, width=3, wrap=True)
    start_h.set(sh)
    start_h.pack(side="left", padx=(5, 0))
    ttk.Label(start_frame, text=":").pack(side="left")
    start_m = ttk.Spinbox(start_frame, values=min_vals, width=3, wrap=True)
    start_m.set(sm)
    start_m.pack(side="left")

    # End time
    end_frame = ttk.Frame(schedule_frame)
    end_frame.pack(fill="x", padx=20, pady=(8, 0))
    ttk.Label(end_frame, text="End time:", width=12, anchor="w").pack(side="left")
    eh, em = cfg["schedule_end"].split(":")
    end_h = ttk.Spinbox(end_frame, values=hour_vals, width=3, wrap=True)
    end_h.set(eh)
    end_h.pack(side="left", padx=(5, 0))
    ttk.Label(end_frame, text=":").pack(side="left")
    end_m = ttk.Spinbox(end_frame, values=min_vals, width=3, wrap=True)
    end_m.set(em)
    end_m.pack(side="left")

    # Day checkboxes
    days_frame = ttk.Frame(schedule_frame)
    days_frame.pack(fill="x", padx=20, pady=(10, 5))
    ttk.Label(days_frame, text="Active days:", anchor="w").pack(anchor="w")
    day_row = ttk.Frame(days_frame)
    day_row.pack(fill="x", pady=(3, 0))
    day_vars = []
    for i, name in enumerate(DAY_NAMES):
        var = tk.BooleanVar(value=i in cfg["schedule_days"])
        day_vars.append(var)
        ttk.Checkbutton(day_row, text=name, variable=var).pack(side="left", padx=(0, 6))

    # --- Timing section ---
    timing_frame = ttk.LabelFrame(win, text="Timing", padding=10)
    timing_frame.pack(fill="x", padx=15, pady=5)

    pulse_frame = ttk.Frame(timing_frame)
    pulse_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(pulse_frame, text="Pulse interval:", width=16, anchor="w").pack(side="left")
    pulse_var = tk.IntVar(value=cfg["pulse_interval"] // 60)
    ttk.Spinbox(pulse_frame, from_=1, to=15, width=4, textvariable=pulse_var).pack(side="left")
    ttk.Label(pulse_frame, text="minutes").pack(side="left", padx=(5, 0))

    afk_frame = ttk.Frame(timing_frame)
    afk_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(afk_frame, text="AFK threshold:", width=16, anchor="w").pack(side="left")
    afk_var = tk.IntVar(value=cfg["afk_threshold"] // 60)
    ttk.Spinbox(afk_frame, from_=5, to=180, width=4, textvariable=afk_var, increment=5).pack(side="left")
    ttk.Label(afk_frame, text="minutes").pack(side="left", padx=(5, 0))

    skip_frame = ttk.Frame(timing_frame)
    skip_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(skip_frame, text="AFK skip:", width=16, anchor="w").pack(side="left")
    skip_var = tk.IntVar(value=cfg["afk_skip"] // 60)
    ttk.Spinbox(skip_frame, from_=1, to=30, width=4, textvariable=skip_var).pack(side="left")
    ttk.Label(skip_frame, text="minutes").pack(side="left", padx=(5, 0))

    # --- Note ---
    note_frame = ttk.Frame(win)
    note_frame.pack(fill="x", padx=15, pady=(5, 0))
    ttk.Label(
        note_frame,
        text="Note: F15 keypresses generally do not prevent\n"
             "screensavers or display sleep from activating.",
        foreground="gray", justify="center",
    ).pack()

    # --- Buttons ---
    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=15)

    def _on_save():
        new_cfg = {
            "schedule_enabled": schedule_var.get(),
            "schedule_start": f"{start_h.get()}:{start_m.get()}",
            "schedule_end": f"{end_h.get()}:{end_m.get()}",
            "schedule_days": [i for i, v in enumerate(day_vars) if v.get()],
            "pulse_interval": max(60, pulse_var.get() * 60),
            "afk_threshold": max(300, afk_var.get() * 60),
            "afk_skip": max(60, skip_var.get() * 60),
        }
        save_config(new_cfg)
        messagebox.showinfo(
            "Jitter",
            "Settings saved.\n\nQuit & reopen the app for the new settings to take effect.",
            parent=win,
        )
        win.destroy()

    ttk.Button(btn_frame, text="Save", width=10, command=_on_save).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", width=10, command=win.destroy).pack(side="left", padx=5)

    win.protocol("WM_DELETE_WINDOW", win.destroy)
    win.mainloop()


if __name__ == "__main__":
    main()
