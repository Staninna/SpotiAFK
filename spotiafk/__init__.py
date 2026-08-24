"""spotiAFK — plays a Spotify playlist on your idle devices while you are away.

Public API:

    from spotiafk import Client, Config

    client = Client(Config.load())   # or Client() for the default locations
    client.run()                     # blocking farm loop
    client.status()                  # dict from the run loop's heartbeat
    client.stats()                   # Stats(total_seconds, tracks, by_day)
"""

from spotiafk.client import Client
from spotiafk.config import Config, ConfigError

__version__ = "2.0.0"
__all__ = ["Client", "Config", "ConfigError", "__version__"]
