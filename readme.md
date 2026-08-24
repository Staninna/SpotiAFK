# spotiAFK

<div align="center">
    <img width="80%" src="https://i.imgur.com/VTRXwHa.png">
</div>

## What is it?

It is a simple AFK program that plays Spotify when you are not using your account. To support your favorite artists on the platform.

## How does it work?

It uses the Spotify API to check if you are listening to music and if you don't for a while, it starts playing on a device you specify. As soon as you press play anywhere yourself, it backs off.

## Quick start

```bash
git clone https://github.com/Staninna/SpotiAFK && cd SpotiAFK
python3 -m venv venv && source venv/bin/activate
pip install -e .

spotiafk setup     # guided: Spotify app creds, login, pick playlist + device (~3 min)
spotiafk run       # start farming; Ctrl-C stops
```

The one thing `setup` can't do for you: create the Spotify app itself. Go to the [developer dashboard](https://developer.spotify.com/dashboard), create an app (tick Web API), and add `http://127.0.0.1:8888/callback/` under Redirect URIs in its settings. `setup` asks for the app's Client ID and Client secret and handles the rest, including logging you in.

## Commands

| Command                 | What it does                                                            |
| ----------------------- | ----------------------------------------------------------------------- |
| `spotiafk setup`        | Guided first-time setup; writes the config file                          |
| `spotiafk run`          | Start farming (foreground; supervise with systemd/tmux if you want)      |
| `spotiafk status`       | Is it running, what is it doing right now (`--json` for scripts)         |
| `spotiafk stats`        | Total playtime and per-day breakdown (`--since 7d`, `--json`)            |
| `spotiafk doctor`       | Checks config, auth, playlist, and devices; each failure comes with a fix |

Exit codes mean something: 0 ok, 1 runtime error, 2 usage, 3 invalid config, 4 auth failure, 5 not running (`status`). Example session:

```console
$ spotiafk doctor
  ✓ config loaded from ~/.config/spotiafk/config.toml
  ✓ authenticated as Stan
  ✓ playlist 'AFK' found
  ✓ devices online: pi
  ✓ all checks passed
$ spotiafk run
...
$ spotiafk stats --since 7d
Total playtime: 12h 30m (45000s)
Tracks credited: 1286
  2026-08-24  3h 05m
```

## Configuration

`spotiafk setup` writes `~/.config/spotiafk/config.toml` for you; you rarely edit it by hand. Only four values are required — see [`spotiafk.toml.example`](spotiafk.toml.example) for every option and its default:

```toml
playlist = "AFK"
play_on = ["pi"]

[spotify]
client_id = "..."
client_secret = "..."
```

Optional sections: `[playback]` (`skip_after` seconds per track, minimum 31 so plays count as streams, or `0` to play tracks in full; `shuffle`), `[checks]` (how often and how many idle checks before playing), and `[telegram]` (`bot_token` from [BotFather](https://t.me/BotFather), `chat_id` from [@userinfobot](https://t.me/userinfobot)) for start/stop/error notifications.

A config file in the current directory (`./spotiafk.toml`), a `--config PATH` flag, or `$SPOTIAFK_CONFIG` all override the default location. Tokens, play history, and logs live in `~/.local/share/spotiafk/`.

**Upgrading from v1?** A legacy `options.py` next to the code still works as config, your `token-*.dat` and `time.txt` are migrated automatically on first run, and `python3 spotiAFK.py` still starts it. Run `spotiafk setup` whenever you want to switch to the new config file.

> **What is a "device"?**
>
> Any device that can play music from your Spotify account: your computer, phone, or a Raspberry Pi running `spotifyd` (a great dedicated setup). `play_on` uses the names you see under Spotify's "Connect to a device" icon; `spotiafk setup` shows you the ones currently online to pick from.

## Python API

```python
from spotiafk import Client, Config

client = Client(Config.load())   # or Client() for the default locations
client.run()                     # blocking farm loop
client.status()                  # dict from the run loop's heartbeat
client.stats()                   # Stats(total_seconds, tracks, by_day)
```

## Development

The code lives in the `spotiafk/` package. Install dev tools and run the checks CI runs:

```bash
pip install -e . ruff pytest
ruff check .
pytest
```

<br>

<div align="center">
    <img alt="CI" src="https://github.com/Staninna/SpotiAFK/actions/workflows/ci.yml/badge.svg">
    <img alt="GitHub code size" src="https://img.shields.io/github/languages/code-size/staninna/spotiAFK">
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/Staninna/spotiAFK">
</div>
