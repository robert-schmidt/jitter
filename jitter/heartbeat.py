"""Timer loop that sends periodic keypresses and caffeinate to prevent idle status."""

import platform
import subprocess
import time
import threading
from datetime import datetime
from pynput.keyboard import Key, Controller as KBController
from pynput.mouse import Controller as MouseController
from jitter import idle, config

_keyboard = KBController()
_mouse = MouseController()
_caffeinate_proc: subprocess.Popen | None = None
_lock = threading.Lock()
_timer: threading.Timer | None = None
_running = False
_skipping = False
_outside_schedule = False
_next_pulse: float = 0

SCHEDULE_CHECK = 30  # re-check schedule every 30s when outside window


def _poke_caffeinate(duration: int):
    """On macOS, use caffeinate -u to assert user activity for the given duration.
    This resets IOKit HIDIdleTime, which is what Teams actually checks."""
    global _caffeinate_proc
    if platform.system() != "Darwin":
        return
    # Kill any existing caffeinate before starting a new one
    if _caffeinate_proc is not None:
        try:
            _caffeinate_proc.kill()
        except OSError:
            pass
    try:
        _caffeinate_proc = subprocess.Popen(
            ["caffeinate", "-u", "-t", str(duration + 30)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def _is_within_schedule() -> bool:
    cfg = config.load()
    if not cfg["schedule_enabled"]:
        return True

    now = datetime.now()
    if now.weekday() not in cfg["schedule_days"]:
        return False

    current = now.strftime("%H:%M")
    start = cfg["schedule_start"]
    end = cfg["schedule_end"]

    if start <= end:
        return start <= current < end
    else:
        # Overnight schedule, e.g. 22:00 - 06:00
        return current >= start or current < end


def _tick():
    global _timer, _skipping, _next_pulse, _outside_schedule
    with _lock:
        if not _running:
            return

        cfg = config.load()
        interval = cfg["pulse_interval"]
        skip_interval = cfg["afk_skip"]
        afk_threshold = cfg["afk_threshold"]

        if not _is_within_schedule():
            _outside_schedule = True
            _skipping = False
            _next_pulse = time.time() + SCHEDULE_CHECK
            _timer = threading.Timer(SCHEDULE_CHECK, _tick)
        elif idle.idle_seconds() >= afk_threshold and not _skipping:
            _outside_schedule = False
            _skipping = True
            _next_pulse = time.time() + skip_interval
            _timer = threading.Timer(skip_interval, _tick)
        else:
            _outside_schedule = False
            if _skipping:
                idle.reset()
            _skipping = False
            # Triple approach to reset all idle detectors:
            # 1. F15 keypress (invisible key, no side effects)
            _keyboard.press(Key.f15)
            _keyboard.release(Key.f15)
            # 2. Mouse nudge (1px right then back — registers as Quartz event,
            #    which is what Teams actually checks via CGEventSource)
            try:
                pos = _mouse.position
                _mouse.move(1, 0)
                _mouse.move(-1, 0)
            except Exception:
                pass
            # 3. caffeinate -u (resets IOKit HIDIdleTime)
            _poke_caffeinate(interval)
            _next_pulse = time.time() + interval
            _timer = threading.Timer(interval, _tick)

        _timer.daemon = True
        _timer.start()


def start():
    global _running
    with _lock:
        if _running:
            return
        _running = True
    _tick()


def stop():
    global _running, _timer, _next_pulse, _caffeinate_proc
    with _lock:
        _running = False
        _next_pulse = 0
        if _timer is not None:
            _timer.cancel()
            _timer = None
        if _caffeinate_proc is not None:
            try:
                _caffeinate_proc.kill()
            except OSError:
                pass
            _caffeinate_proc = None


def is_running() -> bool:
    return _running


def is_skipping() -> bool:
    return _skipping


def is_outside_schedule() -> bool:
    return _outside_schedule


def seconds_until_next() -> int:
    if not _running or _next_pulse == 0:
        return 0
    remaining = _next_pulse - time.time()
    return max(0, int(remaining))
