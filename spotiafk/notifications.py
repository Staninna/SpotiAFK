"""Telegram notifications that never crash the program."""

import datetime
import logging
import os

import telegram_send

from spotiafk.config import Config

logger = logging.getLogger(__name__)


def _conf_path(cfg: Config) -> str | None:
    """The telegram-send ini file to use, generating one from TOML values if needed."""
    if cfg.telegram is None:
        return None
    if cfg.telegram.conf_path:  # legacy options.py setup points at an existing file
        return cfg.telegram.conf_path
    path = os.path.join(cfg.state_dir, "telegram.conf")
    if not os.path.isfile(path):
        os.makedirs(cfg.state_dir, exist_ok=True)
        with open(path, "w") as f:
            f.write(
                f"[telegram]\ntoken = {cfg.telegram.bot_token}\n"
                f"chat_id = {cfg.telegram.chat_id}\n"
            )
        os.chmod(path, 0o600)
    return path


def notify(cfg: Config, level: str, message: str) -> None:
    conf = _conf_path(cfg)
    if conf is None:
        return
    timestamp = str(datetime.datetime.now()).split(".")[0]
    try:
        telegram_send.send(messages=[f"{timestamp}: {level}: {message}"], conf=conf, silent=True)
    except Exception as error:
        logger.warning("Failed to send Telegram notification: %s", error)
