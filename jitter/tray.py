"""System tray setup and menu."""

import threading
import pystray
from pystray import MenuItem

from jitter import icons, heartbeat, idle


def _format_idle() -> str:
    secs = int(idle.idle_seconds())
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    return f"{mins // 60}h {mins % 60}m"


def _toggle(icon: pystray.Icon, _item: MenuItem):
    if heartbeat.is_running():
        heartbeat.stop()
        icon.icon = icons.paused_icon()
    else:
        heartbeat.start()
        icon.icon = icons.active_icon()


def _quit(icon: pystray.Icon, _item: MenuItem):
    heartbeat.stop()
    icon.stop()


def _status_text(_item: MenuItem) -> str:
    if not heartbeat.is_running():
        return "○ Paused"
    if heartbeat.is_skipping():
        return f"⏸ AFK skip (idle {_format_idle()})"
    return f"● Active (idle {_format_idle()})"


def _update_icon(icon: pystray.Icon):
    if not heartbeat.is_running():
        icon.icon = icons.paused_icon()
    elif heartbeat.is_skipping():
        icon.icon = icons.skipping_icon()
    else:
        icon.icon = icons.active_icon()


def _refresh_loop(icon: pystray.Icon):
    try:
        _update_icon(icon)
        icon.update_menu()
    except Exception:
        pass
    timer = threading.Timer(10, _refresh_loop, args=[icon])
    timer.daemon = True
    timer.start()


def _on_setup(icon: pystray.Icon):
    icon.visible = True
    idle.start()
    heartbeat.start()
    _refresh_loop(icon)


def run():
    icon = pystray.Icon(
        name="Jitter",
        icon=icons.active_icon(),
        title="Jitter",
        menu=pystray.Menu(
            MenuItem(_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            MenuItem(
                lambda _: "Pause" if heartbeat.is_running() else "Resume",
                _toggle,
            ),
            MenuItem("Quit", _quit),
        ),
    )
    icon.run(setup=_on_setup)
