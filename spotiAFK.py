"""spotiAFK — plays a Spotify playlist on your idle devices while you are away.

Checks every TIME_BETWEEN_CHECKS seconds whether your account is free; after
CHECKS_BEFORE_PLAYING consecutive free checks it transfers playback to one of
your SERVER_NAMES devices and plays tracks from PLAYLIST_NAME, stopping as
soon as you start listening yourself. Total play time is tracked in the
timelog file, and optional Telegram notifications report state changes.
"""

import datetime
import logging
import os
import random
import signal
import stat
import sys
import time

import requests
import spotipy
import telegram_send
from spotipy.oauth2 import SpotifyOAuth

import options as cfg

# Paths and constants
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SCOPE = "user-modify-playback-state playlist-read-private user-read-playback-state"
MAX_BACKOFF = 300  # seconds; cap for exponential retry backoff
MS_PER_SECOND = 1000
PLAY_CHECK_SLICE = 5  # seconds; how often to re-check activity while a track plays

TRANSIENT_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,  # covers ReadTimeout/ConnectTimeout
)


def _opt(*names, default=None):
    """Read a config value, accepting old misspelled names for compatibility."""
    for name in names:
        if hasattr(cfg, name):
            return getattr(cfg, name)
    return default


CHECKS_BEFORE_PLAYING = _opt("CHECKS_BEFORE_PLAYING", "CHEAKS_BEFORE_PLAYING", default=5)
TIME_BETWEEN_CHECKS = _opt("TIME_BETWEEN_CHECKS", "TIME_BETWEEN_CHEAKS", default=30)
UPDATE_PLAYLIST_NOTIFICATION = _opt(
    "UPDATE_PLAYLIST_NOTIFICATION", "UPDATE_PALYLIST_NOTIFICATION", default="Updated playlist 🎵"
)

TIMELOG_PATH = os.path.join(BASE_DIR, cfg.TIMELOG_FILENAME)
NOTIFICATION_CONF = os.path.join(BASE_DIR, cfg.NOTIFICATION_FILENAME)
TOKEN_PATH = os.path.join(BASE_DIR, f"token-{cfg.USERNAME}.dat")

logger = logging.getLogger("spotiAFK")


def setup_logging() -> None:
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = os.path.join(logs_dir, f"{stamp}_{os.getpid()}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        handlers=[logging.FileHandler(logfile), logging.StreamHandler(sys.stdout)],
    )


def validate_config() -> None:
    problems = []
    if not cfg.CLIENT_ID or set(cfg.CLIENT_ID) == {"X"}:
        problems.append("CLIENT_ID is not configured")
    if not cfg.CLIENT_SECRET or set(cfg.CLIENT_SECRET) == {"X"}:
        problems.append("CLIENT_SECRET is not configured")
    if cfg.USERNAME == "USERNAME":
        problems.append("USERNAME is not configured")
    if not cfg.SERVER_NAMES:
        problems.append("SERVER_NAMES is empty")
    if cfg.NOTIFICATION_ENABLED and not os.path.isfile(NOTIFICATION_CONF):
        problems.append(f"NOTIFICATION_FILENAME not found: {NOTIFICATION_CONF}")
    if problems:
        for problem in problems:
            logger.error("Configuration error: %s", problem)
        sys.exit(f"Fix options.py before running: {', '.join(problems)}")


def notify(level: str, message: str) -> None:
    """Send a Telegram notification; never let a notification failure crash us."""
    if not cfg.NOTIFICATION_ENABLED:
        return
    timestamp = str(datetime.datetime.now()).split(".")[0]
    try:
        telegram_send.send(
            messages=[f"{timestamp}: {level}: {message}"],
            conf=NOTIFICATION_CONF,
            silent=True,
        )
    except Exception as error:
        logger.warning("Failed to send Telegram notification: %s", error)


class RetryState:
    """Tracks time lost to network problems so it can be subtracted from playtime."""

    def __init__(self) -> None:
        self.lost_time = 0.0


RETRY = RetryState()


def with_retry(description, func, *args, **kwargs):
    """Run a Spotify API call, retrying transient network and rate-limit errors."""
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except TRANSIENT_ERRORS:
            delay = min(cfg.RETRY_TIME * 2 ** attempt, MAX_BACKOFF)
            logger.info("Network problem while %s, retrying in %ss", description, delay)
        except spotipy.SpotifyException as error:
            if error.http_status == 429:
                retry_after = error.headers.get("Retry-After") if error.headers else None
                delay = int(retry_after) if retry_after else cfg.RETRY_TIME
                logger.info("Rate limited while %s, waiting %ss", description, delay)
            elif error.http_status in (500, 502, 503, 504):
                delay = min(cfg.RETRY_TIME * 2 ** attempt, MAX_BACKOFF)
                logger.info("Spotify server error while %s, retrying in %ss", description, delay)
            else:
                raise
        attempt += 1
        RETRY.lost_time += delay
        time.sleep(delay)


def make_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=cfg.CLIENT_ID,
        client_secret=cfg.CLIENT_SECRET,
        redirect_uri=cfg.REDIRECT_URI,
        scope=SCOPE,
        cache_path=TOKEN_PATH,
        open_browser=False,
    )
    client = spotipy.Spotify(auth_manager=auth_manager, retries=0)
    with_retry("authenticating", client.current_user)
    if os.path.isfile(TOKEN_PATH):
        os.chmod(TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)  # keep the refresh token private
    logger.info("Authenticated with Spotify")
    return client


def account_is_free(client: spotipy.Spotify) -> bool:
    """True when nobody is listening, or playback is already on one of our servers."""
    playing = with_retry("checking current playback", client.current_user_playing_track)
    if not playing or not playing.get("is_playing"):
        return True
    devices = with_retry("listing devices", client.devices)["devices"]
    active = [d for d in devices if d.get("is_active")]
    if not active:
        return True
    return all(d["name"] in cfg.SERVER_NAMES for d in active)


def get_server_ids(client: spotipy.Spotify) -> list:
    while True:
        devices = with_retry("listing devices", client.devices)["devices"]
        server_ids = [d["id"] for d in devices if d["name"] in cfg.SERVER_NAMES]
        if server_ids:
            for device in devices:
                if device["id"] in server_ids:
                    logger.info("Server named %s found", device["name"])
            return server_ids
        logger.info("The servers %s were not found, retrying in %ss", cfg.SERVER_NAMES, cfg.RETRY_TIME)
        RETRY.lost_time += cfg.RETRY_TIME
        time.sleep(cfg.RETRY_TIME)


def get_tracks(client: spotipy.Spotify, send_notification: bool = False) -> list:
    """Return [uri, duration_seconds, name] for every playable track in the playlist."""
    playlist_id = None
    playlists = with_retry("listing playlists", client.current_user_playlists)
    while playlists:
        for playlist in playlists["items"]:
            if playlist["name"] == cfg.PLAYLIST_NAME:
                playlist_id = playlist["id"]
                break
        if playlist_id or not playlists["next"]:
            break
        playlists = with_retry("listing playlists", client.next, playlists)
    if playlist_id is None:
        raise RuntimeError(f"Playlist {cfg.PLAYLIST_NAME!r} was not found on this account")

    tracks_to_play = []
    tracks = with_retry("fetching playlist tracks", client.playlist, playlist_id)["tracks"]
    while tracks:
        for item in tracks["items"]:
            track = item.get("track")
            if not track or not track.get("uri") or track.get("duration_ms") is None:
                continue  # removed/unavailable tracks and episodes
            tracks_to_play.append(
                [track["uri"], track["duration_ms"] / MS_PER_SECOND, track["name"]]
            )
        tracks = with_retry("fetching playlist tracks", client.next, tracks) if tracks["next"] else None

    if cfg.RANDOM_ORDER_TRACKS:
        random.shuffle(tracks_to_play)
    logger.info("Updated playlist (%d tracks)", len(tracks_to_play))
    if send_notification:
        notify("INFO", UPDATE_PLAYLIST_NOTIFICATION)
    return tracks_to_play


def read_total_time() -> float:
    try:
        with open(TIMELOG_PATH) as f:
            return float(f.readline() or 0.0)
    except (OSError, ValueError):
        return 0.0


def write_total_time(total: float) -> None:
    tmp_path = TIMELOG_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        f.write(str(max(0.0, total)))
    os.replace(tmp_path, TIMELOG_PATH)


class Session:
    """State for one run of the main loop."""

    def __init__(self, client: spotipy.Spotify) -> None:
        self.client = client
        self.server_ids = get_server_ids(client)
        self.success_checks = 0
        self.playing = False
        self.start_playing_time = 0.0
        self.last_message = None

    def notify_once(self, key: str, message: str) -> None:
        if self.last_message != key:
            notify("INFO", message)
            self.last_message = key

    def start_playing(self) -> None:
        logger.info("Started playing tracks")
        self.start_playing_time = time.time()
        RETRY.lost_time = 0.0
        self.notify_once("start", cfg.START_PLAYING_NOTIFICATION)
        self.playing = True

    def stop_playing(self) -> None:
        if not self.playing:
            return
        logger.info("Stopped playing tracks")
        played = (time.time() - self.start_playing_time) - RETRY.lost_time
        write_total_time(read_total_time() + max(0.0, played))
        RETRY.lost_time = 0.0
        self.notify_once("stop", cfg.STOP_PLAYING_NOTIFICATION)
        self.playing = False
        self.success_checks = 0

    def transfer_to_server(self) -> None:
        """Try each configured server until one accepts playback."""
        for attempt in range(2):
            for server_id in self.server_ids:
                try:
                    with_retry("transferring playback", self.client.transfer_playback, server_id, False)
                    return
                except spotipy.SpotifyException as error:
                    if error.http_status == 404:
                        logger.info("Server %s is gone, trying the next one", server_id)
                        continue
                    raise
            self.server_ids = get_server_ids(self.client)
        raise RuntimeError("No configured server accepted playback")

    def wait_out_track(self, duration: float) -> bool:
        """Sleep while the track plays, aborting early if the user becomes active.

        Returns True if the user took over playback."""
        deadline = time.time() + (cfg.SKIP_DELAY if cfg.SKIP_SONGS else duration)
        while time.time() < deadline:
            time.sleep(min(PLAY_CHECK_SLICE, max(0.0, deadline - time.time())))
            if not account_is_free(self.client):
                return True
        return False

    def play_round(self) -> None:
        """One pass over the playlist; returns when the user takes over or list ends."""
        self.transfer_to_server()
        for uri, duration, name in get_tracks(self.client):
            if not account_is_free(self.client):
                self.stop_playing()
                return
            with_retry("adding track to queue", self.client.add_to_queue, uri)
            with_retry("skipping to next track", self.client.next_track)
            if self.wait_out_track(duration):
                self.stop_playing()
                return
            logger.info("Played %s", name)

    def tick(self) -> None:
        time.sleep(TIME_BETWEEN_CHECKS)
        if account_is_free(self.client):
            self.success_checks += 1
        else:
            self.success_checks = 0
            self.stop_playing()
        logger.info(
            "Checked if I could play, success rate is [%d/%d]",
            self.success_checks, CHECKS_BEFORE_PLAYING,
        )
        if self.success_checks >= CHECKS_BEFORE_PLAYING:
            if not self.playing:
                self.start_playing()
            self.play_round()


def main() -> None:
    setup_logging()
    validate_config()
    logger.info("Started the program")
    notify("INFO", cfg.START_PROGRAM_NOTIFICATION)

    if not os.path.isfile(TIMELOG_PATH):
        write_total_time(0.0)

    client = make_client()
    session = Session(client)
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
            if cfg.SEND_NOTIFICATION_ON_ERROR and not is_auth_error:
                notify("ERROR", f"{type(error).__name__}: {error} ⚠️⚠️⚠️")
            time.sleep(min(cfg.RETRY_TIME * 2 ** (retries - 1), MAX_BACKOFF))
            try:
                session.server_ids = get_server_ids(client)
            except Exception as recovery_error:
                logger.error("Recovery failed: %s", recovery_error)


if __name__ == "__main__":
    main()
