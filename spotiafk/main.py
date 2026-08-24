"""Program entry point: logging, startup, and the resilient main loop."""

import datetime
import logging
import os
import signal
import sys
import time

import spotipy

from spotiafk import config, timelog
from spotiafk.notifications import notify
from spotiafk.session import Session
from spotiafk.spotify import make_client

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join(config.LOGS_DIR, f"{stamp}_{os.getpid()}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    setup_logging()
    config.validate()
    logger.info("Started the program")
    notify("INFO", config.START_PROGRAM_NOTIFICATION)

    if not os.path.isfile(config.TIMELOG_PATH):
        timelog.write_total(0.0)

    session = Session(make_client())
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    retries = 0
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
            logger.error("%s: %s", type(error).__name__, error)
            if config.SEND_NOTIFICATION_ON_ERROR and not is_auth_error:
                notify("ERROR", f"{type(error).__name__}: {error} ⚠️⚠️⚠️")
            time.sleep(min(config.RETRY_TIME * 2 ** (retries - 1), config.MAX_BACKOFF))
