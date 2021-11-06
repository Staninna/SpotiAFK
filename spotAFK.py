# CLIENT SECRETS
import secrets

import spotipy, os, json

class SpotifyAPI(object):
    client_id = None
    client_secret = None
    redirect_uri = None
    username = None
    scope = None
    tokens_path = None
    
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

client_id = secrets.CLIENT_ID
client_secret = secrets.CLIENT_SECRET
redirect_uri = "http://localhost:8888/callback/"
username = "Staninna"
scope = "user-read-currently-playing user-modify-playback-state playlist-read-private user-read-private user-read-playback-state"
tokens_path = f"{os.path.dirname(os.path.realpath(__file__))}/token.dat"
Spotify = SpotifyAPI(client_id,
                     client_secret,
                     redirect_uri,
                     username,
                     scope,
                     tokens_path)


# SETTINGS

SERVER_NAME = "AFK_SPOTIFY_CLIENT"
PLAYLIST_NAME = "AFK_PLAYLIST"
PLAYLIST_LIMIT = 50

# LOGIC CODE

Spotify.auth()

devices = Spotify.client.devices()
device_found = False
for device in devices["devices"]:
    if device["name"] == SERVER_NAME:
        device_found = True
        device_id = device["id"]
        device_name = device["name"]
        break
if not device_found:
    raise Exception("Your selected device does not exist or is offline")

total_playlists = Spotify.client.current_user_playlists(limit=0)["total"]
offset = 0
playlist_found = False
while offset != total_playlists:
    playlists = Spotify.client.current_user_playlists(limit=PLAYLIST_LIMIT, offset=offset)["items"]
    for playlist in playlists:
        if playlist["name"] == PLAYLIST_NAME:
            playlist_found = True
            offset = total_playlists
            playlist_id = playlist["id"]
            playlist_name = playlist["name"]
            break
        offset += 1
if not playlist_found:
    raise Exception("Your selected playlist does not exist")

playing = Spotify.client.current_user_playing_track()["is_playing"]
