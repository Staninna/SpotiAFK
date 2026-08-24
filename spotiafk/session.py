"""The play/idle state machine driving spotiAFK's run loop."""

import logging
import time

import spotipy

from spotiafk import stats, statusfile
from spotiafk.config import PLAY_CHECK_SLICE, Config
from spotiafk.notifications import notify
from spotiafk.spotify import account_is_free, get_server_ids, get_tracks

logger = logging.getLogger(__name__)

START_MESSAGE = "Started playing 🟩"
STOP_MESSAGE = "Stopped playing 🟥"


class Session:
    def __init__(self, client: spotipy.Spotify, cfg: Config) -> None:
        self.client = client
        self.cfg = cfg
        self.server_ids = get_server_ids(client, cfg)
        self.success_checks = 0
        self.playing = False
        self.last_message = None

    def notify_once(self, message: str) -> None:
        if self.last_message != message:
            notify(self.cfg, "INFO", message)
            self.last_message = message

    def start_playing(self) -> None:
        logger.info("Started playing tracks")
        self.notify_once(START_MESSAGE)
        self.playing = True

    def stop_playing(self) -> None:
        if not self.playing:
            return
        logger.info("Stopped playing tracks")
        self.notify_once(STOP_MESSAGE)
        self.playing = False
        self.success_checks = 0

    def transfer_to_server(self) -> None:
        """Try each configured device until one accepts playback."""
        refreshed = False
        while True:
            for server_id in self.server_ids:
                try:
                    self.client.transfer_playback(server_id, False)
                    return
                except spotipy.SpotifyException as error:
                    if error.http_status != 404:
                        raise
                    logger.info("Device %s is gone, trying the next one", server_id)
            if refreshed:
                raise RuntimeError("No configured device accepted playback")
            self.server_ids = get_server_ids(self.client, self.cfg)
            refreshed = True

    def wait_out_track(self, duration: float, name: str) -> bool:
        """Sleep while the track plays, crediting elapsed time to the play history.

        Returns True if the user took over playback."""
        start = time.time()
        wait = self.cfg.skip_after if self.cfg.skip_after is not None else duration
        deadline = start + wait
        try:
            while time.time() < deadline:
                time.sleep(min(PLAY_CHECK_SLICE, max(0.0, deadline - time.time())))
                if not account_is_free(self.client, self.cfg):
                    return True
            return False
        finally:
            stats.add(self.cfg.state_dir, time.time() - start, track=name)

    def play_round(self) -> None:
        """One pass over the playlist; returns when the user takes over or list ends."""
        self.transfer_to_server()
        for uri, duration, name in get_tracks(self.client, self.cfg):
            self.client.add_to_queue(uri)
            self.client.next_track()
            statusfile.write(self.cfg.state_dir, "playing", track=name)
            if self.wait_out_track(duration, name):
                self.stop_playing()
                return
            logger.info("Played %s", name)

    def tick(self) -> None:
        time.sleep(self.cfg.check_interval)
        if account_is_free(self.client, self.cfg):
            self.success_checks += 1
        else:
            self.success_checks = 0
            self.stop_playing()
        logger.info(
            "Checked if I could play, success rate is [%d/%d]",
            self.success_checks, self.cfg.idle_checks,
        )
        statusfile.write(
            self.cfg.state_dir, "watching",
            checks=f"{self.success_checks}/{self.cfg.idle_checks}",
        )
        if self.success_checks >= self.cfg.idle_checks:
            if not self.playing:
                self.start_playing()
            self.play_round()
