"""Crash-safe persistence of the total played time (seconds) in a text file."""

import os

from spotiafk import config


def read_total() -> float:
    try:
        with open(config.TIMELOG_PATH) as f:
            return float(f.readline() or 0.0)
    except (OSError, ValueError):
        return 0.0


def write_total(total: float) -> None:
    tmp_path = config.TIMELOG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(str(max(0.0, total)))
    os.replace(tmp_path, config.TIMELOG_PATH)


def add(seconds: float) -> None:
    write_total(read_total() + max(0.0, seconds))
