"""Retry wrapper for Spotify API calls, with lost-time accounting.

Network problems and rate limits are retried with capped exponential
backoff; the seconds spent waiting are accumulated in ``lost_time`` so
they can be subtracted from the played-time total.
"""

import logging
import time

import requests
import spotipy

from spotiafk import config

logger = logging.getLogger("spotiAFK")

TRANSIENT_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,  # covers ReadTimeout/ConnectTimeout
)


class _State:
    def __init__(self) -> None:
        self.lost_time = 0.0


state = _State()


def with_retry(description, func, *args, **kwargs):
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except TRANSIENT_ERRORS:
            delay = min(config.RETRY_TIME * 2 ** attempt, config.MAX_BACKOFF)
            logger.info("Network problem while %s, retrying in %ss", description, delay)
        except spotipy.SpotifyException as error:
            if error.http_status == 429:
                retry_after = error.headers.get("Retry-After") if error.headers else None
                delay = int(retry_after) if retry_after else config.RETRY_TIME
                logger.info("Rate limited while %s, waiting %ss", description, delay)
            elif error.http_status in (500, 502, 503, 504):
                delay = min(config.RETRY_TIME * 2 ** attempt, config.MAX_BACKOFF)
                logger.info("Spotify server error while %s, retrying in %ss", description, delay)
            else:
                raise
        attempt += 1
        state.lost_time += delay
        time.sleep(delay)
