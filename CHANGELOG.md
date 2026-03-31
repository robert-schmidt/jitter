# Changelog

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
