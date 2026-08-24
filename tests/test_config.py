import pytest

import options
from spotiafk import config


def test_options_are_delegated():
    assert config.SKIP_DELAY == options.SKIP_DELAY
    assert config.RETRY_TIME == options.RETRY_TIME


def test_corrected_names_fall_back_to_old_typos(monkeypatch):
    monkeypatch.delattr(options, "CHECKS_BEFORE_PLAYING", raising=False)
    monkeypatch.setattr(options, "CHEAKS_BEFORE_PLAYING", 9, raising=False)
    assert config.CHECKS_BEFORE_PLAYING == 9


def test_unknown_option_raises():
    with pytest.raises(AttributeError):
        _ = config.NO_SUCH_OPTION


def test_validate_rejects_placeholder_config(monkeypatch):
    monkeypatch.setattr(options, "CLIENT_ID", "X" * 32)
    with pytest.raises(SystemExit):
        config.validate()


def test_validate_rejects_empty_server_list(monkeypatch):
    monkeypatch.setattr(options, "CLIENT_ID", "real-id")
    monkeypatch.setattr(options, "CLIENT_SECRET", "real-secret")
    monkeypatch.setattr(options, "USERNAME", "stan")
    monkeypatch.setattr(options, "SERVER_NAMES", [])
    with pytest.raises(SystemExit):
        config.validate()
