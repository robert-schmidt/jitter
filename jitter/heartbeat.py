"""Timer loop that simulates user activity to prevent idle/away status."""

import logging
import os
import platform
import subprocess
import time
import threading
from datetime import datetime
from jitter import idle, config

# Debug log to help diagnose issues
_log_path = os.path.join(os.path.expanduser("~"), ".jitter", "debug.log")
os.makedirs(os.path.dirname(_log_path), exist_ok=True)
logging.basicConfig(
    filename=_log_path,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("jitter")

_caffeinate_proc: subprocess.Popen | None = None
_lock = threading.Lock()
_timer: threading.Timer | None = None
_running = False
_skipping = False
_outside_schedule = False
_next_pulse: float = 0

SCHEDULE_CHECK = 30


def _simulate_activity():
    """Fire every available method to reset idle timers.
    At least one of these will work regardless of permission state."""
    if platform.system() == "Darwin":
        _simulate_macos()
    else:
        _simulate_fallback()


def _simulate_macos():
    # PRIMARY: osascript + System Events
    try:
        subprocess.Popen(
            ["osascript", "-e",
             'tell application "System Events"\n'
             '  key code 56\n'
             '  key code 60\n'
             '  key code 113\n'
             'end tell'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        _log.debug("osascript: sent shift+rshift+F15 via System Events")
    except OSError as e:
        _log.debug("osascript: FAILED - %s", e)

    # SECONDARY: Quartz CGEvent
    try:
        from Quartz import (
            CGEventCreateMouseEvent, CGEventCreateKeyboardEvent,
            CGEventPost, CGEventCreate, CGEventGetLocation,
            kCGEventMouseMoved, kCGHIDEventTap,
        )
        event = CGEventCreate(None)
        pos = CGEventGetLocation(event)
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(
            None, kCGEventMouseMoved, (pos.x + 1, pos.y), 0))
        time.sleep(0.05)
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(
            None, kCGEventMouseMoved, (pos.x, pos.y), 0))
        CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, 56, True))
        CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, 56, False))
        _log.debug("CGEvent: mouse nudge + shift at (%.0f, %.0f)", pos.x, pos.y)
    except Exception as e:
        _log.debug("CGEvent: FAILED - %s", e)

    # TERTIARY: pynput fallback
    try:
        from pynput.keyboard import Key, Controller
        kb = Controller()
        kb.press(Key.f15)
        kb.release(Key.f15)
        _log.debug("pynput: F15 sent")
    except Exception as e:
        _log.debug("pynput: FAILED - %s", e)


def _simulate_fallback():
    """Windows fallback using pynput."""
    try:
        from pynput.keyboard import Key, Controller as KBController
        from pynput.mouse import Controller as MouseController
        kb = KBController()
        mouse = MouseController()

        kb.press(Key.f15)
        kb.release(Key.f15)
        mouse.move(1, 0)
        mouse.move(-1, 0)
    except Exception:
        pass


def _poke_caffeinate(duration: int):
    global _caffeinate_proc
    if platform.system() != "Darwin":
        return
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
            _log.debug("TICK: outside schedule, sleeping %ds", SCHEDULE_CHECK)
            _next_pulse = time.time() + SCHEDULE_CHECK
            _timer = threading.Timer(SCHEDULE_CHECK, _tick)
        elif idle.idle_seconds() >= afk_threshold and not _skipping:
            _outside_schedule = False
            _skipping = True
            _log.debug("TICK: AFK skip (idle %.0fs >= %ds)", idle.idle_seconds(), afk_threshold)
            _next_pulse = time.time() + skip_interval
            _timer = threading.Timer(skip_interval, _tick)
        else:
            _outside_schedule = False
            if _skipping:
                idle.reset()
            _skipping = False
            _log.debug("TICK: pulsing (idle %.0fs, interval %ds)", idle.idle_seconds(), interval)
            _simulate_activity()
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
