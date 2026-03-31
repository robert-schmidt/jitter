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

## How It Works

- Every **3 minutes** (configurable), Jitter sends an **F15 keypress** — a key that exists on no modern keyboard and has zero side effects on any OS. It's enough to reset idle timers without interfering with anything.
- After **60 minutes** of no real keyboard input (configurable), Jitter inserts a **10-minute skip** (configurable) before the next keypress to look more like natural human activity. After the skip, the idle counter resets and the cycle repeats.
- **Schedule support** — set active hours (default 09:00–18:00, weekdays) so Jitter only runs during work time. Outside the schedule, it sleeps and the icon turns gray.
- Everything runs in the **system tray** — no windows, no dock icon, no distractions.
- **Screensavers and display sleep** are generally not affected — simulated F15 keypresses via `pynput` don't reset macOS's HIDIdleTime, so your screen will still lock and sleep normally.

### Tray Menu

| Icon | State | Meaning |
|------|-------|---------|
| 🟢 | Active | Sending F15 — shows countdown to next pulse |
| 🟡 | AFK Skip | Waiting after long idle — shows countdown |
| ⚪ | Outside schedule | Sleeping until next active window |
| ⚪ | Paused | Manually paused |

Click the tray icon for **Pause/Resume**, **Settings**, **About** (with GitHub link), and **Quit** (with confirmation).

### Settings

Open **Settings** from the tray menu to configure:

- **Schedule** — enable/disable, start and end time, active days of the week
- **Pulse interval** — how often to send F15 (default: 3 minutes)
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

### One-liner (macOS)

Clone, build, and install to Applications in one shot:

```bash
git clone https://github.com/robert-schmidt/jitter.git /tmp/jitter && cd /tmp/jitter && pip install -r requirements.txt && make build-mac && cp -r dist/Jitter.app /Applications/ && open /Applications/Jitter.app
```

## Platform Setup

### macOS

Jitter requires two system permissions to function. On every launch, the app checks whether it can simulate keypresses and listen for keyboard input. If either permission is missing, it tells you exactly which one(s) to grant and opens System Settings. If both are already granted, no dialog appears.

You must grant **both** of the following in **System Settings → Privacy & Security**:

1. **Accessibility** — required for simulating the F15 keypress (`pynput` keyboard controller)
2. **Input Monitoring** — required for detecting real keyboard activity to track idle time (`pynput` keyboard listener)

To grant permissions:
1. Open **System Settings → Privacy & Security → Accessibility**
2. Click the **+** button, navigate to `Jitter.app` (or your terminal app if running from source), and add it
3. Repeat for **Privacy & Security → Input Monitoring**
4. Relaunch Jitter

> **Note:** If running from source (not the `.app` bundle), you need to grant these permissions to your **terminal app** (Terminal, iTerm2, etc.) instead.

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
│   ├── main.py          — entry point, permission check
│   ├── tray.py          — system tray setup and menu
│   ├── heartbeat.py     — F15 timer loop with AFK skip logic
│   ├── idle.py          — monitors real keyboard input
│   ├── icons.py         — generates tray icons (green/amber/gray circles)
│   ├── dialogs.py       — About window (with GitHub link) and quit confirmation
│   ├── permissions.py   — macOS permission checks (tests actual keypress/listener)
│   ├── config.py        — persistent settings (~/.jitter/config.json)
│   └── settings_ui.py   — Settings window with schedule and timing controls
├── run.py               — PyInstaller entry point (outside package)
├── Makefile             — build targets for macOS and Windows
├── requirements.txt
└── README.md
```

## About

Jitter was built out of frustration with workplace tools that equate "online" with "working." It's about 200 lines of Python, has no dependencies beyond the tray and input libraries, needs no config files, and does exactly one thing well.

It doesn't touch your network, doesn't phone home, doesn't collect data. It lives in your menu bar, presses a ghost key, and minds its own business — the way your employer should.

**Source:** [github.com/robert-schmidt/jitter](https://github.com/robert-schmidt/jitter)

## Support

If Jitter saved you from one more "why were you Away?" conversation, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-yellow?style=for-the-badge)](https://buymeacoffee.com/robbschmidt)

## License

Do whatever you want with this. If your workplace makes you feel like you need it, you deserve to have it.
