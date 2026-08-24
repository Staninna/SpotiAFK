"""Stub the external dependencies so the test suite runs without them installed."""

import importlib.util
import pathlib
import sys
import types

# options.py is gitignored (it holds the user's credentials); in CI and fresh
# clones, load the committed template in its place.
try:
    import options  # noqa: F401
except ImportError:
    example = pathlib.Path(__file__).resolve().parent.parent / "options.example.py"
    spec = importlib.util.spec_from_file_location("options", example)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["options"] = module


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

    spotipy.SpotifyException = SpotifyException
    spotipy.Spotify = object
    oauth2 = types.ModuleType("spotipy.oauth2")
    oauth2.SpotifyOAuth = object
    spotipy.oauth2 = oauth2
    sys.modules["spotipy.oauth2"] = oauth2

telegram_send = _ensure("telegram_send")
if not hasattr(telegram_send, "send"):
    telegram_send.send = lambda **kwargs: None
