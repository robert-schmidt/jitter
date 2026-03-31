"""System tray setup and menu."""

import threading
import pystray
from pystray import MenuItem

from jitter import icons, heartbeat, idle, dialogs, config, settings_native, startup

_refresh_timer: threading.Timer | None = None


def _format_countdown() -> str:
    secs = heartbeat.seconds_until_next()
    m, s = divmod(secs, 60)
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _schedule_label() -> str:
    cfg = config.load()
    if not cfg["schedule_enabled"]:
        return "Schedule: off"
    days = cfg["schedule_days"]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if days == [0, 1, 2, 3, 4]:
        d = "weekdays"
    elif days == [0, 1, 2, 3, 4, 5, 6]:
        d = "every day"
    else:
        d = ", ".join(day_names[i] for i in days)
    return f"Schedule: {cfg['schedule_start']}–{cfg['schedule_end']} ({d})"


def _toggle(icon: pystray.Icon, _item: MenuItem):
    if heartbeat.is_running():
        heartbeat.stop()
        icon.icon = icons.paused_icon()
    else:
        heartbeat.start()
        icon.icon = icons.active_icon()


def _toggle_startup(icon: pystray.Icon, _item: MenuItem):
    startup.set_enabled(not startup.is_enabled())


def _open_settings(icon: pystray.Icon, _item: MenuItem):
    import threading
    t = threading.Thread(target=settings_native.show, daemon=True)
    t.start()


def _about(icon: pystray.Icon, _item: MenuItem):
    dialogs.show_about()


def _quit(icon: pystray.Icon, _item: MenuItem):
    global _refresh_timer
    if not dialogs.confirm_quit():
        return
    heartbeat.stop()
    if _refresh_timer is not None:
        _refresh_timer.cancel()
        _refresh_timer = None
    icon.stop()


def _status_text(_item: MenuItem) -> str:
    if not heartbeat.is_running():
        return "○ Paused"
    if heartbeat.is_outside_schedule():
        return "◑ Outside schedule — sleeping"
    if heartbeat.is_skipping():
        return f"⏸ AFK skip — next pulse in {_format_countdown()}"
    return f"● Active — next pulse in {_format_countdown()}"


# Track last icon state to avoid redundant reassignment
_last_state: str | None = None


def _update_icon(icon: pystray.Icon):
    global _last_state
    if not heartbeat.is_running():
        state = "paused"
    elif heartbeat.is_outside_schedule():
        state = "paused"
    elif heartbeat.is_skipping():
        state = "skipping"
    else:
        state = "active"

    if state != _last_state:
        _last_state = state
        icon.icon = {"active": icons.active_icon, "skipping": icons.skipping_icon, "paused": icons.paused_icon}[state]()


def _refresh_loop(icon: pystray.Icon):
    global _refresh_timer
    try:
        _update_icon(icon)
        icon.update_menu()
    except Exception:
        pass
    _refresh_timer = threading.Timer(10, _refresh_loop, args=[icon])
    _refresh_timer.daemon = True
    _refresh_timer.start()


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
            MenuItem(lambda _: _schedule_label(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            MenuItem(
                lambda _: "Pause" if heartbeat.is_running() else "Resume",
                _toggle,
            ),
            MenuItem("Settings", _open_settings),
            MenuItem(
                lambda _: "✓ Launch at Login" if startup.is_enabled() else "  Launch at Login",
                _toggle_startup,
            ),
            MenuItem("About", _about),
            pystray.Menu.SEPARATOR,
            MenuItem("Quit", _quit),
        ),
    )
    icon.run(setup=_on_setup)
