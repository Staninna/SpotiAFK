"""Legacy entry point kept for compatibility: same as 'spotiafk run'."""

import sys

from spotiafk.cli import main

if __name__ == "__main__":
    sys.exit(main(["run"]))
