"""Settings window with schedule and interval configuration."""

import tkinter as tk
from tkinter import ttk
from jitter import config

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_settings_window: tk.Tk | None = None


def _time_picker(parent, label_text: str, initial: str) -> tuple[ttk.Spinbox, ttk.Spinbox]:
    """Create an HH:MM time picker. Returns (hour_spin, minute_spin)."""
    frame = ttk.Frame(parent)
    frame.pack(fill="x", padx=20, pady=(8, 0))

    ttk.Label(frame, text=label_text, width=12, anchor="w").pack(side="left")

    h, m = initial.split(":")

    hour_values = [f"{i:02d}" for i in range(24)]
    hour_spin = ttk.Spinbox(frame, values=hour_values, width=3, wrap=True)
    hour_spin.set(h)
    hour_spin.pack(side="left", padx=(5, 0))

    ttk.Label(frame, text=":").pack(side="left")

    min_values = [f"{i:02d}" for i in range(0, 60, 15)]
    min_spin = ttk.Spinbox(frame, values=min_values, width=3, wrap=True)
    min_spin.set(m)
    min_spin.pack(side="left")

    return hour_spin, min_spin


def _read_time(hour_spin: ttk.Spinbox, min_spin: ttk.Spinbox) -> str:
    h = int(hour_spin.get())
    m = int(min_spin.get())
    return f"{h:02d}:{m:02d}"


def show():
    global _settings_window
    if _settings_window is not None:
        try:
            _settings_window.lift()
            _settings_window.focus_force()
            return
        except tk.TclError:
            _settings_window = None

    cfg = config.load()
    win = tk.Tk()
    _settings_window = win
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

    start_h, start_m = _time_picker(schedule_frame, "Start time:", cfg["schedule_start"])
    end_h, end_m = _time_picker(schedule_frame, "End time:", cfg["schedule_end"])

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

    # Pulse interval
    pulse_frame = ttk.Frame(timing_frame)
    pulse_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(pulse_frame, text="Pulse interval:", width=16, anchor="w").pack(side="left")
    pulse_var = tk.IntVar(value=cfg["pulse_interval"] // 60)
    pulse_spin = ttk.Spinbox(
        pulse_frame, from_=1, to=15, width=4, textvariable=pulse_var,
    )
    pulse_spin.pack(side="left")
    ttk.Label(pulse_frame, text="minutes").pack(side="left", padx=(5, 0))

    # AFK threshold
    afk_frame = ttk.Frame(timing_frame)
    afk_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(afk_frame, text="AFK threshold:", width=16, anchor="w").pack(side="left")
    afk_var = tk.IntVar(value=cfg["afk_threshold"] // 60)
    afk_spin = ttk.Spinbox(
        afk_frame, from_=5, to=180, width=4, textvariable=afk_var, increment=5,
    )
    afk_spin.pack(side="left")
    ttk.Label(afk_frame, text="minutes").pack(side="left", padx=(5, 0))

    # AFK skip duration
    skip_frame = ttk.Frame(timing_frame)
    skip_frame.pack(fill="x", padx=5, pady=(0, 5))
    ttk.Label(skip_frame, text="AFK skip:", width=16, anchor="w").pack(side="left")
    skip_var = tk.IntVar(value=cfg["afk_skip"] // 60)
    skip_spin = ttk.Spinbox(
        skip_frame, from_=1, to=30, width=4, textvariable=skip_var,
    )
    skip_spin.pack(side="left")
    ttk.Label(skip_frame, text="minutes").pack(side="left", padx=(5, 0))

    # --- Info note ---
    note_frame = ttk.Frame(win)
    note_frame.pack(fill="x", padx=15, pady=(5, 0))
    ttk.Label(
        note_frame,
        text="Note: Screensavers and display sleep may be\n"
             "prevented while Jitter is actively pulsing.",
        foreground="gray", justify="center",
    ).pack()

    # --- Buttons ---
    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=15)

    def _on_save():
        from tkinter import messagebox
        new_cfg = {
            "schedule_enabled": schedule_var.get(),
            "schedule_start": _read_time(start_h, start_m),
            "schedule_end": _read_time(end_h, end_m),
            "schedule_days": [i for i, v in enumerate(day_vars) if v.get()],
            "pulse_interval": max(60, pulse_var.get() * 60),
            "afk_threshold": max(300, afk_var.get() * 60),
            "afk_skip": max(60, skip_var.get() * 60),
        }
        config.save(new_cfg)
        messagebox.showinfo("Jitter", "Settings saved.\n\nQuit & reopen the app for the new settings to take effect.", parent=win)
        _on_close()

    def _on_close():
        global _settings_window
        _settings_window = None
        win.destroy()

    ttk.Button(btn_frame, text="Save", width=10, command=_on_save).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", width=10, command=_on_close).pack(side="left", padx=5)

    win.protocol("WM_DELETE_WINDOW", _on_close)
    win.mainloop()
