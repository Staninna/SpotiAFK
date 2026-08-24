from spotiafk import statusfile
from spotiafk.client import Client
from spotiafk.config import Config


def test_no_heartbeat_reads_as_not_running(tmp_path):
    client = Client(Config(state_dir=str(tmp_path)))
    status = client.status()
    assert status["live"] is False


def test_fresh_heartbeat_is_live(tmp_path):
    statusfile.write(str(tmp_path), "watching", checks="2/5")
    status = Client(Config(state_dir=str(tmp_path))).status()
    assert status["live"] is True
    assert status["checks"] == "2/5"


def test_stopped_state_is_not_live(tmp_path):
    statusfile.write(str(tmp_path), "stopped")
    assert Client(Config(state_dir=str(tmp_path))).status()["live"] is False


def test_corrupt_status_file_reads_as_not_running(tmp_path):
    (tmp_path / statusfile.STATUS_FILE).write_text("{broken")
    assert Client(Config(state_dir=str(tmp_path))).status()["live"] is False
