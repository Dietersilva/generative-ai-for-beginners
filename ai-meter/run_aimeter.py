"""Entry point used by the Windows build (PyInstaller)."""
import sys

from aimeter.app import main

if __name__ == "__main__":
    sys.exit(main())
