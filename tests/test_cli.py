import argparse
import json

import pytest

from spotiafk import statusfile
from spotiafk.cli import EXIT_CONFIG, EXIT_NOT_RUNNING, EXIT_OK, _parse_since, main


def write_config(tmp_path):
    path = tmp_path / "spotiafk.toml"
    path.write_text(
        'playlist = "AFK"\nplay_on = ["pi"]\n'
        f"state_dir = {json.dumps(str(tmp_path / 'state'))}\n"
        '[spotify]\nclient_id = "id"\nclient_secret = "sec"\n'
    )
    return str(path)


def test_parse_since_accepts_days_hours_minutes():
    assert _parse_since("7d") < _parse_since("24h") < _parse_since("30m")


def test_parse_since_rejects_garbage():
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_since("soon")


def test_status_not_running_exits_5(tmp_path, capsys):
    code = main(["--config", write_config(tmp_path), "status"])
    assert code == EXIT_NOT_RUNNING
    assert "Not running" in capsys.readouterr().out


def test_status_live_json(tmp_path, capsys):
    config = write_config(tmp_path)
    statusfile.write(str(tmp_path / "state"), "watching", checks="1/5")
    code = main(["--config", config, "status", "--json"])
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["live"] is True
    assert payload["checks"] == "1/5"


def test_stats_json(tmp_path, capsys):
    from spotiafk import stats

    config = write_config(tmp_path)
    stats.add(str(tmp_path / "state"), 90, track="a")
    code = main(["--config", config, "stats", "--json"])
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_seconds"] == 90
    assert payload["tracks"] == 1


def test_missing_config_exits_3(tmp_path, capsys):
    code = main(["--config", str(tmp_path / "absent.toml"), "status"])
    assert code == EXIT_CONFIG
    assert "spotiafk setup" in capsys.readouterr().err
