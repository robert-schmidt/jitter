"""Jitter — keep Teams awake from the system tray."""

import logging
import os

_log_path = os.path.join(os.path.expanduser("~"), ".jitter", "debug.log")
os.makedirs(os.path.dirname(_log_path), exist_ok=True)
_log = logging.getLogger("jitter.main")
_log.setLevel(logging.DEBUG)
_fh = logging.FileHandler(_log_path, mode="a")
_fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
_log.addHandler(_fh)


def main():
    _log.info("Jitter starting...")

    try:
        from jitter.permissions import check_all
        check_all()
    except Exception as e:
        _log.error("Permission check failed: %s", e)

    try:
        from jitter.tray import run
        _log.info("Loading tray icon...")
        run()
    except Exception as e:
        _log.error("Tray failed: %s", e)
        raise


if __name__ == "__main__":
    main()
