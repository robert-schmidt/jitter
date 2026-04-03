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


def _post_hid_event(dx: int, dy: int):
    """Post a NX_MOUSEMOVED event via IOHIDPostEvent — resets the real HID idle timer.

    CGEventPost, CGWarpMouseCursorPosition, and cliclick all use higher-level APIs
    that do NOT reset IOHIDSystem's idle counter on newer macOS. This is the only
    programmatic way to reset it without physical hardware input.
    """
    import ctypes
    import struct

    NX_MOUSEMOVED = 5

    class NXEventData(ctypes.Structure):
        _fields_ = [("data", (ctypes.c_uint8 * 64))]

    class IOGPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_int16), ("y", ctypes.c_int16)]

    iokit = ctypes.cdll.LoadLibrary(
        "/System/Library/Frameworks/IOKit.framework/IOKit")
    libc = ctypes.cdll.LoadLibrary("/usr/lib/libSystem.B.dylib")

    libc.mach_task_self.restype = ctypes.c_uint32
    iokit.IOServiceMatching.restype = ctypes.c_void_p
    iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
    iokit.IOServiceGetMatchingService.restype = ctypes.c_uint32
    iokit.IOServiceGetMatchingService.argtypes = [
        ctypes.c_uint32, ctypes.c_void_p]
    iokit.IOServiceOpen.restype = ctypes.c_int
    iokit.IOServiceOpen.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32)]
    iokit.IOHIDPostEvent.restype = ctypes.c_int
    iokit.IOHIDPostEvent.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, IOGPoint,
        ctypes.POINTER(NXEventData), ctypes.c_uint32,
        ctypes.c_uint32, ctypes.c_uint32]
    iokit.IOServiceClose.restype = ctypes.c_int
    iokit.IOServiceClose.argtypes = [ctypes.c_uint32]
    iokit.IOObjectRelease.restype = ctypes.c_int
    iokit.IOObjectRelease.argtypes = [ctypes.c_uint32]

    service = iokit.IOServiceGetMatchingService(
        0, iokit.IOServiceMatching(b"IOHIDSystem"))
    if not service:
        raise RuntimeError("IOHIDSystem service not found")

    connect = ctypes.c_uint32()
    kr = iokit.IOServiceOpen(
        service, libc.mach_task_self(),
        1,  # kIOHIDParamConnectType
        ctypes.byref(connect))
    iokit.IOObjectRelease(service)
    if kr != 0:
        raise RuntimeError(f"IOServiceOpen failed: {kr:#x}")

    try:
        event_data = NXEventData()
        # NXEventData mouseMove: first 4 bytes = dx (int32), next 4 = dy (int32)
        struct.pack_into("<ii", event_data.data, 0, dx, dy)
        location = IOGPoint(x=0, y=0)

        kr = iokit.IOHIDPostEvent(
            connect.value, NX_MOUSEMOVED, location,
            ctypes.byref(event_data),
            2,  # kNXEventDataVersion
            0,  # eventFlags
            0)  # options
        if kr != 0:
            raise RuntimeError(f"IOHIDPostEvent failed: {kr:#x}")
    finally:
        iokit.IOServiceClose(connect)


def _simulate_macos():
    # Larger offsets + randomised pauses to look human
    dx = random.randint(30, 80)
    dy = random.randint(30, 80)
    wait = random.randint(300, 700)   # ms between moves

    # METHOD 1: IOHIDPostEvent (kernel-level — resets HIDIdleTime)
    try:
        _post_hid_event(dx, dy)
        time.sleep(0.05)
        _post_hid_event(-dx, -dy)
        _log.debug("IOHIDPost: moved +%d,+%d and back", dx, dy)
    except Exception as e:
        _log.warning("IOHIDPost: FAILED - %s", e)

    # METHOD 2: cliclick with pauses (Teams monitors CGEvent mouse moves)
    # w: = wait in ms between actions, larger moves, realistic timing
    if _cliclick:
        try:
            result = subprocess.run(
                [_cliclick,
                 f"m:+{dx},+0",   f"w:{wait}",
                 f"m:+0,+{dy}",   f"w:{wait}",
                 f"m:-{dx},+0",   f"w:{wait}",
                 f"m:+0,-{dy}",   f"w:{wait}",
                 "kp:f15"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                _log.debug("cliclick: moved +%d,+%d (wait %dms) and f15", dx, dy, wait)
            else:
                _log.warning("cliclick: exit code %d stderr: %s", result.returncode, result.stderr.strip())
        except Exception as e:
            _log.debug("cliclick: FAILED - %s", e)

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

    # Check 1: CGEventSource (user-space idle counter)
    cg_idle = None
    try:
        from Quartz import (
            CGEventSourceSecondsSinceLastEventType,
            kCGEventSourceStateCombinedSessionState,
            kCGAnyInputEventType,
        )
        cg_idle = CGEventSourceSecondsSinceLastEventType(
            kCGEventSourceStateCombinedSessionState, kCGAnyInputEventType
        )
    except Exception:
        pass

    # Check 2: IOKit HIDIdleTime (kernel-level idle counter — what Teams reads)
    hid_idle = None
    try:
        result = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem", "-d", "4"],
            capture_output=True, text=True, timeout=3,
        )
        for line in result.stdout.split("\n"):
            if "HIDIdleTime" in line and "=" in line:
                ns = int(line.split("=")[-1].strip())
                hid_idle = ns / 1_000_000_000
                break
    except Exception:
        pass

    parts = []
    if cg_idle is not None:
        parts.append(f"CGEvent={cg_idle:.1f}s")
    if hid_idle is not None:
        parts.append(f"HIDIdle={hid_idle:.1f}s")

    landed = (hid_idle is not None and hid_idle < 2.0) or (cg_idle is not None and cg_idle < 2.0)
    if landed:
        _log.debug("VERIFY: %s — events ARE landing", " ".join(parts))
    else:
        _log.warning("VERIFY: %s — events NOT landing!", " ".join(parts))


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
