import pytest
import spotipy

import options
from spotiafk import config
from spotiafk import session as session_module
from spotiafk.session import Session


class FakeClient:
    def __init__(self):
        self.transfers = []
        self.queued = []
        self.skips = 0
        self.gone_ids = set()

    def transfer_playback(self, device_id, force):
        if device_id in self.gone_ids:
            raise spotipy.SpotifyException(http_status=404, msg="Device not found")
        self.transfers.append(device_id)

    def add_to_queue(self, uri):
        self.queued.append(uri)

    def next_track(self):
        self.skips += 1


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr(session_module, "get_server_ids", lambda client: ["srv-1", "srv-2"])
    monkeypatch.setattr(session_module, "notify", lambda level, message: None)
    monkeypatch.setattr(options, "TIME_BETWEEN_CHECKS", 0, raising=False)
    return Session(FakeClient())


def test_tick_counts_free_checks(monkeypatch, session):
    monkeypatch.setattr(session_module, "account_is_free", lambda client: True)
    monkeypatch.setattr(Session, "play_round", lambda self: None)
    for _ in range(config.CHECKS_BEFORE_PLAYING):
        session.tick()
    assert session.playing


def test_tick_resets_counter_when_user_is_active(monkeypatch, session):
    session.success_checks = 3
    session.playing = True
    monkeypatch.setattr(session_module, "account_is_free", lambda client: False)
    session.tick()
    assert session.success_checks == 0
    assert not session.playing


def test_stop_playing_is_a_noop_when_not_playing(session):
    sent = []
    session.notify_once = lambda message: sent.append(message)
    session.stop_playing()
    assert sent == []


def test_notify_once_deduplicates(monkeypatch, session):
    sent = []
    monkeypatch.setattr(session_module, "notify", lambda level, message: sent.append(message))
    session.notify_once("hello")
    session.notify_once("hello")
    session.notify_once("bye")
    assert sent == ["hello", "bye"]


def test_transfer_falls_back_to_next_server(session):
    session.client.gone_ids = {"srv-1"}
    session.transfer_to_server()
    assert session.client.transfers == ["srv-2"]


def test_transfer_raises_when_no_server_accepts(monkeypatch, session):
    session.client.gone_ids = {"srv-1", "srv-2"}
    with pytest.raises(RuntimeError):
        session.transfer_to_server()


def test_wait_out_track_credits_playtime(monkeypatch, session, tmp_path):
    monkeypatch.setattr(config, "TIMELOG_PATH", str(tmp_path / "time.txt"))
    monkeypatch.setattr(config, "PLAY_CHECK_SLICE", 0.01)
    monkeypatch.setattr(options, "SKIP_SONGS", False)
    monkeypatch.setattr(session_module, "account_is_free", lambda client: True)

    from spotiafk import timelog

    took_over = session.wait_out_track(duration=0.03)
    assert not took_over
    assert timelog.read_total() > 0


def test_wait_out_track_stops_when_user_takes_over(monkeypatch, session, tmp_path):
    monkeypatch.setattr(config, "TIMELOG_PATH", str(tmp_path / "time.txt"))
    monkeypatch.setattr(config, "PLAY_CHECK_SLICE", 0.01)
    monkeypatch.setattr(options, "SKIP_SONGS", False)
    monkeypatch.setattr(session_module, "account_is_free", lambda client: False)

    assert session.wait_out_track(duration=5)
