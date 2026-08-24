"""Configuration: user options from options.py, derived paths, and validation.

Options are read straight from options.py via module ``__getattr__``;
only derived values, constants, and validation live here.
"""

import logging
import os
import sys

import options as _options

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SCOPE = "user-modify-playback-state playlist-read-private user-read-playback-state"
MAX_BACKOFF = 300  # seconds; cap for the main loop's error backoff
MS_PER_SECOND = 1000
PLAY_CHECK_SLICE = 5  # seconds; how often to re-check activity while a track plays

# Old misspelled option names still accepted from existing options.py files
_COMPAT_NAMES = {
    "CHECKS_BEFORE_PLAYING": "CHEAKS_BEFORE_PLAYING",
    "TIME_BETWEEN_CHECKS": "TIME_BETWEEN_CHEAKS",
    "UPDATE_PLAYLIST_NOTIFICATION": "UPDATE_PALYLIST_NOTIFICATION",
}

# Paths (anchored to the repo directory so any working directory works)
TIMELOG_PATH = os.path.join(BASE_DIR, _options.TIMELOG_FILENAME)
NOTIFICATION_CONF = os.path.join(BASE_DIR, _options.NOTIFICATION_FILENAME)
TOKEN_PATH = os.path.join(BASE_DIR, f"token-{_options.USERNAME}.dat")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

logger = logging.getLogger(__name__)


def __getattr__(name):
    if hasattr(_options, name):
        return getattr(_options, name)
    old_name = _COMPAT_NAMES.get(name)
    if old_name and hasattr(_options, old_name):
        return getattr(_options, old_name)
    raise AttributeError(f"options.py defines no option {name!r}")


def validate() -> None:
    """Fail fast with a clear message when options.py is not filled in."""
    problems = []
    if not _options.CLIENT_ID or set(_options.CLIENT_ID) == {"X"}:
        problems.append("CLIENT_ID is not configured")
    if not _options.CLIENT_SECRET or set(_options.CLIENT_SECRET) == {"X"}:
        problems.append("CLIENT_SECRET is not configured")
    if _options.USERNAME == "USERNAME":
        problems.append("USERNAME is not configured")
    if not _options.SERVER_NAMES:
        problems.append("SERVER_NAMES is empty")
    if _options.NOTIFICATION_ENABLED and not os.path.isfile(NOTIFICATION_CONF):
        problems.append(f"NOTIFICATION_FILENAME not found: {NOTIFICATION_CONF}")
    if problems:
        for problem in problems:
            logger.error("Configuration error: %s", problem)
        sys.exit(f"Fix options.py before running: {', '.join(problems)}")
