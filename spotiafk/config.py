"""Configuration: user options from options.py, derived paths, and validation."""

import logging
import os
import sys

import options as _options

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SCOPE = "user-modify-playback-state playlist-read-private user-read-playback-state"
MAX_BACKOFF = 300  # seconds; cap for exponential retry backoff
MS_PER_SECOND = 1000
PLAY_CHECK_SLICE = 5  # seconds; how often to re-check activity while a track plays

logger = logging.getLogger("spotiAFK")


def _opt(*names, default=None):
    """Read an option, accepting old misspelled names for compatibility."""
    for name in names:
        if hasattr(_options, name):
            return getattr(_options, name)
    return default


# Playing
SKIP_SONGS = _options.SKIP_SONGS
SKIP_DELAY = _options.SKIP_DELAY
RANDOM_ORDER_TRACKS = _options.RANDOM_ORDER_TRACKS

# API
CLIENT_ID = _options.CLIENT_ID
CLIENT_SECRET = _options.CLIENT_SECRET
REDIRECT_URI = _options.REDIRECT_URI

# Account
USERNAME = _options.USERNAME
PLAYLIST_NAME = _options.PLAYLIST_NAME
SERVER_NAMES = _options.SERVER_NAMES

# Checks
CHECKS_BEFORE_PLAYING = _opt("CHECKS_BEFORE_PLAYING", "CHEAKS_BEFORE_PLAYING", default=5)
TIME_BETWEEN_CHECKS = _opt("TIME_BETWEEN_CHECKS", "TIME_BETWEEN_CHEAKS", default=30)

# Errors
RETRY_TIME = _options.RETRY_TIME

# Notifications
NOTIFICATION_ENABLED = _options.NOTIFICATION_ENABLED
UPDATE_PLAYLIST_NOTIFICATION = _opt(
    "UPDATE_PLAYLIST_NOTIFICATION", "UPDATE_PALYLIST_NOTIFICATION", default="Updated playlist 🎵"
)
START_PROGRAM_NOTIFICATION = _options.START_PROGRAM_NOTIFICATION
START_PLAYING_NOTIFICATION = _options.START_PLAYING_NOTIFICATION
STOP_PLAYING_NOTIFICATION = _options.STOP_PLAYING_NOTIFICATION
SEND_NOTIFICATION_ON_ERROR = _options.SEND_NOTIFICATION_ON_ERROR

# Paths (anchored to the repo directory so any working directory works)
TIMELOG_PATH = os.path.join(BASE_DIR, _options.TIMELOG_FILENAME)
NOTIFICATION_CONF = os.path.join(BASE_DIR, _options.NOTIFICATION_FILENAME)
TOKEN_PATH = os.path.join(BASE_DIR, f"token-{USERNAME}.dat")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def validate() -> None:
    """Fail fast with a clear message when options.py is not filled in."""
    problems = []
    if not CLIENT_ID or set(CLIENT_ID) == {"X"}:
        problems.append("CLIENT_ID is not configured")
    if not CLIENT_SECRET or set(CLIENT_SECRET) == {"X"}:
        problems.append("CLIENT_SECRET is not configured")
    if USERNAME == "USERNAME":
        problems.append("USERNAME is not configured")
    if not SERVER_NAMES:
        problems.append("SERVER_NAMES is empty")
    if NOTIFICATION_ENABLED and not os.path.isfile(NOTIFICATION_CONF):
        problems.append(f"NOTIFICATION_FILENAME not found: {NOTIFICATION_CONF}")
    if problems:
        for problem in problems:
            logger.error("Configuration error: %s", problem)
        sys.exit(f"Fix options.py before running: {', '.join(problems)}")
