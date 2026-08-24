"""Spotify API access: authentication and the queries spotiAFK needs.

Transient failures (network errors, 429 rate limits, 5xx) are handled by
spotipy's built-in urllib3 retry with backoff, configured on the client;
anything that still escapes is handled by the run loop's error handler.
"""

import glob
import logging
import os
import random
import shutil
import stat
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotiafk.config import BASE_DIR, MS_PER_SECOND, SCOPE, Config

logger = logging.getLogger(__name__)


def token_cache_path(cfg: Config) -> str:
    return os.path.join(cfg.state_dir, "token.dat")


def _migrate_legacy_token(cfg: Config) -> None:
    cache = token_cache_path(cfg)
    if os.path.isfile(cache):
        return
    legacy = sorted(glob.glob(os.path.join(BASE_DIR, "token-*.dat")))
    if legacy:
        os.makedirs(cfg.state_dir, exist_ok=True)
        shutil.copy(legacy[0], cache)
        logger.info("Migrated legacy token cache into %s", cfg.state_dir)


def make_client(cfg: Config) -> spotipy.Spotify:
    _migrate_legacy_token(cfg)
    os.makedirs(cfg.state_dir, exist_ok=True)
    auth_manager = SpotifyOAuth(
        client_id=cfg.client_id,
        client_secret=cfg.client_secret,
        redirect_uri=cfg.redirect_uri,
        scope=SCOPE,
        cache_path=token_cache_path(cfg),
        open_browser=False,
    )
    client = spotipy.Spotify(
        auth_manager=auth_manager,
        requests_timeout=15,
        retries=5,
        status_retries=5,
        backoff_factor=1,  # urllib3 backoff; also honors Retry-After on 429
    )
    client.current_user()
    if os.path.isfile(token_cache_path(cfg)):
        os.chmod(token_cache_path(cfg), stat.S_IRUSR | stat.S_IWUSR)
    logger.info("Authenticated with Spotify")
    return client


def account_is_free(client: spotipy.Spotify, cfg: Config) -> bool:
    """True when nobody is listening, or playback is already on one of our devices."""
    playing = client.current_user_playing_track()
    if not playing or not playing.get("is_playing"):
        return True
    active = [d for d in client.devices()["devices"] if d.get("is_active")]
    if not active:
        return True
    return all(d["name"] in cfg.play_on for d in active)


def get_server_ids(client: spotipy.Spotify, cfg: Config) -> list:
    """Ids of the configured devices, waiting until at least one is online."""
    while True:
        servers = [d for d in client.devices()["devices"] if d["name"] in cfg.play_on]
        if servers:
            for device in servers:
                logger.info("Device named %s found", device["name"])
            return [d["id"] for d in servers]
        logger.info("None of %s are online, retrying in %ss", list(cfg.play_on), cfg.retry_time)
        time.sleep(cfg.retry_time)


def find_playlist_id(client: spotipy.Spotify, name: str) -> str | None:
    playlists = client.current_user_playlists()
    while playlists:
        for playlist in playlists["items"]:
            if playlist and playlist["name"] == name:
                return playlist["id"]
        playlists = client.next(playlists) if playlists["next"] else None
    return None


def get_tracks(client: spotipy.Spotify, cfg: Config) -> list:
    """Return [uri, duration_seconds, name] for every playable track in the playlist."""
    playlist_id = find_playlist_id(client, cfg.playlist)
    if playlist_id is None:
        raise RuntimeError(f"Playlist {cfg.playlist!r} was not found on this account")

    tracks_to_play = []
    page = client.playlist_items(playlist_id)
    while page:
        for entry in page["items"]:
            # the API renamed the entry key from "track" to "item"; accept both
            track = entry.get("item") or entry.get("track")
            if not track or not track.get("uri") or track.get("duration_ms") is None:
                continue  # removed/unavailable tracks and episodes
            tracks_to_play.append(
                [track["uri"], track["duration_ms"] / MS_PER_SECOND, track["name"]]
            )
        page = client.next(page) if page["next"] else None

    if cfg.shuffle:
        random.shuffle(tracks_to_play)
    logger.info("Updated playlist (%d tracks)", len(tracks_to_play))
    return tracks_to_play
