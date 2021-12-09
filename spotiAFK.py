# Imports
import os
import sys
import time
import random
import options
import spotipy
import logging
import datetime
import requests
import telegram_send

# Variables

# API variables
USERNAME = options.USERNAME
CLIENT_ID = options.CLIENT_ID
CLIENT_SECRET = options.CLIENT_SECRET
REDIRECT_URI = options.REDIRECT_URI
TOKEN_PATH = f"{os.path.dirname(os.path.realpath(__file__))}/token-{USERNAME}.dat" 
SCOPE = "user-modify-playback-state playlist-read-private user-read-playback-state"

# App variables
NOTIFICATION_FILENAME = options.NOTIFICATION_FILENAME
SERVER_NAMES = options.SERVER_NAMES
PLAYLIST_NAME = options.PLAYLIST_NAME
TIME_BETWEEN_CHEAKS = options.TIME_BETWEEN_CHEAKS
CHEAKS_BEFORE_PLAYING = options.CHEAKS_BEFORE_PLAYING
RANDOM_ORDER_TRACKS = options.RANDOM_ORDER_TRACKS
SKIP_SONGS = options.SKIP_SONGS
SKIP_DELAY = options.SKIP_DELAY
RETRY_TIME = options.RETRY_TIME
TIMELOG_FILENAME = options.TIMELOG_FILENAME

# Classes

# API class
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
             retry_time : float,
             lost_time  : float) -> None:
        while True:
            try:
                if hasattr(self, 'token'):
                    old_token = self.token
                else:
                    old_token = str()
                    log(logging.INFO, "Getting token for first time")
                self.token = spotipy.prompt_for_user_token(self.username,
                                                        self.scope,
                                                        self.client_id,
                                                        self.client_secret,
                                                        self.redirect_uri,
                                                        self.tokens_path)
                if old_token != self.token:
                    log(logging.INFO, f"New token is {self.token}")
                else:
                    log(logging.INFO, "Tried to renew token but token was still valid")
                self.client = spotipy.Spotify(self.token)
                break
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                log(logging.INFO, "No internet connection found while trying to get authenticated")
                lost_time += RETRY_TIME
                time.sleep(retry_time)
                log(logging.INFO, "Retrying to get authenticated")
        return lost_time

# Functions

# Check if program can play
def can_i_play(succes_checks    : int,
               retry_time       : float,
               lost_time        : float):  
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
            log(logging.INFO, "No internet connection found while checking if server could play tracks")
            lost_time += RETRY_TIME
            time.sleep(retry_time)
            log(logging.INFO, "Retrying checking if server could play tracks")
    return succes_checks, lost_time

# Update the playlist
def update_playlist(retry_time  : float,
                    lost_time   : float):
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
            log(logging.INFO, "Updated playlist")
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            log(logging.INFO, "No internet connection found while checking if server could play tracks")
            lost_time += RETRY_TIME
            time.sleep(retry_time)
            log(logging.INFO, "Retrying checking if server could play tracks")
    return tracks_to_play, lost_time

# Get ids of play servers
def get_server_ids(lost_time):
    server_ids = list()
    while True:
        try:
            devices = Spotify.client.devices()
            for device in devices["devices"]:
                if device["name"] in SERVER_NAMES:
                    server_id = device["id"]
                    server_ids.append(server_id)
                    log(logging.INFO, f"Server named {server_id} found")
            if "server_id" not in locals():
                log(logging.INFO, f"The servers {SERVER_NAMES} were not found")
                lost_time += RETRY_TIME
                time.sleep(RETRY_TIME)
                log(logging.INFO, "Retrying getting server ids")
            else:
                break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            log(logging.INFO, "No internet connection found updating playlist")
            lost_time += RETRY_TIME
            time.sleep(RETRY_TIME)
            log(logging.INFO, "Retrying updateing playlist")
    return server_ids, lost_time

# Loggin to a file
def log(level, 
        message):
    print(message)
    logging.log(level, message)

# Code

# Send notification that program is starting
telegram_send.send(messages=[f"{str(datetime.datetime.now()).split('.')[0]}: INFO: Starting program..."], conf=NOTIFICATION_FILENAME)

# Making log file
if not os.path.isdir("logs"):
    os.mkdir("logs")
date = datetime.datetime.now()
logging.basicConfig(filename=f"logs/{date.day}-{date.month}-{date.year}_{date.hour}-{date.minute}-{date.second}.log",
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s",
                    datefmt='%d/%m/%Y %H:%M:%S:'
                    )
log(logging.INFO, "Started the program")

# Making time log file
if not os.path.isfile(TIMELOG_FILENAME):
    with open(TIMELOG_FILENAME,"w") as f:
        f.write("0")

# Make spotify API object
Spotify = API(CLIENT_ID,
              CLIENT_SECRET,
              REDIRECT_URI,
              USERNAME,
              SCOPE,
              TOKEN_PATH)

# First auth
lost_time = Spotify.auth(RETRY_TIME, 0)

# Some variables
server_ids, lost_time = get_server_ids(lost_time)
succes_checks = 0
retries = 0
played = False
last_message_send = None

# Main loop
while True:
    try:

        # Testing x times before playing songs
        time.sleep(TIME_BETWEEN_CHEAKS)
        succes_checks, lost_time = can_i_play(succes_checks, RETRY_TIME, lost_time)
        log(logging.INFO, f"Checked if i could play success rate is [{succes_checks}/{CHEAKS_BEFORE_PLAYING}]")
        if played:
            played = False
        
        # Main play loop
        while succes_checks >= CHEAKS_BEFORE_PLAYING:
            
            # If not logged that program is playing do so
            if not played:
                log(logging.INFO, "Started playing tracks")
                start_playing_time = time.time()
                lost_time = 0
                if last_message_send != "Started playing track":
                    telegram_send.send(messages=[f"{str(datetime.datetime.now()).split('.')[0]}: INFO: Started playing track"], conf=NOTIFICATION_FILENAME, silent=True)
                    last_message_send = "Started playing track"
                played = True
            
            # Transfering playback to server
            while True:
                try:
                    Spotify.client.transfer_playback(server_ids[0], False)
                    break
                except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                    log(logging.INFO, "No internet connection found while transfering playback to server")
                    lost_time += RETRY_TIME
                    time.sleep(RETRY_TIME)
                    log(logging.INFO, "Retrying transfering playback to server")
            
            # Getting all songs from the afk playlist
            tracks, lost_time = update_playlist(RETRY_TIME, lost_time)
            
            # Looping over songs
            for track, duration, name in tracks:
                if can_i_play(0, RETRY_TIME, lost_time)[0] == 0:
                    log(logging.INFO, "Stopped playing tracks")
                    with open(TIMELOG_FILENAME, "r") as f:
                        total_time = str(float(f.readline()) + (time.time() - start_playing_time) - lost_time)
                    with open(TIMELOG_FILENAME, "w") as f:
                        f.write(total_time)
                    if last_message_send != "Stopped playing tracks":
                        telegram_send.send(messages=[f"{str(datetime.datetime.now()).split('.')[0]}: INFO: Stopped playing tracks"], conf=NOTIFICATION_FILENAME, silent=True)
                        last_message_send = "Stopped playing tracks"
                    break
                
                # Add song to queue
                while True:
                    try:
                        Spotify.client.add_to_queue(track)
                        break
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                        log(logging.INFO, "No internet connection found while adding track to queue")
                        lost_time += RETRY_TIME
                        time.sleep(RETRY_TIME)
                        log(logging.INFO, "Retrying adding track to queue")
                
                # Play the song
                while True:
                    try:
                        Spotify.client.next_track()
                        break
                    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                        log(logging.INFO, "No internet connection found while skipping track")
                        lost_time += RETRY_TIME
                        time.sleep(RETRY_TIME)
                        log(logging.INFO, "Retrying skipping track")
                
                # Wait till song is done
                if SKIP_SONGS:
                    time.sleep(SKIP_DELAY)
                else:
                    time.sleep(duration)
                log(logging.INFO, f"Played {name}")
            
            # If looped over all songs wait
            time.sleep(TIME_BETWEEN_CHEAKS)
            succes_checks, lost_time = can_i_play(succes_checks, RETRY_TIME, lost_time)
    
    
    # Reset and log some things on a error
    except Exception as e:
        # DEBUG
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log(logging.ERROR, f"{e}:::{exc_type}:::{fname}:::{exc_tb.tb_lineno}")
        telegram_send.send(messages=[f"{e}:::{exc_type}:::{fname}:::{exc_tb.tb_lineno}"], conf=NOTIFICATION_FILENAME)
        # DEBUG
        while True:
            try:
                if not "The access token expired, reason: None" in str(e):
                    telegram_send.send(messages=[f"{str(datetime.datetime.now()).split('.')[0]}: ERROR: {str(e)}"], conf=NOTIFICATION_FILENAME)
                log(logging.ERROR, e)
                time.sleep(RETRY_TIME * (retries + 1))
                lost_time = Spotify.auth(RETRY_TIME, lost_time)
                server_ids, lost_time = get_server_ids(lost_time)
                tracks, lost_time = update_playlist(RETRY_TIME, lost_time)
                retries = 0
                break
            except Exception as e:
                # DEBUG
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log(logging.ERROR, f"{e}:::{exc_type}:::{fname}:::{exc_tb.tb_lineno}")
                telegram_send.send(messages=[f"{e}:::{exc_type}:::{fname}:::{exc_tb.tb_lineno}"], conf=NOTIFICATION_FILENAME)
                # DEBUG
                retries += 1
                if not "The access token expired, reason: None" in str(e):
                    telegram_send.send(messages=[f"{str(datetime.datetime.now()).split('.')[0]}: ERROR: {str(e)}"], conf=NOTIFICATION_FILENAME)
                log(logging.ERROR, e)
                time.sleep(RETRY_TIME * (retries + 1))      
