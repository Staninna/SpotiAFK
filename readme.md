# spotiAFK

<div align="center">
    <img width="80%" src="https://i.imgur.com/VTRXwHa.png">      
</div>

<br>

<div align="center">
    <img alt="GitHub code size" src="https://img.shields.io/github/languages/code-size/staninna/spotiAFK">
    <img alt="GitHub Pipenv locked Python version" src="https://img.shields.io/github/pipenv/locked/python-version/Staninna/spotiAFK">
    <img alt="Lines of code" src="https://img.shields.io/tokei/lines/github/Staninna/spotiAFK">
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/Staninna/spotiAFK">
</div>

## What is it?

It is a simple AFK program that plays Spotify when you are not using your account. To support your favorite artists on the platform.

## How does it work?

It uses the Spotify API to check if you are listening to music and if you don't for a while, it starts playing on a device you specify.

## Setting it up

### Step one: Downloading the program

1. Download the latest version via [this link](https://github.com/Staninna/spotiAFK/releases/latest)

2. And unzip it to the folder where you want to save the programme

### Step two: Setting up the API

1. Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard/) and click on `LOGIN` to login with your Spotify account

<br>

<img alt="LOGIN" src="https://i.imgur.com/IbDnNl0.png">

<br>

2. Click on `CREATE A APP`

<br>

<img alt="CREATE A APP" src="https://i.imgur.com/bbzCqmq.png">

<br>

3. Give it a name, for example `spotiAFK` and a description, for example `Spotify AFK program`

4. Click on `CREATE`

<br>

<img alt="CREATE BUTTON" src="https://i.imgur.com/fF1zRhc.png">

<br>

5. Click `EDIT SETTINGS`

<br>

<img alt="EDIT SETTINGS" src="https://i.imgur.com/COmPVud.png">

<br>

6. Add at Redirect URIs your REDIRECT_URI specified in the `options.py` and click on save

<br>

<img alt="SAVE" src="https://i.imgur.com/wSdtjQP.png">

7. Copy the client id and paste it into `options.py` under `CLIENT_ID`

<br>

<img alt="CLIENT ID" src="https://i.imgur.com/c9HXuwh.png">

<br>

8. Click on `SHOW CLIENT SECRET`

<br>

<img alt="CLIENT SECRET" src="https://i.imgur.com/cQs6KwF.png">

<br>

9.  Copy the client secret and paste it into `options.py` under `CLIENT_SECRET`
    DON'T SHARE THIS WITH ANYONE IT GIVES YOU COMPLETE CONTROL OVER YOUR SPOTIFY ACCOUNT

<br>

<img alt="DUMMY CLIENT SECRET" src="https://i.imgur.com/yxrK0Ua.png">

<br>

### Step tree: Running the program for the first time

1. Go to the folder where you extracted the programme

2. Go to the Configure section on this page and configure `options.py` to your liking

3. Run `pip install spotipy` in the command prompt (cmd.exe) otherwise the program will not work then run `spotiAFK.py` with Python

4. When you run the program for the first time, you will be redirected to a login screen login with your Spotify account

5. If you see this, you have pasted the `CLIENT_ID` incorrectly, correct this in step 2.7 If you don't see this but still get an error message or the console window closes immediately, check your `CLIENT_SECRET` in step 2.9

<br>

<img alt="INCORRECTLY CLIENT ID" src="https://i.imgur.com/LyBmWuo.png">

<br>

6. You may be asked to insert a url in the console window if that happens, copy the url the browser linked to and paste it into the console

7. You are running the program now. ENJOY!!!

## Configuring

`options.py` is the configuration file for this program

### `options.py`

```python
# PLAYING
SKIP_SONGS = True
SKIP_DELAY = 35
RANDOM_ORDER_TRACKS = True
PLAYLIST_NAME = "PLAYLIST"

# API
CLIENT_ID = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
CLIENT_SECRET = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
REDIRECT_URI = "http://localhost:8888/callback/"

# ACCOUNT
USERNAME = "USERNAME"
SERVER_NAMES = ["SERVER-1", "SERVER-2", "SERVER-3", "SERVER-4"]

# CHEAKS
CHEAKS_BEFORE_PLAYING = 5
TIME_BETWEEN_CHEAKS = 30

# ERRORS
RETRY_TIME = 10
```

### Playing

| Options             | Function                                                                   | Default  |
| :------------------ | :------------------------------------------------------------------------- | :------- |
| SKIP_SONGS          | If the program will skip songs after SKIP_DELAY seconds                    | True     |
| SKIP_DELAY          | The amount of seconds to wait before skipping a song if SKIP_SONGS is True | 35       |
| RANDOM_ORDER_TRACKS | If the program will shuffle the playlist                                   | True     |
| PLAYLIST_NAME       | The name of the playlist you wanna use                                     | PLAYLIST |

### API

| Options       | Function                                                   | Default                           |
| :------------ | :--------------------------------------------------------- | :-------------------------------- |
| CLIENT_ID     | The client id found on the Spotify developer dashboard     | Some "X's"                        |
| CLIENT_SECRET | The client secret found on the Spotify developer dashboard | Some "X's"                        |
| REDIRECT_URI  | The uri used to authorize the user                         | `http://localhost:8888/callback/` |

### Account

| Options      | Function                                                   | Default                                          |
| :----------- | :--------------------------------------------------------- | :----------------------------------------------- |
| USERNAME     | Your Spotify username                                      | USERNAME                                         |
| SERVER_NAMES | A list of Spotify connect clients you wanna use as servers | ["SERVER-1", "SERVER-2", "SERVER-3", "SERVER-4"] |

### Cheaks

| Options               | Function                                  | Default |
| :-------------------- | :---------------------------------------- | :------ |
| CHEAKS_BEFORE_PLAYING | Amount of cheaks before playing any songs | 5       |
| TIME_BETWEEN_CHEAKS   | Amount of time between cheaks in seconds  | 30      |

### Errors

| Options    | Function                                                      | Default |
| :--------- | :------------------------------------------------------------ | :------ |
| RETRY_TIME | Amount of time to wait after a error occurred before retrying | 10      |
