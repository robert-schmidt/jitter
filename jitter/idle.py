"""Monitor real user activity to detect true AFK status.

Uses Quartz CGEventSource on macOS (no permissions needed, no crash risk).
Falls back to time-since-start on other platforms.

On enterprise Macs where CGEventSource isn't reset by synthetic events,
reset() overrides the idle time until real user input occurs."""

import platform
import time


_last_real_input: float = time.time()
_override_until: float = 0  # when set, idle_seconds() returns 0 until this time


def start():
    """No-op — CGEventSource queries are stateless, no listener needed."""
    pass


def idle_seconds() -> float:
    # If we recently reset (after AFK skip), report 0 until real input arrives
    # or the override window expires. This prevents re-triggering AFK skip
    # on systems where synthetic events don't reset CGEventSource.
    if _override_until and time.time() < _override_until:
        return time.time() - _last_real_input

    if platform.system() == "Darwin":
        try:
            from Quartz import (
                CGEventSourceSecondsSinceLastEventType,
                kCGEventSourceStateCombinedSessionState,
                kCGAnyInputEventType,
            )
            cg = CGEventSourceSecondsSinceLastEventType(
                kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
            )
            # If CGEventSource shows low idle, real input happened — clear override
            if cg < 5.0:
                _clear_override()
            return min(cg, time.time() - _last_real_input)
        except Exception:
            pass
    return time.time() - _last_real_input


def reset():
    """Reset idle tracking — called after AFK skip ends."""
    global _last_real_input, _override_until
    _last_real_input = time.time()
    # Override for the afk_threshold duration so we don't re-trigger AFK skip
    # immediately on systems where CGEventSource isn't reset by synthetic events
    _override_until = time.time() + 3600


def _clear_override():
    global _override_until
    _override_until = 0
