# Changelog

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
