# Jitter

A tiny system tray app that keeps Microsoft Teams (and other apps) from marking you as "Away."

[![GitHub](https://img.shields.io/github/v/release/robert-schmidt/jitter)](https://github.com/robert-schmidt/jitter/releases)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow)](https://buymeacoffee.com/robbschmidt)

## Why This Exists

Modern workplace surveillance has gone too far.

Your employer hired you to do a job — not to prove every three minutes that your fingers are touching a keyboard. "Away" status has become a proxy for laziness in the eyes of managers who confuse presence with productivity. People step away to think, to sketch on paper, to have a conversation with a colleague, to take a walk that unsticks a hard problem — and they come back to a passive-aggressive "I noticed you were Away for 20 minutes" from someone who spent that same 20 minutes refreshing a dashboard.

Activity monitoring doesn't measure work. It measures compliance. It tells you nothing about whether someone shipped a feature, fixed a bug, helped a teammate, or had the insight that saved the project. What it does measure, with great precision, is how little a company trusts the people it chose to hire.

If your organization tracks green dots instead of outcomes, the problem isn't the employee who went to get coffee. The problem is a culture that treats adults like suspects.

Jitter is a small, peaceful act of resistance. It presses a key that does nothing, so you can do the things that matter.

### Why not just Amphetamine?

Amphetamine is a great app, but it stopped working on my Mac one day and I have no idea why. 🤷 So I built this.

## How It Works

Every **2 minutes** (configurable), Jitter fires multiple redundant methods to keep you "Available." Each method targets a different layer of macOS idle detection, so at least one will work regardless of your system's security configuration.

### Activity methods

| # | Method | What it does | Permission |
|---|--------|-------------|------------|
| 1 | **`IOHIDPostEvent`** | Posts a `NX_MOUSEMOVED` event directly to the IOKit HID kernel layer, resetting the real `HIDIdleTime` counter that many apps check. | Accessibility |
| 2 | **`cliclick`** | Native C binary. Moves the mouse in a square pattern (30–80 px per axis, 300–700 ms random pauses between steps) then presses the invisible F15 key. Generates realistic CGEvent mouse-move events. Installed via `brew install cliclick`. | Accessibility |
| 3 | **`IOPMAssertionDeclareUserActivity`** | Apple's power management API — tells macOS the user is active, equivalent to pressing a key. Resets the system idle timer and prevents display sleep. | **None** |
| 4 | **Teams window activation** | Finds the running Microsoft Teams process and briefly activates its window via `NSRunningApplication`, then immediately switches back to your previous app (~150 ms). Teams receives a system activation event and resets its internal idle state. Only runs if Teams is open. | **None** |
| 5 | **`caffeinate -u`** | Prevents system sleep for the duration of the pulse interval. | **None** |

Methods 3–5 require **no permissions at all** and work on any Mac, including enterprise/corporate machines with strict security policies. Methods 1–2 provide deeper idle timer resets when Accessibility permission is available.

### AFK behaviour

- After **60 minutes** of no real keyboard/mouse input (configurable), Jitter inserts a **10-minute skip** before the next pulse to mimic natural human activity — nobody is active for 8 hours straight without a break. After the skip, pulsing resumes normally.
- On enterprise Macs where synthetic events don't reset the system idle counter, Jitter uses an internal timer to track the skip so it doesn't get stuck in a skip loop.

### Other features

- **Schedule support** — set active hours and days so Jitter only runs during work time (disabled by default). Outside the schedule, it sleeps and the icon turns gray.
- **Launch at login** — toggle from the tray menu (default: off).
- Everything runs in the **system tray** — no windows, no dock icon, no distractions.
- **Debug log** at `~/.jitter/debug.log` — every pulse logs which methods succeeded, plus verification of both `CGEventSource` (user-space) and `HIDIdleTime` (kernel) idle counters.

> **Tip:** Pause Jitter while you're actively working — the mouse movement can interfere with precise cursor work (design tools, spreadsheets, etc.). Use the tray menu to quickly pause and resume.

> **Note on screensavers:** While actively pulsing, Jitter will prevent display sleep and screensaver activation. Outside the schedule or when paused, the system behaves normally.

### Tray Menu

| Icon | State | Meaning |
|------|-------|---------|
| 🟢 | Active | Pulsing — shows countdown to next pulse |
| 🟡 | AFK Skip | Waiting after long idle — shows countdown |
| ⚪ | Outside schedule | Sleeping until next active window |
| ⚪ | Paused | Manually paused |

Click the tray icon for **Pause/Resume**, **Settings**, **About** (with GitHub link), and **Quit** (with confirmation).

### Settings

Open **Settings** from the tray menu to configure:

- **Schedule** — enable/disable, start and end time, active days of the week
- **Pulse interval** — how often to send activity pulses (default: 2 minutes)
- **AFK threshold** — how long without real input before triggering a skip (default: 60 minutes)
- **AFK skip duration** — how long to wait during a skip (default: 10 minutes)

Settings are saved to `~/.jitter/config.json` and persist across restarts.

## Install & Run

Requires Python 3.11+ and Git.

```bash
git clone https://github.com/robert-schmidt/jitter.git
cd jitter
pip install -r requirements.txt
python -m jitter.main
```

**Optional:** install `cliclick` for mouse movement simulation (method 2):
```bash
brew install cliclick
```

> **Note:** `cliclick` is a native macOS tool for simulating mouse/keyboard events. It enables method 2 (mouse moves + F15 keypress) but is not required — Jitter works without it using methods 3–5.

### One-liner (macOS)

Clone, build, and install to Applications in one shot:

```bash
git clone https://github.com/robert-schmidt/jitter.git /tmp/jitter && cd /tmp/jitter && pip install -r requirements.txt && make build-mac && cp -r dist/Jitter.app /Applications/ && open /Applications/Jitter.app
```

## Platform Setup

### macOS

**Jitter works without any permissions** — methods 3–5 (DeclareUserActivity, Teams activation, caffeinate) need no grants at all and are enough to keep Teams active on most systems, including enterprise Macs.

For the full set of methods, grant the following in **System Settings → Privacy & Security**:

| Permission | Required? | What it enables |
|-----------|-----------|----------------|
| **Accessibility** | Recommended | Enables `IOHIDPostEvent` (kernel idle reset) and `cliclick` (mouse movement simulation). Without this, methods 1–2 will log "FAILED" and only methods 3–5 will run. |
| **Automation → System Events** | Not needed | Previously used for osascript keystroke sending. Removed in v1.3.3 — typically blocked by MDM on enterprise Macs anyway. |

To grant Accessibility:
1. Open **System Settings → Privacy & Security → Accessibility**
2. Click **+**, navigate to `Jitter.app`, and add it
3. If `cliclick` is installed via Homebrew, also add `/opt/homebrew/bin/cliclick`
4. Relaunch Jitter

> **Note:** If running from source (not the `.app` bundle), grant permissions to your **terminal app** (Terminal, iTerm2, etc.) instead.

> **Tested on:** macOS Tahoe 26.3.1 (a) (25D771280a)

### Windows

No special permissions are required. Jitter works out of the box on Windows.

> **Note:** Windows builds have not been tested yet. If you run into issues, please [open an issue](https://github.com/robert-schmidt/jitter/issues).

## Build Standalone Binaries

### macOS (.app)

```bash
make build-mac
```

Output: `dist/Jitter.app` — move to Applications or run directly.

### Windows (.exe)

```bash
make build-win
```

Output: `dist/Jitter.exe` — run directly or place anywhere convenient.

### Pre-built Binaries

Check the [Releases](https://github.com/robert-schmidt/jitter/releases) page for ready-to-run builds.

## Project Structure

```
jitter/
├── jitter/
│   ├── main.py              — entry point, permission check
│   ├── tray.py              — system tray setup and menu
│   ├── heartbeat.py         — activity simulation (IOHIDPost, cliclick, Teams activation)
│   ├── idle.py              — idle detection via CGEventSource
│   ├── icons.py             — generates tray icons (green/amber/gray circles)
│   ├── dialogs.py           — About window and quit confirmation
│   ├── permissions.py       — macOS permission checks
│   ├── config.py            — persistent settings (~/.jitter/config.json)
│   ├── settings_native.py   — Settings dialogs (osascript on macOS)
│   ├── startup.py           — launch at login (LaunchAgent / registry)
│   └── settings_ui.py       — Settings window (tkinter, Windows fallback)
├── assets/                  — app icon source files
├── run.py                   — PyInstaller entry point
├── Makefile                 — build targets for macOS and Windows
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## About

Jitter was built out of frustration with workplace tools that equate "online" with "working." It's about 1,100 lines of Python, runs entirely in the menu bar (no dock icon), and does exactly one thing well.

It doesn't touch your network, doesn't phone home, doesn't collect data. It lives in your menu bar, simulates natural activity, and minds its own business — the way your employer should.

**Source:** [github.com/robert-schmidt/jitter](https://github.com/robert-schmidt/jitter)

## Support

If Jitter saved you from one more "why were you Away?" conversation, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-yellow?style=for-the-badge)](https://buymeacoffee.com/robbschmidt)

## License

Do whatever you want with this. If your workplace makes you feel like you need it, you deserve to have it.
