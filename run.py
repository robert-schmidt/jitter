"""PyInstaller entry point — must be outside the jitter package."""

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from jitter.main import main
    main()
