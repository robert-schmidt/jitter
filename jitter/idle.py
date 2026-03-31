"""Monitor real keyboard input to detect true AFK status."""

import time
from pynput.keyboard import Key, Listener

AFK_THRESHOLD = 3600  # 60 minutes in seconds

_last_real_input: float = time.time()
_listener: Listener | None = None


def _on_press(key):
    global _last_real_input
    if key == Key.f15:
        return
    _last_real_input = time.time()


def start():
    """Start the global listener. Call once at app startup."""
    global _listener
    if _listener is not None:
        return
    _listener = Listener(on_press=_on_press)
    _listener.daemon = True
    _listener.start()


def idle_seconds() -> float:
    return time.time() - _last_real_input


def reset():
    global _last_real_input
    _last_real_input = time.time()


def is_truly_afk() -> bool:
    return idle_seconds() >= AFK_THRESHOLD
