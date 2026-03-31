"""Monitor real user activity to detect true AFK status.

Uses Quartz CGEventSource on macOS (no permissions needed, no crash risk).
Falls back to time-since-start on other platforms."""

import platform
import time


_last_real_input: float = time.time()


def start():
    """No-op — CGEventSource queries are stateless, no listener needed."""
    pass


def idle_seconds() -> float:
    if platform.system() == "Darwin":
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
            pass
    return time.time() - _last_real_input


def reset():
    global _last_real_input
    _last_real_input = time.time()
