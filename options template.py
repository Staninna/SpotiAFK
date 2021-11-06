CLIENT_ID = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"      # Your client_id
CLIENT_SECRET = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Your client_secret

SERVER_NAME = "AFK_SPOTIFY_CLIENT"                  # Name of device that is going to afk
PLAYLIST_NAME = "AFK_PLAYLIST"                      # Name of playlist to grab the songs from
CYCLE_TIME = .5 * 60                                # Time in seconds between music playback checks, when song skip is enabled, likely smooths to 0 
UPDATE_PLAYLIST = 12                                # Time to wait the CYCLE_TIME before updating playlist calculation is (CYCLE_TIME * UPDATE_PLAYLIST)
SKIP_DELAY = 35                                     # Time in seconds to wait till a track gets skips keep in mind only 30+ seconds count as a stream, set to 0 if you don't wanna skip songs
RANDOM_ORDER_SONGS = True                           # Do you want to randomize the playlist

# There also some things i didn't mention in this file about timings becomeing really long depending on your length of your afk playlist and enabling track skipping

# rename tis file to options.py