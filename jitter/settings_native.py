"""Settings dialog. Uses system python3 + tkinter on macOS, inline tkinter on Windows."""

import json
import os
import platform
import subprocess
import sys
import textwrap

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".jitter")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# Self-contained tkinter settings script — no jitter imports needed.
# Launched as a standalone python3 process so tkinter gets the main thread.
_TK_SCRIPT = textwrap.dedent(r'''
import json, os, sys
from tkinter import *
from tkinter import ttk, messagebox

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".jitter")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULTS = {
    "schedule_enabled": True, "schedule_start": "09:00", "schedule_end": "18:00",
    "schedule_days": [0,1,2,3,4], "pulse_interval": 180,
    "afk_threshold": 3600, "afk_skip": 600, "launch_at_login": False,
}
DAY_NAMES = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def load():
    try:
        with open(CONFIG_PATH) as f: return {**DEFAULTS, **json.load(f)}
    except: return dict(DEFAULTS)

def save(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f: json.dump(cfg, f, indent=2)

cfg = load()
win = Tk()
win.title("Jitter Settings")
win.resizable(False, False)
win.attributes("-topmost", True)

# --- Schedule ---
sf = ttk.LabelFrame(win, text="Active Schedule", padding=10)
sf.pack(fill="x", padx=15, pady=(15,5))

sched_var = BooleanVar(value=cfg["schedule_enabled"])
ttk.Checkbutton(sf, text="Only run during scheduled hours", variable=sched_var).pack(anchor="w", padx=5)

tf1 = ttk.Frame(sf); tf1.pack(fill="x", padx=20, pady=(8,0))
ttk.Label(tf1, text="Start time:", width=12, anchor="w").pack(side="left")
hrs = [f"{i:02d}" for i in range(24)]
mins = [f"{i:02d}" for i in range(0,60,15)]
sh, sm = cfg["schedule_start"].split(":")
start_h = ttk.Spinbox(tf1, values=hrs, width=3, wrap=True); start_h.set(sh); start_h.pack(side="left", padx=(5,0))
ttk.Label(tf1, text=":").pack(side="left")
start_m = ttk.Spinbox(tf1, values=mins, width=3, wrap=True); start_m.set(sm); start_m.pack(side="left")

tf2 = ttk.Frame(sf); tf2.pack(fill="x", padx=20, pady=(8,0))
ttk.Label(tf2, text="End time:", width=12, anchor="w").pack(side="left")
eh, em = cfg["schedule_end"].split(":")
end_h = ttk.Spinbox(tf2, values=hrs, width=3, wrap=True); end_h.set(eh); end_h.pack(side="left", padx=(5,0))
ttk.Label(tf2, text=":").pack(side="left")
end_m = ttk.Spinbox(tf2, values=mins, width=3, wrap=True); end_m.set(em); end_m.pack(side="left")

df = ttk.Frame(sf); df.pack(fill="x", padx=20, pady=(10,5))
ttk.Label(df, text="Active days:", anchor="w").pack(anchor="w")
dr = ttk.Frame(df); dr.pack(fill="x", pady=(3,0))
day_vars = []
for i, name in enumerate(DAY_NAMES):
    v = BooleanVar(value=i in cfg["schedule_days"]); day_vars.append(v)
    ttk.Checkbutton(dr, text=name, variable=v).pack(side="left", padx=(0,6))

# --- Timing ---
tmf = ttk.LabelFrame(win, text="Timing", padding=10)
tmf.pack(fill="x", padx=15, pady=5)

pf = ttk.Frame(tmf); pf.pack(fill="x", padx=5, pady=(0,5))
ttk.Label(pf, text="Pulse interval:", width=16, anchor="w").pack(side="left")
pulse_var = IntVar(value=cfg["pulse_interval"]//60)
ttk.Spinbox(pf, from_=1, to=15, width=4, textvariable=pulse_var).pack(side="left")
ttk.Label(pf, text="minutes").pack(side="left", padx=(5,0))

af = ttk.Frame(tmf); af.pack(fill="x", padx=5, pady=(0,5))
ttk.Label(af, text="AFK threshold:", width=16, anchor="w").pack(side="left")
afk_var = IntVar(value=cfg["afk_threshold"]//60)
ttk.Spinbox(af, from_=5, to=180, width=4, textvariable=afk_var, increment=5).pack(side="left")
ttk.Label(af, text="minutes").pack(side="left", padx=(5,0))

skf = ttk.Frame(tmf); skf.pack(fill="x", padx=5, pady=(0,5))
ttk.Label(skf, text="AFK skip:", width=16, anchor="w").pack(side="left")
skip_var = IntVar(value=cfg["afk_skip"]//60)
ttk.Spinbox(skf, from_=1, to=30, width=4, textvariable=skip_var).pack(side="left")
ttk.Label(skf, text="minutes").pack(side="left", padx=(5,0))

# --- Note ---
nf = ttk.Frame(win); nf.pack(fill="x", padx=15, pady=(5,0))
ttk.Label(nf, text="Screensavers and display sleep may be prevented\nwhile Jitter is actively pulsing.",
    foreground="gray", justify="center").pack()

# --- Buttons ---
bf = ttk.Frame(win); bf.pack(pady=15)

def on_save():
    new = {
        "schedule_enabled": sched_var.get(),
        "schedule_start": f"{start_h.get()}:{start_m.get()}",
        "schedule_end": f"{end_h.get()}:{end_m.get()}",
        "schedule_days": [i for i,v in enumerate(day_vars) if v.get()],
        "pulse_interval": max(60, pulse_var.get()*60),
        "afk_threshold": max(300, afk_var.get()*60),
        "afk_skip": max(60, skip_var.get()*60),
        "launch_at_login": cfg.get("launch_at_login", False),
    }
    save(new)
    messagebox.showinfo("Jitter", "Settings saved.\n\nQuit & reopen the app for the new settings to take effect.", parent=win)
    win.destroy()

ttk.Button(bf, text="Save", width=10, command=on_save).pack(side="left", padx=5)
ttk.Button(bf, text="Cancel", width=10, command=win.destroy).pack(side="left", padx=5)
win.protocol("WM_DELETE_WINDOW", win.destroy)
win.mainloop()
''')


def show():
    # Launch tkinter settings as a standalone python3 process
    # This works on both macOS and Windows, and avoids the main-thread
    # restriction since the subprocess owns its own main thread.
    python = "python3" if platform.system() == "Darwin" else sys.executable
    subprocess.Popen(
        [python, "-c", _TK_SCRIPT],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
