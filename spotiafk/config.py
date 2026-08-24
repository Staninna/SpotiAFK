"""Configuration: a small TOML file, with legacy options.py still honored.

Search order: explicit path, $SPOTIAFK_CONFIG, ./spotiafk.toml,
~/.config/spotiafk/config.toml, and finally a legacy options.py next to
the repo. State (token cache, play history, logs, status) lives in
~/.local/share/spotiafk/ regardless of where the config came from.
"""

import dataclasses
import importlib.util
import os
import tomllib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SCOPE = "user-modify-playback-state playlist-read-private user-read-playback-state"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback/"
MAX_BACKOFF = 300  # seconds; cap for the main loop's error backoff
MS_PER_SECOND = 1000
PLAY_CHECK_SLICE = 5  # seconds; how often to re-check activity while a track plays


class ConfigError(Exception):
    """The configuration is missing or invalid; message says how to fix it."""


def default_config_path() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(config_home, "spotiafk", "config.toml")


def default_state_dir() -> str:
    data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(data_home, "spotiafk")


@dataclasses.dataclass(frozen=True)
class Telegram:
    bot_token: str = ""
    chat_id: str = ""
    notify_on_error: bool = True
    conf_path: str | None = None  # legacy telegram-send ini file


@dataclasses.dataclass(frozen=True)
class Config:
    playlist: str = ""
    play_on: tuple = ()
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = DEFAULT_REDIRECT_URI
    skip_after: float | None = 35.0  # seconds per track; None plays tracks in full
    shuffle: bool = True
    idle_checks: int = 5
    check_interval: float = 30.0
    retry_time: float = 10.0
    telegram: Telegram | None = None
    state_dir: str = dataclasses.field(default_factory=default_state_dir)
    source: str = "<defaults>"

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> "Config":
        """Load config from the first location found; raise ConfigError if none."""
        candidates = (
            [os.fspath(path)]
            if path is not None
            else [
                os.environ.get("SPOTIAFK_CONFIG", ""),
                os.path.join(os.getcwd(), "spotiafk.toml"),
                default_config_path(),
            ]
        )
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return cls._from_toml(candidate)
        legacy = os.path.join(BASE_DIR, "options.py")
        if path is None and os.path.isfile(legacy):
            return cls._from_options_py(legacy)
        raise ConfigError(
            "No configuration found. Run 'spotiafk setup' to create one "
            f"(looked for spotiafk.toml here and at {default_config_path()})."
        )

    @classmethod
    def _from_toml(cls, path: str) -> "Config":
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as error:
            raise ConfigError(f"{path} is not valid TOML: {error}") from error
        spotify = data.get("spotify", {})
        playback = data.get("playback", {})
        checks = data.get("checks", {})
        telegram = None
        if "telegram" in data:
            telegram = Telegram(
                bot_token=data["telegram"].get("bot_token", ""),
                chat_id=str(data["telegram"].get("chat_id", "")),
                notify_on_error=data["telegram"].get("notify_on_error", True),
            )
        skip_after = playback.get("skip_after", 35)
        return cls(
            playlist=data.get("playlist", ""),
            play_on=tuple(data.get("play_on", [])),
            client_id=spotify.get("client_id", ""),
            client_secret=spotify.get("client_secret", ""),
            redirect_uri=spotify.get("redirect_uri", DEFAULT_REDIRECT_URI),
            skip_after=None if skip_after in (False, 0) else float(skip_after),
            shuffle=playback.get("shuffle", True),
            idle_checks=int(checks.get("idle_checks", 5)),
            check_interval=float(checks.get("interval", 30)),
            retry_time=float(checks.get("retry", 10)),
            telegram=telegram,
            state_dir=os.path.expanduser(data.get("state_dir", default_state_dir())),
            source=path,
        )

    @classmethod
    def _from_options_py(cls, path: str) -> "Config":
        spec = importlib.util.spec_from_file_location("spotiafk_legacy_options", path)
        opts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(opts)

        def get(*names, default=None):
            for name in names:
                if hasattr(opts, name):
                    return getattr(opts, name)
            return default

        telegram = None
        if get("NOTIFICATION_ENABLED", default=False):
            telegram = Telegram(
                notify_on_error=get("SEND_NOTIFICATION_ON_ERROR", default=True),
                conf_path=os.path.join(
                    BASE_DIR, get("NOTIFICATION_FILENAME", default="telegram.conf")
                ),
            )
        return cls(
            playlist=get("PLAYLIST_NAME", default=""),
            play_on=tuple(get("SERVER_NAMES", default=[])),
            client_id=get("CLIENT_ID", default=""),
            client_secret=get("CLIENT_SECRET", default=""),
            redirect_uri=get("REDIRECT_URI", default=DEFAULT_REDIRECT_URI),
            skip_after=(
                float(get("SKIP_DELAY", default=35)) if get("SKIP_SONGS", default=True) else None
            ),
            shuffle=get("RANDOM_ORDER_TRACKS", default=True),
            idle_checks=int(get("CHECKS_BEFORE_PLAYING", "CHEAKS_BEFORE_PLAYING", default=5)),
            check_interval=float(get("TIME_BETWEEN_CHECKS", "TIME_BETWEEN_CHEAKS", default=30)),
            retry_time=float(get("RETRY_TIME", default=10)),
            telegram=telegram,
            source=path,
        )

    def issues(self) -> list:
        """Human-readable problems, each with the fix; empty list means valid."""
        problems = []
        if not self.client_id or set(self.client_id) == {"X"}:
            problems.append("spotify.client_id is not set — copy it from your Spotify app")
        if not self.client_secret or set(self.client_secret) == {"X"}:
            problems.append("spotify.client_secret is not set — copy it from your Spotify app")
        if not self.playlist:
            problems.append("playlist is not set — the playlist name to play from")
        if not self.play_on:
            problems.append("play_on is empty — list at least one Spotify device name")
        if self.skip_after is not None and self.skip_after < 31:
            problems.append(
                "playback.skip_after must be at least 31s for a play to count as a stream"
            )
        if self.telegram and not self.telegram.conf_path:
            if not self.telegram.bot_token:
                problems.append("telegram.bot_token is missing — get it from BotFather")
            if not self.telegram.chat_id:
                problems.append("telegram.chat_id is missing — message @userinfobot for yours")
        return problems

    def require_valid(self) -> None:
        problems = self.issues()
        if problems:
            raise ConfigError(
                f"Fix {self.source} before running:\n  - " + "\n  - ".join(problems)
            )
