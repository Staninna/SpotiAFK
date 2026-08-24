"""The spotiafk command line: setup, run, status, stats, doctor.

Exit codes: 0 ok, 1 runtime error, 2 usage error, 3 invalid config,
4 auth failure, 5 not running (status).
"""

import argparse
import datetime
import getpass
import json
import os
import re
import sys

import spotipy

from spotiafk import stats as stats_module
from spotiafk.client import Client, setup_logging
from spotiafk.config import DEFAULT_REDIRECT_URI, Config, ConfigError, default_config_path
from spotiafk.spotify import make_client

EXIT_OK, EXIT_ERROR, EXIT_CONFIG, EXIT_AUTH, EXIT_NOT_RUNNING = 0, 1, 3, 4, 5


def _parse_since(text: str) -> datetime.datetime:
    match = re.fullmatch(r"(\d+)([dhm])", text)
    if not match:
        raise argparse.ArgumentTypeError("use a number plus d/h/m, e.g. 7d, 24h, 30m")
    amount, unit = int(match[1]), match[2]
    delta = {"d": "days", "h": "hours", "m": "minutes"}[unit]
    return datetime.datetime.now() - datetime.timedelta(**{delta: amount})


def _load_config(args) -> Config:
    return Config.load(args.config)


def cmd_run(args) -> int:
    cfg = _load_config(args)
    setup_logging(cfg)
    Client(cfg).run()
    return EXIT_OK


def cmd_status(args) -> int:
    status = Client(_load_config(args)).status()
    if args.json:
        print(json.dumps(status))
    elif not status["live"]:
        print("Not running.")
        if status.get("state") not in (None, "not running", "stopped"):
            print(f"(last seen {status.get('age_seconds')}s ago in state '{status['state']}')")
    else:
        line = f"Running — {status['state']}"
        if status.get("track"):
            line += f", track: {status['track']}"
        if status.get("checks"):
            line += f", idle checks: {status['checks']}"
        print(line + f" (heartbeat {status['age_seconds']}s ago, pid {status.get('pid')})")
    return EXIT_OK if status["live"] else EXIT_NOT_RUNNING


def cmd_stats(args) -> int:
    result = Client(_load_config(args)).stats(since=args.since)
    if args.json:
        print(json.dumps(result.as_dict()))
        return EXIT_OK
    print(f"Total playtime: {stats_module.format_duration(result.total_seconds)}"
          f" ({int(result.total_seconds)}s)")
    if result.tracks:
        print(f"Tracks credited: {result.tracks}")
    for day in sorted(result.by_day)[-7:]:
        print(f"  {day}  {stats_module.format_duration(result.by_day[day])}")
    return EXIT_OK


def cmd_doctor(args) -> int:
    def ok(msg):
        print(f"  ✓ {msg}")

    def bad(msg, hint):
        print(f"  ✗ {msg}\n    fix: {hint}")

    try:
        cfg = _load_config(args)
    except ConfigError as error:
        bad("no usable configuration", str(error))
        return EXIT_CONFIG
    ok(f"config loaded from {cfg.source}")

    problems = cfg.issues()
    for problem in problems:
        bad(problem, "edit the config or re-run 'spotiafk setup'")
    if problems:
        return EXIT_CONFIG

    try:
        client = make_client(cfg)
    except Exception as error:
        bad(f"Spotify auth failed: {error}", "check client_id/client_secret and redirect_uri")
        return EXIT_AUTH
    user = client.current_user()
    ok(f"authenticated as {user.get('display_name') or user['id']}")

    from spotiafk.spotify import find_playlist_id

    if find_playlist_id(client, cfg.playlist) is None:
        bad(f"playlist {cfg.playlist!r} not found", "check the name or re-run 'spotiafk setup'")
        return EXIT_ERROR
    ok(f"playlist {cfg.playlist!r} found")

    online = [d["name"] for d in client.devices()["devices"]]
    matched = [name for name in cfg.play_on if name in online]
    if matched:
        ok(f"devices online: {', '.join(matched)}")
    else:
        bad(
            f"none of {list(cfg.play_on)} are online (online now: {online or 'none'})",
            "open Spotify on the device, or fix play_on in the config",
        )
        return EXIT_ERROR
    ok("all checks passed")
    return EXIT_OK


def _pick(prompt: str, names: list) -> str:
    for index, name in enumerate(names, 1):
        print(f"  {index}. {name}")
    while True:
        answer = input(f"{prompt} [number or name]: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            return names[int(answer) - 1]
        if answer in names:
            return answer
        print("Not one of the options, try again.")


def cmd_setup(args) -> int:
    print("SpotiAFK setup — takes about 3 minutes.\n")
    print("1/4 Spotify app credentials")
    print("    Create an app at https://developer.spotify.com/dashboard (tick Web API),")
    print(f"    add this redirect URI in its settings: {DEFAULT_REDIRECT_URI}")
    client_id = input("    Client ID: ").strip()
    client_secret = getpass.getpass("    Client secret (hidden): ").strip()

    cfg = Config(client_id=client_id, client_secret=client_secret)
    print("\n2/4 Logging in to Spotify (follow the URL it prints)...")
    try:
        client = make_client(cfg)
    except Exception as error:
        print(f"Authorization failed: {error}", file=sys.stderr)
        return EXIT_AUTH
    user = client.current_user()
    print(f"    Hi {user.get('display_name') or user['id']}!")

    print("\n3/4 Which playlist should SpotiAFK play?")
    playlists = []
    page = client.current_user_playlists()
    while page and len(playlists) < 50:
        playlists += [p["name"] for p in page["items"] if p]
        page = client.next(page) if page["next"] else None
    playlist = _pick("Playlist", playlists)

    print("\n4/4 Play on which device? (must be online now to appear)")
    devices = [d["name"] for d in client.devices()["devices"]]
    play_on = [_pick("Device", devices)] if devices else []
    if not devices:
        print("    No devices online; set play_on in the config later.")

    telegram_lines = ""
    if input("\nTelegram notifications? [y/N] ").strip().lower().startswith("y"):
        token = getpass.getpass("    Bot token (hidden, from BotFather): ").strip()
        chat_id = input("    Chat id (message @userinfobot for it): ").strip()
        telegram_lines = (
            f"\n[telegram]\nbot_token = {json.dumps(token)}\nchat_id = {json.dumps(chat_id)}\n"
        )

    path = args.config or default_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(
            f"playlist = {json.dumps(playlist)}\n"
            f"play_on = {json.dumps(play_on)}\n\n"
            f"[spotify]\n"
            f"client_id = {json.dumps(client_id)}\n"
            f"client_secret = {json.dumps(client_secret)}\n"
            + telegram_lines
        )
    os.chmod(path, 0o600)
    print(f"\nWrote {path} (kept private with chmod 600).")
    print("All set! Start with: spotiafk run")
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="spotiafk",
        description="Plays a Spotify playlist on your devices while you're away.",
    )
    parser.add_argument("--config", help="path to spotiafk.toml (default: standard locations)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("setup", help="guided first-time setup").set_defaults(func=cmd_setup)
    sub.add_parser("run", help="start farming (blocking; Ctrl-C stops)").set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="is it running, and what is it doing")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_stats = sub.add_parser("stats", help="total playtime and per-day breakdown")
    p_stats.add_argument("--since", type=_parse_since, help="window like 7d, 24h, 30m")
    p_stats.add_argument("--json", action="store_true")
    p_stats.set_defaults(func=cmd_stats)

    sub.add_parser("doctor", help="check config, auth, playlist, and devices").set_defaults(
        func=cmd_doctor
    )

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as error:
        print(f"spotiafk: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except spotipy.oauth2.SpotifyOauthError as error:
        print(f"spotiafk: authentication failed: {error}", file=sys.stderr)
        return EXIT_AUTH
    except KeyboardInterrupt:
        return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
