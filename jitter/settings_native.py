"""Settings dialogs using native osascript on macOS."""

import json
import os
import platform
import subprocess

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
    "launch_at_login": False,
}

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load():
    try:
        with open(CONFIG_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)


def _save(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def _osa(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=120,
    )


def _osa_input(title: str, prompt: str, default: str) -> str | None:
    escaped_default = default.replace('"', '\\"')
    escaped_prompt = prompt.replace('"', '\\"')
    result = _osa(
        f'display dialog "{escaped_prompt}" '
        f'with title "{title}" '
        f'default answer "{escaped_default}" '
        f'buttons {{"Cancel", "OK"}} default button "OK"'
    )
    if result.returncode != 0:
        return None
    for part in result.stdout.strip().split(", "):
        if part.startswith("text returned:"):
            return part[len("text returned:"):]
    return None


def _osa_choose_days(current_days: list[int]) -> list[int] | None:
    current_names = [DAY_NAMES[i] for i in current_days]
    default_items = ", ".join(f'"{n}"' for n in current_names)
    all_items = ", ".join(f'"{n}"' for n in DAY_NAMES)
    result = _osa(
        f'choose from list {{{all_items}}} '
        f'with title "Active Days" '
        f'with prompt "Select active days (Cmd+click for multiple):" '
        f'default items {{{default_items}}} '
        f'with multiple selections allowed'
    )
    if result.returncode != 0 or result.stdout.strip() == "false":
        return None
    chosen = [s.strip() for s in result.stdout.strip().split(", ")]
    return [i for i, name in enumerate(DAY_NAMES) if name in chosen]


def _build_summary(cfg) -> str:
    days_str = ", ".join(DAY_NAMES[i] for i in cfg["schedule_days"])
    schedule_status = "ON" if cfg["schedule_enabled"] else "OFF"
    return (
        f"Current settings:\\n\\n"
        f"Schedule: {schedule_status}\\n"
        f"Active hours: {cfg['schedule_start']} – {cfg['schedule_end']}\\n"
        f"Active days: {days_str}\\n"
        f"Pulse interval: {cfg['pulse_interval'] // 60} min\\n"
        f"AFK threshold: {cfg['afk_threshold'] // 60} min\\n"
        f"AFK skip: {cfg['afk_skip'] // 60} min"
    )


def show_macos():
    cfg = _load()

    while True:
        menu_text = _build_summary(cfg)
        result = _osa(
            f'display dialog "{menu_text}" '
            f'with title "Jitter Settings" '
            f'buttons {{"Close", "Edit Schedule", "Edit Timing"}} '
            f'default button "Close"'
        )

        if result.returncode != 0:
            return

        output = result.stdout.strip()

        if "Edit Schedule" in output:
            _edit_schedule(cfg)
        elif "Edit Timing" in output:
            _edit_timing(cfg)
        else:
            return


def _edit_schedule(cfg):
    current = "ON" if cfg["schedule_enabled"] else "OFF"
    result = _osa(
        f'display dialog "Schedule is currently {current}." '
        f'with title "Schedule" '
        f'buttons {{"Cancel", "Toggle ON/OFF", "Edit Hours & Days"}} '
        f'default button "Edit Hours & Days"'
    )
    if result.returncode != 0:
        return

    output = result.stdout.strip()

    if "Toggle" in output:
        cfg["schedule_enabled"] = not cfg["schedule_enabled"]
        _save(cfg)
        status = "ON" if cfg["schedule_enabled"] else "OFF"
        _osa(f'display dialog "Schedule is now {status}.\\n\\nQuit & reopen the app for changes to take effect." '
             f'with title "Jitter" buttons {{"OK"}} default button "OK"')

    elif "Edit Hours" in output:
        val = _osa_input("Start Time", "Enter start time (HH:MM):", cfg["schedule_start"])
        if val and ":" in val:
            cfg["schedule_start"] = val

        val = _osa_input("End Time", "Enter end time (HH:MM):", cfg["schedule_end"])
        if val and ":" in val:
            cfg["schedule_end"] = val

        days = _osa_choose_days(cfg["schedule_days"])
        if days is not None:
            cfg["schedule_days"] = days

        _save(cfg)
        _osa('display dialog "Schedule updated.\\n\\nQuit & reopen the app for changes to take effect." '
             'with title "Jitter" buttons {"OK"} default button "OK"')


def _edit_timing(cfg):
    val = _osa_input("Pulse Interval",
                     "Minutes between activity pulses (1-15):",
                     str(cfg["pulse_interval"] // 60))
    if val:
        try:
            cfg["pulse_interval"] = max(60, min(900, int(val) * 60))
        except ValueError:
            pass

    val = _osa_input("AFK Threshold",
                     "Minutes of idle before triggering skip (5-180):",
                     str(cfg["afk_threshold"] // 60))
    if val:
        try:
            cfg["afk_threshold"] = max(300, min(10800, int(val) * 60))
        except ValueError:
            pass

    val = _osa_input("AFK Skip Duration",
                     "Minutes to wait during AFK skip (1-30):",
                     str(cfg["afk_skip"] // 60))
    if val:
        try:
            cfg["afk_skip"] = max(60, min(1800, int(val) * 60))
        except ValueError:
            pass

    _save(cfg)
    _osa('display dialog "Timing updated.\\n\\nQuit & reopen the app for changes to take effect." '
         'with title "Jitter" buttons {"OK"} default button "OK"')


def show():
    if platform.system() == "Darwin":
        show_macos()
    else:
        # Windows fallback — tkinter is bundled with Python on Windows
        from jitter.settings_ui import show as show_tk
        show_tk()
