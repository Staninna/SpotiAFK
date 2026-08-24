import pytest

from spotiafk.config import Config, ConfigError


def write(tmp_path, text):
    path = tmp_path / "spotiafk.toml"
    path.write_text(text)
    return path


MINIMAL = """
playlist = "AFK"
play_on = ["pi"]
[spotify]
client_id = "id"
client_secret = "secret"
"""


def test_minimal_toml_with_defaults(tmp_path):
    cfg = Config.load(write(tmp_path, MINIMAL))
    assert cfg.playlist == "AFK"
    assert cfg.play_on == ("pi",)
    assert cfg.skip_after == 35.0
    assert cfg.shuffle is True
    assert cfg.idle_checks == 5
    assert cfg.telegram is None
    assert cfg.issues() == []


def test_skip_after_zero_means_full_tracks(tmp_path):
    cfg = Config.load(write(tmp_path, MINIMAL + "[playback]\nskip_after = 0\n"))
    assert cfg.skip_after is None


def test_telegram_section(tmp_path):
    cfg = Config.load(write(tmp_path, MINIMAL + '[telegram]\nbot_token = "t"\nchat_id = 5\n'))
    assert cfg.telegram.bot_token == "t"
    assert cfg.telegram.chat_id == "5"


def test_missing_config_raises_with_fix_hint(tmp_path):
    with pytest.raises(ConfigError, match="spotiafk setup"):
        Config.load(tmp_path / "nope.toml")


def test_invalid_toml_raises(tmp_path):
    with pytest.raises(ConfigError, match="not valid TOML"):
        Config.load(write(tmp_path, "playlist = ["))


def test_issues_name_each_problem():
    problems = Config().issues()
    assert any("client_id" in p for p in problems)
    assert any("playlist" in p for p in problems)
    assert any("play_on" in p for p in problems)


def test_skip_after_below_stream_threshold_is_an_issue(tmp_path):
    cfg = Config.load(write(tmp_path, MINIMAL + "[playback]\nskip_after = 20\n"))
    assert any("31" in p for p in cfg.issues())


def test_legacy_options_py_is_mapped(tmp_path, monkeypatch):
    legacy = tmp_path / "options.py"
    legacy.write_text(
        'CLIENT_ID = "id"\nCLIENT_SECRET = "sec"\nPLAYLIST_NAME = "Old"\n'
        'SERVER_NAMES = ["srv"]\nSKIP_SONGS = False\nCHEAKS_BEFORE_PLAYING = 7\n'
        "NOTIFICATION_ENABLED = False\n"
    )
    monkeypatch.setattr("spotiafk.config.BASE_DIR", str(tmp_path))
    monkeypatch.setattr("spotiafk.config.default_config_path", lambda: str(tmp_path / "absent"))
    monkeypatch.chdir(tmp_path)
    cfg = Config.load()
    assert cfg.playlist == "Old"
    assert cfg.play_on == ("srv",)
    assert cfg.skip_after is None  # SKIP_SONGS = False
    assert cfg.idle_checks == 7  # old typo name accepted
    assert cfg.telegram is None
