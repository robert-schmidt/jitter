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

- Every **3 minutes**, Jitter sends an **F15 keypress** — a key that exists on no modern keyboard and has zero side effects on any OS. It's enough to reset idle timers without interfering with anything.
- After **60 minutes** of no real keyboard input (you're truly AFK), Jitter inserts a **10-minute skip** before the next keypress to look more like natural human activity. After the skip, the idle counter resets and the cycle repeats.
- Everything runs in the **system tray** — no windows, no dock icon, no distractions.

### Tray Menu

| Icon | State | Meaning |
|------|-------|---------|
| 🟢 | Active | Sending F15 every 3 min |
| 🟡 | AFK Skip | Waiting 10 min (idle >60 min) |
| ⚪ | Paused | Manually paused |

Click the tray icon for **Pause/Resume** and **Quit**.

## Install & Run

Requires Python 3.11+.

```bash
git clone https://github.com/robert-schmidt/jitter.git
cd jitter
pip install -r requirements.txt
python -m jitter.main
```

## Build Standalone Binaries

### macOS (.app)

```bash
make build-mac
```

Output: `dist/Jitter.app`

On first launch, macOS will ask for **Accessibility** and **Input Monitoring** permissions (System Settings → Privacy & Security). This is required for simulating and monitoring keypresses.

### Windows (.exe)

```bash
make build-win
```

Output: `dist/Jitter.exe`

No special permissions needed on Windows.

### Pre-built Binaries

Check the [Releases](https://github.com/robert-schmidt/jitter/releases) page for ready-to-run builds for macOS (Apple Silicon) and Windows.

## Project Structure

```
jitter/
├── jitter/
│   ├── main.py        — entry point
│   ├── tray.py        — system tray setup and menu
│   ├── heartbeat.py   — F15 timer loop with AFK skip logic
│   ├── idle.py        — monitors real keyboard input
│   └── icons.py       — generates tray icons (green/amber/gray circles)
├── Makefile           — build targets for macOS and Windows
├── requirements.txt
└── README.md
```

## About

Jitter was built out of frustration with workplace tools that equate "online" with "working." It's less than 200 lines of Python, has no dependencies beyond the tray and input libraries, needs no config files, and does exactly one thing well.

It doesn't touch your network, doesn't phone home, doesn't collect data. It lives in your menu bar, presses a ghost key, and minds its own business — the way your employer should.

**Source:** [github.com/robert-schmidt/jitter](https://github.com/robert-schmidt/jitter)

## Support

If Jitter saved you from one more "why were you Away?" conversation, consider buying me a coffee:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-yellow?style=for-the-badge)](https://buymeacoffee.com/robbschmidt)

## License

Do whatever you want with this. If your workplace makes you feel like you need it, you deserve to have it.
