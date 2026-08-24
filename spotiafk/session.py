"""The play/idle state machine driving spotiAFK's main loop."""

import logging
import time

import spotipy

from spotiafk import config, timelog
from spotiafk.notifications import notify
from spotiafk.retry import state, with_retry
from spotiafk.spotify import account_is_free, get_server_ids, get_tracks

logger = logging.getLogger("spotiAFK")


class Session:
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
        state.lost_time = 0.0
        self.notify_once("start", config.START_PLAYING_NOTIFICATION)
        self.playing = True

    def stop_playing(self) -> None:
        if not self.playing:
            return
        logger.info("Stopped playing tracks")
        played = (time.time() - self.start_playing_time) - state.lost_time
        timelog.add(played)
        state.lost_time = 0.0
        self.notify_once("stop", config.STOP_PLAYING_NOTIFICATION)
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
        """Sleep while the track plays; returns True if the user took over playback."""
        deadline = time.time() + (config.SKIP_DELAY if config.SKIP_SONGS else duration)
        while time.time() < deadline:
            time.sleep(min(config.PLAY_CHECK_SLICE, max(0.0, deadline - time.time())))
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
        time.sleep(config.TIME_BETWEEN_CHECKS)
        if account_is_free(self.client):
            self.success_checks += 1
        else:
            self.success_checks = 0
            self.stop_playing()
        logger.info(
            "Checked if I could play, success rate is [%d/%d]",
            self.success_checks, config.CHECKS_BEFORE_PLAYING,
        )
        if self.success_checks >= config.CHECKS_BEFORE_PLAYING:
            if not self.playing:
                self.start_playing()
            self.play_round()
