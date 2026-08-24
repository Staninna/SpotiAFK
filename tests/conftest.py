"""Stub the external dependencies so the test suite runs without them installed."""

import sys
import types


def _ensure(name):
    try:
        __import__(name)
    except ImportError:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return sys.modules[name]


spotipy = _ensure("spotipy")
if not hasattr(spotipy, "SpotifyException"):

    class SpotifyException(Exception):
        def __init__(self, http_status=0, code=-1, msg="", headers=None):
            super().__init__(msg)
            self.http_status = http_status
            self.headers = headers

    class SpotifyOauthError(Exception):
        pass

    spotipy.SpotifyException = SpotifyException
    spotipy.Spotify = object
    oauth2 = types.ModuleType("spotipy.oauth2")
    oauth2.SpotifyOAuth = object
    oauth2.SpotifyOauthError = SpotifyOauthError
    spotipy.oauth2 = oauth2
    sys.modules["spotipy.oauth2"] = oauth2

telegram_send = _ensure("telegram_send")
if not hasattr(telegram_send, "send"):
    telegram_send.send = lambda **kwargs: None
