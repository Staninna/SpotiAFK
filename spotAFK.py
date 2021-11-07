# CLIENT SECRETS
import options

import spotipy, os, time, random, json

class SpotifyAPI(object):
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
             pickled : bool = True) -> None:
        """Function that authorizes your class

        Args:
            pickled (bool, optional): Defines if token get saved as plain text or not. Defaults to True.
        """
        if pickled:
            import pickle
            if os.path.isfile(self.tokens_path):
                with open(self.tokens_path, "rb") as token_file:
                    token = pickle.load(token_file)
                    token_file.close()
                with open(self.tokens_path, "w") as token_file:
                    json.dump(token, token_file)
                    token_file.close()
                self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_uri, self.tokens_path,)
                pickle.dump(token, open(self.tokens_path, "wb", pickle.HIGHEST_PROTOCOL))
            else:
                self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_uri, self.tokens_path,)
                with open(self.tokens_path) as token_file:
                    cache = json.load(token_file)
                    token_file.close()
                pickle.dump(cache, open(self.tokens_path, "wb", pickle.HIGHEST_PROTOCOL))
        else:
            self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_uri, self.tokens_path,)
        self.client = spotipy.Spotify(auth=self.token)

client_id = options.CLIENT_ID
client_secret = options.CLIENT_SECRET
redirect_uri = "http://localhost:8888/callback/"
username = "Staninna"
scope = "user-modify-playback-state playlist-read-private user-read-playback-state"
tokens_path = f"{os.path.dirname(os.path.realpath(__file__))}/token.dat"
Spotify = SpotifyAPI(client_id,
                     client_secret,
                     redirect_uri,
                     username,
                     scope,
                     tokens_path)
Spotify.auth()


# SETTINGS

SERVER_NAMES = options.SERVER_NAMES
PLAYLIST_NAME = options.PLAYLIST_NAME
TIME_BETWEEN_CHEAKS = options.TIME_BETWEEN_CHEAKS
CHEAKS_BEFORE_PLAYING = options.CHEAKS_BEFORE_PLAYING
RANDOM_ORDER_TRACKS = options.RANDOM_ORDER_TRACKS
SKIP_SONGS = options.SKIP_SONGS
SKIP_DELAY = options.SKIP_DELAY


# CODE

# FUNCTIONS

def can_i_play(succes_checks):
    try:
        if Spotify.client.current_user_playing_track()["is_playing"]:  
                for device in Spotify.client.devices()["devices"]:
                    if device["is_active"]:
                        if device["name"] in SERVER_NAMES:
                            succes_checks += 1
                        else:
                            succes_checks = 0
        else:
            succes_checks += 1
    except TypeError:
        succes_checks += 1
    return succes_checks

def update_playlist():
    playlists = Spotify.client.current_user_playlists()
    for playlist in playlists["items"]:
        if playlist["name"] == PLAYLIST_NAME:
            tracks = Spotify.client.playlist(playlist["id"])["tracks"]
            tracks_to_play = list()
            while tracks:
                for track in tracks["items"]:
                    duration_sec = track["track"]["duration_ms"] / 1000
                    uri = track["track"]["uri"]
                    tracks_to_play.append([uri, duration_sec])
                if tracks["next"]:
                    tracks = Spotify.client.next(tracks)
                else:
                    tracks = None
            break
    if RANDOM_ORDER_TRACKS:
        random.shuffle(tracks_to_play)
    return tracks_to_play

# Get Server ids
devices = Spotify.client.devices()
for device in devices["devices"]:
    if device["name"] == SERVER_NAMES:
        server_id = device["id"]

succes_checks = 0
# MAIN LOOP
while True:
    try:
        time.sleep(TIME_BETWEEN_CHEAKS)
        succes_checks = can_i_play(succes_checks)
        while succes_checks >= CHEAKS_BEFORE_PLAYING:
            Spotify.client.transfer_playback(server_id, False)
            tracks = update_playlist()
            for track, duration in tracks:
                if can_i_play(0) == 0:
                    break
                Spotify.client.add_to_queue(track)
                Spotify.client.next_track()
                if SKIP_SONGS:
                    time.sleep(SKIP_DELAY)
                else:
                    time.sleep(duration)
            time.sleep(TIME_BETWEEN_CHEAKS)
            succes_checks = can_i_play(succes_checks)
    except Exception as e:
        print(e)
