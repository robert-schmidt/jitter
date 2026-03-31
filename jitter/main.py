"""Jitter — keep Teams awake from the system tray."""

from jitter.permissions import check_all
from jitter.tray import run


def main():
    check_all()
    run()


if __name__ == "__main__":
    main()
