"""Monitor real keyboard input to detect true AFK status.

Uses pynput listener if Input Monitoring permission is available,
falls back to Quartz CGEventSource idle time query if not."""

import platform
import time
from pynput.keyboard import Key, Listener

_last_real_input: float = time.time()
_listener: Listener | None = None
_use_quartz_fallback = False


def _on_press(key):
    global _last_real_input
    # Ignore our own simulated keys
    if key == Key.f15 or key == Key.shift or key == Key.shift_l or key == Key.shift_r:
        return
    _last_real_input = time.time()


def start():
    """Start the global listener. Call once at app startup."""
    global _listener, _use_quartz_fallback
    if _listener is not None:
        return
    try:
        _listener = Listener(on_press=_on_press)
        _listener.daemon = True
        _listener.start()
        # Check if it actually started (may fail silently without Input Monitoring)
        time.sleep(0.3)
        if not _listener.running:
            _use_quartz_fallback = True
    except Exception:
        _use_quartz_fallback = True


def idle_seconds() -> float:
    if _use_quartz_fallback and platform.system() == "Darwin":
        return _quartz_idle_seconds()
    return time.time() - _last_real_input


def _quartz_idle_seconds() -> float:
    """Query system idle time directly via Quartz. Works without Input Monitoring."""
    try:
        from Quartz import (
            CGEventSourceSecondsSinceLastEventType,
            kCGEventSourceStateCombinedSessionState,
            kCGAnyInputEventType,
        )
        return CGEventSourceSecondsSinceLastEventType(
            kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
        )
    except Exception:
        return time.time() - _last_real_input


def reset():
    global _last_real_input
    _last_real_input = time.time()
