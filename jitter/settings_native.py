"""Native macOS settings dialogs using osascript. Fallback to tkinter on Windows."""

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


def _osa(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=120,
    )
    return proc.stdout.strip()


def _osa_input(title: str, prompt: str, default: str) -> str | None:
    """Show an input dialog. Returns the text or None if cancelled."""
    escaped_default = default.replace('"', '\\"')
    escaped_prompt = prompt.replace('"', '\\"')
    try:
        result = subprocess.run(
            ["osascript", "-e",
             f'display dialog "{escaped_prompt}" '
             f'with title "{title}" '
             f'default answer "{escaped_default}" '
             f'buttons {{"Cancel", "OK"}} default button "OK"'],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return None
        # Parse "button returned:OK, text returned:value"
        for part in result.stdout.strip().split(", "):
            if part.startswith("text returned:"):
                return part[len("text returned:"):]
    except Exception:
        pass
    return None


def _osa_choose_days(current_days: list[int]) -> list[int] | None:
    """Show a day picker using choose from list."""
    current_names = [DAY_NAMES[i] for i in current_days]
    default_items = ", ".join(f'"{n}"' for n in current_names)
    all_items = ", ".join(f'"{n}"' for n in DAY_NAMES)
    try:
        result = subprocess.run(
            ["osascript", "-e",
             f'choose from list {{{all_items}}} '
             f'with title "Active Days" '
             f'with prompt "Select active days (Cmd+click for multiple):" '
             f'default items {{{default_items}}} '
             f'with multiple selections allowed'],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0 or result.stdout.strip() == "false":
            return None
        chosen = [s.strip() for s in result.stdout.strip().split(", ")]
        return [i for i, name in enumerate(DAY_NAMES) if name in chosen]
    except Exception:
        return None


def _build_summary(cfg) -> str:
    from jitter import startup
    days_str = ", ".join(DAY_NAMES[i] for i in cfg["schedule_days"])
    schedule_status = "ON" if cfg["schedule_enabled"] else "OFF"
    login_status = "ON" if startup.is_enabled() else "OFF"
    return (
        f"Current settings:\\n\\n"
        f"Launch at login: {login_status}\\n"
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
        try:
            result = subprocess.run(
                ["osascript", "-e",
                 f'display dialog "{menu_text}" '
                 f'with title "Jitter Settings" '
                 f'buttons {{"Edit Timing", "Edit Schedule", "General"}} '
                 f'default button "General"'],
                capture_output=True, text=True, timeout=300,
            )
        except Exception:
            return

        if result.returncode != 0:
            return

        output = result.stdout.strip()

        if "General" in output:
            _edit_general(cfg)
        elif "Edit Schedule" in output:
            _edit_schedule(cfg)
        elif "Edit Timing" in output:
            _edit_timing(cfg)
        else:
            return


def _edit_general(cfg):
    from jitter import startup
    current = "ON" if startup.is_enabled() else "OFF"
    try:
        result = subprocess.run(
            ["osascript", "-e",
             f'display dialog "Launch at login is currently {current}.\\n\\n'
             f'When enabled, Jitter will start automatically when you log in." '
             f'with title "General" '
             f'buttons {{"Cancel", "Toggle Launch at Login"}} '
             f'default button "Toggle Launch at Login"'],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return

        if "Toggle" in result.stdout:
            if startup.is_enabled():
                startup.disable()
                cfg["launch_at_login"] = False
                new_status = "OFF"
            else:
                startup.enable()
                cfg["launch_at_login"] = True
                new_status = "ON"
            _save(cfg)
            _osa(f'display dialog "Launch at login is now {new_status}." '
                 f'with title "Jitter" buttons {{"OK"}} default button "OK"')
    except Exception:
        pass


def _edit_schedule(cfg):
    # Toggle schedule on/off
    current = "ON" if cfg["schedule_enabled"] else "OFF"
    try:
        result = subprocess.run(
            ["osascript", "-e",
             f'display dialog "Schedule is currently {current}." '
             f'with title "Schedule" '
             f'buttons {{"Cancel", "Toggle ON/OFF", "Edit Hours & Days"}} '
             f'default button "Edit Hours & Days"'],
            capture_output=True, text=True, timeout=120,
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
            # Edit start time
            val = _osa_input("Start Time", "Enter start time (HH:MM):", cfg["schedule_start"])
            if val and ":" in val:
                cfg["schedule_start"] = val

            # Edit end time
            val = _osa_input("End Time", "Enter end time (HH:MM):", cfg["schedule_end"])
            if val and ":" in val:
                cfg["schedule_end"] = val

            # Edit days
            days = _osa_choose_days(cfg["schedule_days"])
            if days is not None:
                cfg["schedule_days"] = days

            _save(cfg)
            _osa('display dialog "Schedule updated.\\n\\nQuit & reopen the app for changes to take effect." '
                 'with title "Jitter" buttons {"OK"} default button "OK"')

    except Exception:
        pass


def _edit_timing(cfg):
    # Pulse interval
    val = _osa_input("Pulse Interval",
                     "Minutes between F15 keypresses (1-15):",
                     str(cfg["pulse_interval"] // 60))
    if val:
        try:
            mins = int(val)
            cfg["pulse_interval"] = max(60, min(900, mins * 60))
        except ValueError:
            pass

    # AFK threshold
    val = _osa_input("AFK Threshold",
                     "Minutes of idle before triggering skip (5-180):",
                     str(cfg["afk_threshold"] // 60))
    if val:
        try:
            mins = int(val)
            cfg["afk_threshold"] = max(300, min(10800, mins * 60))
        except ValueError:
            pass

    # AFK skip
    val = _osa_input("AFK Skip Duration",
                     "Minutes to wait during AFK skip (1-30):",
                     str(cfg["afk_skip"] // 60))
    if val:
        try:
            mins = int(val)
            cfg["afk_skip"] = max(60, min(1800, mins * 60))
        except ValueError:
            pass

    _save(cfg)
    _osa('display dialog "Timing updated.\\n\\nQuit & reopen the app for changes to take effect." '
         'with title "Jitter" buttons {"OK"} default button "OK"')


def show():
    if platform.system() == "Darwin":
        show_macos()
    else:
        from jitter.settings_ui import show as show_tk
        show_tk()
