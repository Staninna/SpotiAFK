import datetime

from spotiafk import stats


def test_add_and_summary(tmp_path):
    state = str(tmp_path)
    stats.add(state, 30, track="a")
    stats.add(state, 40, track="b")
    result = stats.summary(state)
    assert result.total_seconds == 70
    assert result.tracks == 2
    assert sum(result.by_day.values()) == 70


def test_zero_and_negative_seconds_are_ignored(tmp_path):
    stats.add(str(tmp_path), 0)
    stats.add(str(tmp_path), -5)
    assert stats.summary(str(tmp_path)).total_seconds == 0


def test_corrupt_lines_are_skipped(tmp_path):
    stats.add(str(tmp_path), 10, track="a")
    with open(tmp_path / stats.EVENTS_FILE, "a") as f:
        f.write("not json\n")
    assert stats.summary(str(tmp_path)).total_seconds == 10


def test_since_filters_out_old_events(tmp_path):
    stats.add(str(tmp_path), 10, track="a")
    future = datetime.datetime.now() + datetime.timedelta(hours=1)
    assert stats.summary(str(tmp_path), since=future).total_seconds == 0


def test_legacy_time_txt_is_imported_once(tmp_path, monkeypatch):
    legacy_dir = tmp_path / "repo"
    legacy_dir.mkdir()
    (legacy_dir / "time.txt").write_text("120.5")
    monkeypatch.setattr(stats, "BASE_DIR", str(legacy_dir))
    state = str(tmp_path / "state")
    stats.import_legacy(state)
    stats.import_legacy(state)  # second call must not double the baseline
    result = stats.summary(state)
    assert result.total_seconds == 120.5
    assert result.tracks == 0
    assert result.by_day == {}  # baseline is excluded from daily breakdown


def test_format_duration():
    assert stats.format_duration(3725) == "1h 02m"
