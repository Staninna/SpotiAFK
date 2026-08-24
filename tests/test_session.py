import pytest
import spotipy

from spotiafk import session as session_module
from spotiafk.config import Config
from spotiafk.session import Session


class FakeClient:
    def __init__(self):
        self.transfers = []
        self.gone_ids = set()

    def transfer_playback(self, device_id, force):
        if device_id in self.gone_ids:
            raise spotipy.SpotifyException(http_status=404, msg="Device not found")
        self.transfers.append(device_id)


@pytest.fixture
def session(monkeypatch, tmp_path):
    cfg = Config(
        playlist="AFK",
        play_on=("srv-1", "srv-2"),
        client_id="id",
        client_secret="sec",
        check_interval=0,
        skip_after=None,
        state_dir=str(tmp_path),
    )
    monkeypatch.setattr(session_module, "get_server_ids", lambda client, cfg: ["srv-1", "srv-2"])
    monkeypatch.setattr(session_module, "notify", lambda cfg, level, message: None)
    return Session(FakeClient(), cfg)


def test_tick_counts_free_checks(monkeypatch, session):
    monkeypatch.setattr(session_module, "account_is_free", lambda client, cfg: True)
    monkeypatch.setattr(Session, "play_round", lambda self: None)
    for _ in range(session.cfg.idle_checks):
        session.tick()
    assert session.playing


def test_tick_resets_counter_when_user_is_active(monkeypatch, session):
    session.success_checks = 3
    session.playing = True
    monkeypatch.setattr(session_module, "account_is_free", lambda client, cfg: False)
    session.tick()
    assert session.success_checks == 0
    assert not session.playing


def test_notify_once_deduplicates(monkeypatch, session):
    sent = []
    monkeypatch.setattr(session_module, "notify", lambda cfg, level, message: sent.append(message))
    session.notify_once("hello")
    session.notify_once("hello")
    session.notify_once("bye")
    assert sent == ["hello", "bye"]


def test_transfer_falls_back_to_next_server(session):
    session.client.gone_ids = {"srv-1"}
    session.transfer_to_server()
    assert session.client.transfers == ["srv-2"]


def test_transfer_raises_when_no_server_accepts(session):
    session.client.gone_ids = {"srv-1", "srv-2"}
    with pytest.raises(RuntimeError):
        session.transfer_to_server()


def test_wait_out_track_credits_playtime(monkeypatch, session):
    monkeypatch.setattr(session_module, "PLAY_CHECK_SLICE", 0.01)
    monkeypatch.setattr(session_module, "account_is_free", lambda client, cfg: True)
    took_over = session.wait_out_track(0.03, "song")
    assert not took_over
    from spotiafk import stats

    result = stats.summary(session.cfg.state_dir)
    assert result.total_seconds > 0
    assert result.tracks == 1


def test_wait_out_track_stops_when_user_takes_over(monkeypatch, session):
    monkeypatch.setattr(session_module, "PLAY_CHECK_SLICE", 0.01)
    monkeypatch.setattr(session_module, "account_is_free", lambda client, cfg: False)
    assert session.wait_out_track(5, "song")
