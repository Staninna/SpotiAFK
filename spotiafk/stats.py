"""Play history: an append-only JSONL event log in the state dir.

Each completed (or interrupted) track append one event, so totals are
crash-safe and can be broken down by day. A legacy time.txt total is
imported once as a baseline event.
"""

import dataclasses
import datetime
import json
import os

from spotiafk.config import BASE_DIR

EVENTS_FILE = "events.jsonl"


def _events_path(state_dir: str) -> str:
    return os.path.join(state_dir, EVENTS_FILE)


def import_legacy(state_dir: str) -> None:
    """One-time import of the old time.txt total as a baseline event."""
    if os.path.isfile(_events_path(state_dir)):
        return
    legacy = os.path.join(BASE_DIR, "time.txt")
    try:
        with open(legacy) as f:
            total = float(f.readline() or 0.0)
    except (OSError, ValueError):
        return
    if total > 0:
        add(state_dir, total, track=None, legacy=True)


def add(state_dir: str, seconds: float, track: str | None = None, legacy: bool = False) -> None:
    if seconds <= 0:
        return
    os.makedirs(state_dir, exist_ok=True)
    event = {"t": datetime.datetime.now().isoformat(timespec="seconds"), "s": round(seconds, 3)}
    if track:
        event["track"] = track
    if legacy:
        event["legacy"] = True
    with open(_events_path(state_dir), "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


@dataclasses.dataclass(frozen=True)
class Stats:
    total_seconds: float
    tracks: int  # events with a known track (excludes the legacy baseline)
    by_day: dict  # ISO date -> seconds, within the queried window

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


def summary(state_dir: str, since: datetime.datetime | None = None) -> Stats:
    total = 0.0
    tracks = 0
    by_day: dict = {}
    try:
        with open(_events_path(state_dir)) as f:
            lines = f.readlines()
    except OSError:
        lines = []
    for line in lines:
        try:
            event = json.loads(line)
            when = datetime.datetime.fromisoformat(event["t"])
            seconds = float(event["s"])
        except (ValueError, KeyError):
            continue  # ignore a torn or corrupt line
        if since and when < since:
            continue
        total += seconds
        if "track" in event:
            tracks += 1
        if not event.get("legacy"):
            day = when.date().isoformat()
            by_day[day] = by_day.get(day, 0.0) + seconds
    return Stats(total_seconds=total, tracks=tracks, by_day=by_day)


def format_duration(seconds: float) -> str:
    minutes, _ = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"
