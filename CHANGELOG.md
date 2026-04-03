# Changelog

## v1.3.4 — 2026-04-03

### Fixed
- **F15 "~" appearing in terminal** — cliclick's F15 keypress was landing in Terminal (which interprets it as escape sequence `\e[28~`). Now verifies Teams is actually the frontmost app before sending any input.
- **Permission dialog never showing** — was checking if the `cliclick` binary had Accessibility (it has its own entry from Homebrew), not whether Jitter.app itself had it. Now checks `AXIsProcessTrusted()` for the running process.
- **Dialog blocked on corporate Macs** — permission dialog used `osascript display dialog` which needs Automation permission (blocked by MDM). Now uses tkinter which needs no permissions.
- **No permission errors in logs** — now logs a warning on launch when Accessibility is not granted, explaining which methods won't work.
- **Screen stays on while pulsing** — `caffeinate -u -d -i` prevents display sleep and screensaver. Killed immediately when entering AFK skip or going outside schedule.
- **VERIFY false alarm** — HIDIdle threshold raised from 2s to 5s to account for cliclick wait time.

### Changed
- **Mouse/key input sent while Teams is focused** — activates Teams first, sends cliclick moves + F15 while Teams is the active app, then switches back. Teams registers this as real user interaction in its window.

## v1.3.3 — 2026-04-03

**Enterprise Mac compatibility — complete rewrite of activity simulation.**

The previous methods (osascript, CGEvent, pynput) stopped working on enterprise/corporate Macs where security software blocks synthetic events from resetting the system idle timer. This release replaces all of them with methods that work regardless of enterprise security policies.

### Fixed
- **`cliclick kp:shift` was invalid** — cliclick doesn't support modifier keys with `kp:`, causing silent failure (exit code 1) every pulse. The entire cliclick command — including mouse moves — was aborting. Replaced with `kp:f15`.
- **Events not resetting macOS idle timer** — `CGEventPost` and `CGWarpMouseCursorPosition` don't reset `HIDIdleTime` on newer macOS. Added `IOHIDPostEvent` which posts `NX_MOUSEMOVED` directly to the IOKit HID kernel layer.
- **Enterprise security blocking CGEventSource reset** — on managed Macs, no synthetic event method resets `CGEventSourceSecondsSinceLastEventType` (which Teams reads). Added `IOPMAssertionDeclareUserActivity` and direct Teams window activation via `NSRunningApplication` to bypass the idle timer entirely.
- **Permission dialog showing when already granted** — now tests if cliclick can actually send events before falling back to `AXIsProcessTrusted()`.

### Changed
- **4 new activity methods** replacing the old 3:
  1. `IOHIDPostEvent` — kernel-level NX_MOUSEMOVED (resets HIDIdleTime)
  2. `cliclick` — mouse moves in square pattern (30-80px, 300-700ms pauses) + F15 keypress
  3. `IOPMAssertionDeclareUserActivity` — Apple's power management API to declare user active
  4. Teams window activation — briefly activates Teams via NSRunningApplication
- **Removed** osascript/System Events method (blocked by MDM on enterprise Macs)
- **Removed** Quartz CGEvent method (doesn't reset idle on newer macOS)
- **Removed** pynput (crashes on macOS Tahoe)
- **Better diagnostics** — VERIFY now logs both `CGEventSource` and `HIDIdleTime` (kernel) counters
- Mouse movements increased from 5-20px to 30-80px with realistic pauses between steps
- Debug logging restored (was accidentally set to WARNING in v1.3.2)

## v1.3.0 — 2026-04-01

- **Custom app icon** — green dot with pulse rings on dark background
- **No dock icon** — Jitter runs entirely in the menu bar (LSUIElement)
- **pynput removed from macOS build** — was crashing on macOS Tahoe (EXC_BREAKPOINT). macOS now uses cliclick, osascript, and Quartz CGEvent only
- **Auto-install cliclick** — if cliclick isn't found and Homebrew is available, Jitter installs it automatically on first run
- Updated README with current project structure and line count

## v1.2.0 — 2026-03-31

**This release fixes the core issue: Teams should actually stay active now.**

- **Schedule OFF by default** — the schedule (09:00–18:00) was silently blocking pulses outside work hours. Schedule is now disabled by default. Enable it in Settings if you want it.
- **osascript + System Events as primary method** — sends keystrokes via macOS System Events process, which has its own Accessibility context. Works even if the app's own permissions are revoked by MDM.
- **Quartz CGEvent as secondary** — direct mouse nudge + shift key at the HID event tap level.
- **pynput as tertiary fallback** — F15 keypress for maximum coverage.
- **caffeinate -u** — continues to reset IOKit HIDIdleTime.
- **Idle detection fallback** — if Input Monitoring isn't available, falls back to querying `CGEventSource` idle time directly (no permissions needed).
- **Pulse interval reduced to 2 minutes** (was 3) for better reliability with aggressive idle detection.
- **Non-blocking permission check** — app always launches, shows a soft hint if permissions are missing.

**If upgrading:** Delete `~/.jitter/config.json` to get the new defaults, or toggle schedule off in Settings.

## v1.1.0 — 2026-03-31

- **Fix: Teams actually stays active now** — added `caffeinate -u` alongside F15 keypresses on macOS. F15 via pynput doesn't reset HIDIdleTime (which Teams checks), but `caffeinate -u` does. Both are now used together.
- **Launch at login** — optional setting to start Jitter automatically on login (default: off)
  - macOS: creates a LaunchAgent in `~/Library/LaunchAgents/`
  - Windows: adds a registry key in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- Settings dialog now has a **General** section to toggle launch at login
- Added CHANGELOG.md

## v1.0.0 — 2026-03-31

Initial release.

- F15 keypress every 3 minutes to prevent Teams "Away" status
- AFK detection: 10-minute skip after 60 minutes of no real keyboard input, then idle counter resets
- System tray with green (active), amber (AFK skip), gray (paused/outside schedule) icons
- Pause/Resume toggle
- Schedule support: configurable active hours and days (default 09:00–18:00, Mon–Fri)
- Settings via native macOS dialogs (osascript): schedule, pulse interval, AFK threshold, AFK skip
- About dialog with GitHub link
- Quit confirmation
- Permission check on first launch (Accessibility + Input Monitoring on macOS)
- PyInstaller builds for macOS (.app) and Windows (.exe)
- Tested on macOS Tahoe 26.3.1 (a) (25D771280a)
