"""A heartbeat file the run loop writes and 'spotiafk status' reads.

No daemon IPC: status works by reading this JSON file and judging its age.
"""

import datetime
import json
import os

STATUS_FILE = "status.json"


def _path(state_dir: str) -> str:
    return os.path.join(state_dir, STATUS_FILE)


def write(state_dir: str, state: str, **fields) -> None:
    os.makedirs(state_dir, exist_ok=True)
    payload = {
        "state": state,
        "pid": os.getpid(),
        "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        **fields,
    }
    tmp = _path(state_dir) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, _path(state_dir))


def read(state_dir: str) -> dict | None:
    try:
        with open(_path(state_dir)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def age_seconds(status: dict) -> float | None:
    try:
        updated = datetime.datetime.fromisoformat(status["updated"])
    except (KeyError, ValueError):
        return None
    return (datetime.datetime.now() - updated).total_seconds()
