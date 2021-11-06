# CLIENT SECRETS
import options

import spotipy, os, time, random

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
            import pickle, json
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


# SETTINGS

SERVER_NAME = options.SERVER_NAME
PLAYLIST_NAME = options.PLAYLIST_NAME
CYCLE_TIME = options.CYCLE_TIME
UPDATE_PLAYLIST = options.UPDATE_PLAYLIST
RANDOM_ORDER_SONGS = options.RANDOM_ORDER_SONGS
SKIP_DELAY = options.SKIP_DELAY

# FUNCTIONS

def can_i_play() -> list:
    devices = Spotify.client.devices()
    active_devices = 0
    for device in devices["devices"]:
        if device["name"] == SERVER_NAME:
            server_id = device["id"]
        if device["is_active"]:
            active_devices += 1
        else:
            pass
    if active_devices > 0 and Spotify.client.current_user_playing_track()["is_playing"]:
        return [False, "dQw4w9WgXcQ"]
    else:
        return [True, server_id]

def update_playlist() -> list:
    playlists = Spotify.client.current_user_playlists()
    playlist_found = False
    while playlists:
        for playlist in playlists["items"]:
            if playlist["name"] == PLAYLIST_NAME:
                playlist_found = True
                tracks = Spotify.client.playlist(playlist["id"])["tracks"]
                if len(tracks["items"]) == 0:
                    raise Exception("Playlist doesn't coinain any tracks to AFK")
                playlist_track_uris = list()
                while tracks:
                    for track in tracks["items"]:
                        playlist_track_uris.append(track["track"]["uri"])
                    if tracks["next"]:
                        tracks = Spotify.client.next(tracks)
                    else:
                        tracks = None
                break
        if playlist_found:
            break
        elif playlists["next"]:
            playlists = Spotify.client.next(playlists)
        else:
            playlists = None
    if not playlist_found:
        raise Exception("Your selected playlist does not exist")
    return playlist_track_uris

Spotify.auth()

# MAIN LOOP
while True:
    playlist = update_playlist()
    length_playlist = len(playlist)
    print("update")
    if RANDOM_ORDER_SONGS:
        random.shuffle(playlist)
    for i in range(UPDATE_PLAYLIST):
        can_play, device_id = can_i_play()
        print("check")
        if can_play:
            print("play")
            Spotify.client.start_playback(device_id=device_id, uris=playlist)
            for _ in range(len(playlist)):
                if SKIP_DELAY != 0:
                    print("skip")
                    time.sleep(SKIP_DELAY)
                    Spotify.client.next_track()
        time.sleep((abs((CYCLE_TIME - (len(playlist) * SKIP_DELAY))) + (CYCLE_TIME - (len(playlist) * SKIP_DELAY))) / 2)
