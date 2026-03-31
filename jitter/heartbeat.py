"""Timer loop that sends periodic keypresses to prevent idle status."""

import time
import threading
from pynput.keyboard import Key, Controller
from jitter import idle

INTERVAL = 180       # 3 minutes
SKIP_INTERVAL = 600  # 10 minutes when truly AFK

_keyboard = Controller()
_lock = threading.Lock()
_timer: threading.Timer | None = None
_running = False
_skipping = False
_next_pulse: float = 0


def _tick():
    global _timer, _skipping, _next_pulse
    with _lock:
        if not _running:
            return

        if idle.is_truly_afk() and not _skipping:
            _skipping = True
            _next_pulse = time.time() + SKIP_INTERVAL
            _timer = threading.Timer(SKIP_INTERVAL, _tick)
        else:
            if _skipping:
                idle.reset()
            _skipping = False
            _keyboard.press(Key.f15)
            _keyboard.release(Key.f15)
            _next_pulse = time.time() + INTERVAL
            _timer = threading.Timer(INTERVAL, _tick)

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
    global _running, _timer, _next_pulse
    with _lock:
        _running = False
        _next_pulse = 0
        if _timer is not None:
            _timer.cancel()
            _timer = None


def is_running() -> bool:
    return _running


def is_skipping() -> bool:
    return _skipping


def seconds_until_next() -> int:
    if not _running or _next_pulse == 0:
        return 0
    remaining = _next_pulse - time.time()
    return max(0, int(remaining))
