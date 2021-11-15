# Imports
import os
import time
import random
import options
import spotipy
import logging
import datetime
import requests

# API Class
class API(object):
    def __init__(self,
                 client_id      : str,
                 client_secret  : str,
                 redirect_uri   : str,
                 username       : str,
                 scope          : str,
                 tokens_path    : str,
                 ) -> None:
        """Set-up SpotifyAPI class

        Args:
            client_id (str): Your Client ID of your app
            client_secret (str): Your Client secret of your app
            redirect_uri (str): The redirect uri you set in your aoo
            username (str): Your spotify username
            scope (str): The scopes you want to use in your class
            tokens_path (str): Path to the directory/file you want to save your token(s)
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.username = username
        self.scope = scope
        self.tokens_path = tokens_path
    
    def auth(self,
             retry_time : float) -> None:
        while True:
            try:
                if hasattr(self, 'token'):
                    old_token = self.token
                else:
                    old_token = str()
                    logging.info("Getting token for first time")
                self.token = spotipy.prompt_for_user_token(self.username,
                                                        self.scope,
                                                        self.client_id,
                                                        self.client_secret,
                                                        self.redirect_uri,
                                                        self.tokens_path)
                if old_token != self.token:
                    logging.info(f"New token is {self.token}")
                else:
                    logging.info("Tried to renew token but")
                self.client = spotipy.Spotify(self.token)
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                logging.info("No internet connection found while trying to get authenticated")
                time.sleep(retry_time)
                logging.info("Retrying to get authenticated")

# TODO IDK WHAT YET

client_id = options.CLIENT_ID
client_secret = options.CLIENT_SECRET
redirect_uri = "http://localhost:8888/callback/"
username = "Staninna"
scope = "user-modify-playback-state playlist-read-private user-read-playback-state"
token_path = f"{os.path.dirname(os.path.realpath(__file__))}/token-{username}.dat"
Spotify = API(client_id,
              client_secret,
              redirect_uri,
              username,
              scope,
              token_path)


# SETTINGS

SERVER_NAMES = options.SERVER_NAMES
PLAYLIST_NAME = options.PLAYLIST_NAME
TIME_BETWEEN_CHEAKS = options.TIME_BETWEEN_CHEAKS
CHEAKS_BEFORE_PLAYING = options.CHEAKS_BEFORE_PLAYING
RANDOM_ORDER_TRACKS = options.RANDOM_ORDER_TRACKS
SKIP_SONGS = options.SKIP_SONGS
SKIP_DELAY = options.SKIP_DELAY
RETRY_TIME = options.RETRY_TIME

# Code

# Functions
def can_i_play(succes_checks    : int,
               retry_time       : float,):
    while True:
        try:
            if Spotify.client.current_user_playing_track()["is_playing"]:  
                    for device in Spotify.client.devices()["devices"]:
                        if device["is_active"]:
                            if device["name"] in SERVER_NAMES:
                                succes_checks += 1
                                break
                            else:
                                succes_checks = 0
                                break
            else:
                succes_checks += 1
            break
        except TypeError:
            succes_checks += 1
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logging.info("No internet connection found while checking if server could play tracks")
            time.sleep(retry_time)
            logging.info("Retrying checking if server could play tracks")
    return succes_checks

def update_playlist(retry_time  : float):
    while True:
        try:
            playlists = Spotify.client.current_user_playlists()
            for playlist in playlists["items"]:
                if playlist["name"] == PLAYLIST_NAME:
                    tracks = Spotify.client.playlist(playlist["id"])["tracks"]
                    tracks_to_play = list()
                    while tracks:
                        for track in tracks["items"]:
                            duration_sec = track["track"]["duration_ms"] / 1000
                            uri = track["track"]["uri"]
                            name = track["track"]["name"]
                            tracks_to_play.append([uri, duration_sec, name])
                        if tracks["next"]:
                            tracks = Spotify.client.next(tracks)
                        else:
                            tracks = None
                    break
            if RANDOM_ORDER_TRACKS:
                random.shuffle(tracks_to_play)
            logging.info("Updated playlist")
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logging.info("No internet connection found while checking if server could play tracks")
            time.sleep(retry_time)
            logging.info("Retrying checking if server could play tracks")
    return tracks_to_play

def get_server_ids():
    server_ids = list()
    while True:
        try:
            devices = Spotify.client.devices()
            for device in devices["devices"]:
                if device["name"] in SERVER_NAMES:
                    server_id = device["id"]
                    server_ids.append(server_id)
                    logging.info(f"Server named {server_id} found")
            if "server_id" not in locals():
                logging.info(f"The servers {SERVER_NAMES} were not found")
                exit()
            else:
                break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logging.info("No internet connection found updating playlist")
            time.sleep(RETRY_TIME)
            logging.info("Retrying updateing playlist")
    return server_ids

def log(level, 
        message):
    print(message)
    logging.log(level, message)

# Making Log File
if not os.path.isdir("logs"):
    os.mkdir("logs")
date = datetime.datetime.now()
logging.basicConfig(filename=f"logs/{date.day}-{date.month}-{date.year}_{date.hour}-{date.minute}-{date.second}.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt='%d/%m/%Y %H:%M:%S:'
                    )
log(logging.INFO, "Started the program")

# Auth
Spotify.auth(RETRY_TIME)

server_ids = get_server_ids()

# Main loop
succes_checks = 0
played = False
while True:
    try:
        time.sleep(TIME_BETWEEN_CHEAKS)
        succes_checks = can_i_play(succes_checks, RETRY_TIME)
        if played:
            played = False
        while succes_checks >= CHEAKS_BEFORE_PLAYING:
            if not played:
                log(logging.INFO, "Started playing tracks")
                played = True
            while True:
                try:
                    Spotify.client.transfer_playback(server_ids[0], False)
                    break
                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                    log(logging.INFO, "No internet connection found while transfering playback to server")
                    time.sleep(RETRY_TIME)
                    log(logging.INFO, "Retrying transfering playback to server")
            tracks = update_playlist(RETRY_TIME)
            for track, duration, name in tracks:
                if can_i_play(0, RETRY_TIME) == 0:                    
                    log(logging.INFO, "Stopped playing tracks")
                    break
                while True:
                    try:
                        Spotify.client.add_to_queue(track)
                        break
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                        log(logging.INFO, "No internet connection found while adding track to queue")
                        time.sleep(RETRY_TIME)
                        log(logging.INFO, "Retrying adding track to queue")
                while True:
                    try:
                        Spotify.client.next_track()
                        break
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                        log(logging.INFO, "No internet connection found while skipping track")
                        time.sleep(RETRY_TIME)
                        log(logging.INFO, "Retrying skipping track")
                if SKIP_SONGS:
                    time.sleep(SKIP_DELAY)
                else:
                    time.sleep(duration)
                log(logging.INFO, f"Played {name}")
            time.sleep(TIME_BETWEEN_CHEAKS)
            succes_checks = can_i_play(succes_checks, RETRY_TIME)
    except Exception as e:
        time.sleep(RETRY_TIME)
        log(logging.ERROR, e)
        Spotify.auth(RETRY_TIME)
        server_ids = get_server_ids()
