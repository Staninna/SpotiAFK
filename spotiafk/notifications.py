"""Telegram notifications that never crash the program."""

import datetime
import logging

import telegram_send

from spotiafk import config

logger = logging.getLogger(__name__)


def notify(level: str, message: str) -> None:
    if not config.NOTIFICATION_ENABLED:
        return
    timestamp = str(datetime.datetime.now()).split(".")[0]
    try:
        telegram_send.send(
            messages=[f"{timestamp}: {level}: {message}"],
            conf=config.NOTIFICATION_CONF,
            silent=True,
        )
    except Exception as error:
        logger.warning("Failed to send Telegram notification: %s", error)
