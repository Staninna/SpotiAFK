"""The public Python API: Config.load() + Client(run/status/stats)."""

import datetime
import logging
import os
import signal
import sys
import time

import spotipy

from spotiafk import stats, statusfile
from spotiafk.config import MAX_BACKOFF, Config
from spotiafk.notifications import notify
from spotiafk.session import Session
from spotiafk.spotify import make_client

logger = logging.getLogger(__name__)

START_PROGRAM_MESSAGE = "Starting program 🏁"


def setup_logging(cfg: Config) -> None:
    logs_dir = os.path.join(cfg.state_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join(logs_dir, f"{stamp}_{os.getpid()}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)],
    )


class Client:
    """Everything a caller can do with spotiAFK: run it, ask its status and stats."""

    def __init__(self, config: Config | None = None) -> None:
        self.cfg = config if config is not None else Config.load()

    def run(self) -> None:
        """Validate, authenticate, and farm until interrupted. Blocking."""
        self.cfg.require_valid()
        stats.import_legacy(self.cfg.state_dir)
        logger.info("Started the program")
        notify(self.cfg, "INFO", START_PROGRAM_MESSAGE)

        session = Session(make_client(self.cfg), self.cfg)
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

        retries = 0
        try:
            while True:
                try:
                    session.tick()
                    retries = 0
                except (KeyboardInterrupt, SystemExit):
                    session.stop_playing()
                    logger.info("Shutting down")
                    raise
                except Exception as error:
                    retries += 1
                    is_auth_error = (
                        isinstance(error, spotipy.SpotifyException) and error.http_status == 401
                    )
                    logger.exception("%s: %s", type(error).__name__, error)
                    telegram = self.cfg.telegram
                    if telegram and telegram.notify_on_error and not is_auth_error:
                        notify(self.cfg, "ERROR", f"{type(error).__name__}: {error} ⚠️⚠️⚠️")
                    statusfile.write(self.cfg.state_dir, "retrying", error=str(error))
                    time.sleep(min(self.cfg.retry_time * 2 ** (retries - 1), MAX_BACKOFF))
        finally:
            statusfile.write(self.cfg.state_dir, "stopped")

    def status(self) -> dict:
        """The last heartbeat the run loop wrote, plus whether it looks live."""
        status = statusfile.read(self.cfg.state_dir)
        if status is None:
            return {"state": "not running", "live": False}
        age = statusfile.age_seconds(status)
        stale_after = max(3 * self.cfg.check_interval, 90)
        live = status.get("state") not in ("stopped",) and age is not None and age < stale_after
        return {**status, "live": live, "age_seconds": None if age is None else round(age)}

    def stats(self, since: datetime.datetime | None = None) -> stats.Stats:
        stats.import_legacy(self.cfg.state_dir)
        return stats.summary(self.cfg.state_dir, since=since)
