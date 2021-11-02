# CLIENT SECRETS
import secrets

import spotipy, os, pickle, json

class API(object):

    def __init__(self,
                 client_id      : str,
                 client_secret  : str,
                 username       : str,
                 scope          : str,
                 redirect_url   : str,
                 cache_path     : str,) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.scope = scope
        self.redirect_url = redirect_url
        self.cache_path = cache_path
    
    def auth(self,
             pickled : bool = True) -> None:
        if pickled:
            if os.path.isfile(self.cache_path):
                with open(self.cache_path, "rb") as cache_file:
                    cache = pickle.load(cache_file)
                    cache_file.close()
                with open(self.cache_path, "w") as cache_file:
                    json.dump(cache, cache_file)
                    cache_file.close()
                self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_url, self.cache_path,)
                pickle.dump(cache, open(self.cache_path, "wb", pickle.HIGHEST_PROTOCOL))
            else:
                self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_url, self.cache_path,)
                with open(self.cache_path) as cache_file:
                    cache = json.load(cache_file)
                    cache_file.close()
                pickle.dump(cache, open(self.cache_path, "wb", pickle.HIGHEST_PROTOCOL))
        else:
            self.token = spotipy.util.prompt_for_user_token(self.username, self.scope, self.client_id, self.client_secret, self.redirect_url, self.cache_path,)

client_id = secrets.CLIENT_ID
client_secret = secrets.CLIENT_SECRET
username = "Staninna"
scope = "user-read-currently-playing user-modify-playback-state playlist-read-private user-read-private user-read-playback-state"
redirect_url = "https://localhost:8080/callback/"
cache_path = f"{os.path.dirname(os.path.realpath(__file__))}/cache.dat"

spotify = API(client_id, client_secret, username, scope, redirect_url, cache_path)

spotify.auth()
token = spotify.token
spotifyObject = spotipy.Spotify(token)

devices = spotifyObject.devices()
print(json.dumps(devices, sort_keys=True, indent=4))