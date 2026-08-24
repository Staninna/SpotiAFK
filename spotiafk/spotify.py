"""Spotify API access: authentication and the queries spotiAFK needs.

Transient failures (network errors, 429 rate limits, 5xx) are handled by
spotipy's built-in urllib3 retry with backoff, configured on the client;
anything that still escapes is handled by the main loop's error handler.
"""

import logging
import os
import random
import stat
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotiafk import config
from spotiafk.notifications import notify

logger = logging.getLogger(__name__)


def make_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        redirect_uri=config.REDIRECT_URI,
        scope=config.SCOPE,
        cache_path=config.TOKEN_PATH,
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
    if os.path.isfile(config.TOKEN_PATH):
        os.chmod(config.TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)  # keep the refresh token private
    logger.info("Authenticated with Spotify")
    return client


def account_is_free(client: spotipy.Spotify) -> bool:
    """True when nobody is listening, or playback is already on one of our servers."""
    playing = client.current_user_playing_track()
    if not playing or not playing.get("is_playing"):
        return True
    active = [d for d in client.devices()["devices"] if d.get("is_active")]
    if not active:
        return True
    return all(d["name"] in config.SERVER_NAMES for d in active)


def get_server_ids(client: spotipy.Spotify) -> list:
    """Ids of the configured server devices, waiting until at least one is online."""
    while True:
        servers = [d for d in client.devices()["devices"] if d["name"] in config.SERVER_NAMES]
        if servers:
            for device in servers:
                logger.info("Server named %s found", device["name"])
            return [d["id"] for d in servers]
        logger.info(
            "The servers %s were not found, retrying in %ss",
            config.SERVER_NAMES, config.RETRY_TIME,
        )
        time.sleep(config.RETRY_TIME)


def get_tracks(client: spotipy.Spotify, send_notification: bool = False) -> list:
    """Return [uri, duration_seconds, name] for every playable track in the playlist."""
    playlist_id = None
    playlists = client.current_user_playlists()
    while playlists:
        for playlist in playlists["items"]:
            if playlist["name"] == config.PLAYLIST_NAME:
                playlist_id = playlist["id"]
                break
        if playlist_id or not playlists["next"]:
            break
        playlists = client.next(playlists)
    if playlist_id is None:
        raise RuntimeError(f"Playlist {config.PLAYLIST_NAME!r} was not found on this account")

    tracks_to_play = []
    tracks = client.playlist(playlist_id)["tracks"]
    while tracks:
        for item in tracks["items"]:
            track = item.get("track")
            if not track or not track.get("uri") or track.get("duration_ms") is None:
                continue  # removed/unavailable tracks and episodes
            tracks_to_play.append(
                [track["uri"], track["duration_ms"] / config.MS_PER_SECOND, track["name"]]
            )
        tracks = client.next(tracks) if tracks["next"] else None

    if config.RANDOM_ORDER_TRACKS:
        random.shuffle(tracks_to_play)
    logger.info("Updated playlist (%d tracks)", len(tracks_to_play))
    if send_notification:
        notify("INFO", config.UPDATE_PLAYLIST_NOTIFICATION)
    return tracks_to_play
