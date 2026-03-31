"""Jitter — keep Teams awake from the system tray."""

import sys
from jitter.permissions import check_all
from jitter.tray import run


def main():
    if not check_all():
        sys.exit(1)
    run()


if __name__ == "__main__":
    main()
