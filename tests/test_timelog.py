from spotiafk import config, timelog


def use_tmp_timelog(monkeypatch, tmp_path):
    path = tmp_path / "time.txt"
    monkeypatch.setattr(config, "TIMELOG_PATH", str(path))
    return path


def test_missing_file_reads_zero(monkeypatch, tmp_path):
    use_tmp_timelog(monkeypatch, tmp_path)
    assert timelog.read_total() == 0.0


def test_roundtrip(monkeypatch, tmp_path):
    use_tmp_timelog(monkeypatch, tmp_path)
    timelog.write_total(123.5)
    assert timelog.read_total() == 123.5


def test_corrupt_file_reads_zero(monkeypatch, tmp_path):
    path = use_tmp_timelog(monkeypatch, tmp_path)
    path.write_text("not a number")
    assert timelog.read_total() == 0.0


def test_empty_file_reads_zero(monkeypatch, tmp_path):
    path = use_tmp_timelog(monkeypatch, tmp_path)
    path.write_text("")
    assert timelog.read_total() == 0.0


def test_add_accumulates(monkeypatch, tmp_path):
    use_tmp_timelog(monkeypatch, tmp_path)
    timelog.add(10)
    timelog.add(5)
    assert timelog.read_total() == 15.0


def test_negative_values_are_clamped(monkeypatch, tmp_path):
    use_tmp_timelog(monkeypatch, tmp_path)
    timelog.add(-30)
    assert timelog.read_total() == 0.0
    timelog.write_total(-1)
    assert timelog.read_total() == 0.0
