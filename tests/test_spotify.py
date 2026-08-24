import options
from spotiafk.spotify import get_tracks


def make_track(name, uri="spotify:track:x", duration=1000):
    return {"name": name, "uri": uri, "duration_ms": duration}


class FakeClient:
    """Serves one playlist page in either the old or the new API shape."""

    def __init__(self, entries):
        self.entries = entries

    def current_user_playlists(self):
        return {"items": [{"name": options.PLAYLIST_NAME, "id": "pl-1"}], "next": None}

    def playlist_items(self, playlist_id):
        return {"items": self.entries, "next": None}


def test_new_api_shape_uses_item_key(monkeypatch):
    monkeypatch.setattr(options, "RANDOM_ORDER_TRACKS", False)
    client = FakeClient([{"item": make_track("a")}, {"item": make_track("b")}])
    assert [name for _, _, name in get_tracks(client)] == ["a", "b"]


def test_old_api_shape_uses_track_key(monkeypatch):
    monkeypatch.setattr(options, "RANDOM_ORDER_TRACKS", False)
    client = FakeClient([{"track": make_track("a")}])
    assert [name for _, _, name in get_tracks(client)] == ["a"]


def test_unplayable_entries_are_skipped(monkeypatch):
    monkeypatch.setattr(options, "RANDOM_ORDER_TRACKS", False)
    client = FakeClient(
        [
            {"item": None},  # removed track
            {"item": {"name": "no-duration", "uri": "spotify:track:y", "duration_ms": None}},
            {"item": make_track("keep")},
        ]
    )
    assert [name for _, _, name in get_tracks(client)] == ["keep"]
