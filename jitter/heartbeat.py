"""Timer loop that simulates user activity to prevent idle/away status."""

import logging
import os
import platform
import random
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime
from jitter import idle, config

_caffeinate_proc: subprocess.Popen | None = None
_lock = threading.Lock()
_timer: threading.Timer | None = None
_running = False
_skipping = False
_outside_schedule = False
_next_pulse: float = 0

SCHEDULE_CHECK = 30

_log_path = os.path.join(os.path.expanduser("~"), ".jitter", "debug.log")
os.makedirs(os.path.dirname(_log_path), exist_ok=True)
_log = logging.getLogger("jitter.heartbeat")
_log.setLevel(logging.DEBUG)
_fh = logging.FileHandler(_log_path, mode="a")
_fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
_log.addHandler(_fh)

def _find_cliclick() -> str | None:
    """Find cliclick — check PATH, Homebrew, try to install if missing."""
    path = shutil.which("cliclick")
    if path:
        return path
    for p in ["/opt/homebrew/bin/cliclick", "/usr/local/bin/cliclick"]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    # Try to install via Homebrew
    if shutil.which("brew"):
        try:
            _log.debug("cliclick not found — attempting brew install...")
            subprocess.run(
                ["brew", "install", "cliclick"],
                capture_output=True, timeout=120,
            )
            for p in ["/opt/homebrew/bin/cliclick", "/usr/local/bin/cliclick"]:
                if os.path.isfile(p):
                    _log.debug("cliclick installed at %s", p)
                    return p
        except Exception as e:
            _log.debug("brew install cliclick failed: %s", e)
    return None


_cliclick = _find_cliclick()
if _cliclick:
    _log.debug("cliclick found at %s", _cliclick)
else:
    _log.debug("cliclick not found — install with: brew install cliclick")


def _simulate_activity():
    if platform.system() == "Darwin":
        _simulate_macos()
    else:
        _simulate_fallback()


def _simulate_macos():
    # Generate random offsets for natural-looking movement
    dx = random.randint(5, 20)
    dy = random.randint(5, 20)

    # METHOD 1: cliclick (native C binary — most reliable, separate process)
    if _cliclick:
        try:
            # Move mouse in a natural pattern using relative movements
            # Note: cliclick kp: only supports named keys (f1-f16, space, etc.), not modifiers
            result = subprocess.run(
                [_cliclick, f"m:+{dx},+0", f"m:+0,+{dy}", f"m:-{dx},-{dy}",
                 "kp:f15", "kp:f15"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                _log.debug("cliclick: moved +%d,+%d and f15", dx, dy)
            else:
                _log.warning("cliclick: exit code %d stderr: %s", result.returncode, result.stderr.strip())
        except Exception as e:
            _log.debug("cliclick: FAILED - %s", e)

    # METHOD 2: osascript + System Events (separate process, own Accessibility)
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events"\n'
             '  key code 56\n'
             '  key code 60\n'
             'end tell'],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            _log.debug("osascript: sent shift+rshift via System Events")
        else:
            _log.debug("osascript: exit code %d stderr: %s", result.returncode, result.stderr.strip())
    except Exception as e:
        _log.debug("osascript: FAILED - %s", e)

    # METHOD 3: Quartz CGEvent (direct, if Accessibility is granted to this process)
    try:
        from Quartz import (
            CGEventCreateMouseEvent, CGEventCreateKeyboardEvent,
            CGEventPost, CGEventCreate, CGEventGetLocation,
            kCGEventMouseMoved, kCGHIDEventTap,
        )
        event = CGEventCreate(None)
        pos = CGEventGetLocation(event)
        x, y = pos.x, pos.y

        # Natural multi-direction mouse movement
        for step_x, step_y in [(dx, 0), (0, dy), (-dx, -dy)]:
            CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(
                None, kCGEventMouseMoved, (x + step_x, y + step_y), 0))
            time.sleep(0.03 + random.random() * 0.04)  # 30-70ms between moves
            x, y = x + step_x, y + step_y

        # Return to original position
        orig = CGEventGetLocation(CGEventCreate(None))
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(
            None, kCGEventMouseMoved, (pos.x, pos.y), 0))

        # Shift key
        CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, 56, True))
        CGEventPost(kCGHIDEventTap, CGEventCreateKeyboardEvent(None, 56, False))
        _log.debug("CGEvent: multi-move (%+d,%+d) + shift at (%.0f, %.0f)", dx, dy, pos.x, pos.y)
    except Exception as e:
        _log.debug("CGEvent: FAILED - %s", e)

    # pynput removed — crashes on macOS Tahoe (EXC_BREAKPOINT in backend)


def _simulate_fallback():
    try:
        from pynput.keyboard import Key, Controller as KBController
        from pynput.mouse import Controller as MouseController
        kb = KBController()
        mouse = MouseController()
        dx, dy = random.randint(5, 20), random.randint(5, 20)
        mouse.move(dx, 0)
        time.sleep(0.05)
        mouse.move(0, dy)
        time.sleep(0.05)
        mouse.move(-dx, -dy)
        kb.press(Key.f15)
        kb.release(Key.f15)
    except Exception:
        pass


def _verify_idle_reset():
    if platform.system() != "Darwin":
        return
    try:
        from Quartz import (
            CGEventSourceSecondsSinceLastEventType,
            kCGEventSourceStateCombinedSessionState,
            kCGAnyInputEventType,
        )
        sys_idle = CGEventSourceSecondsSinceLastEventType(
            kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
        )
        if sys_idle < 2.0:
            _log.debug("VERIFY: system idle %.1fs — events ARE landing", sys_idle)
        else:
            _log.warning("VERIFY: system idle %.1fs — events NOT landing!", sys_idle)
    except Exception as e:
        _log.debug("VERIFY: could not check - %s", e)


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
            time.sleep(0.3)
            _verify_idle_reset()
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
