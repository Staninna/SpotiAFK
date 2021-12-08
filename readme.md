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

### 1. Configure telegram bot for notifications

1.  Make the bot

    1. Open a dm with [BotFather](https://t.me/BotFather) and click on start

    2. Send a message with the text`/newbot` and follow the instructions

    3. Send a message with the text `/mybots` and select the bot we just created

        - Note that if you want to customize your bot, you can do that also here with `Edit Bot`

    4. Select `API Token` and copy the token and⚠️DON'T SHARE IT WITH ANYONE⚠️

2.  Make `telegram.conf`

    1. In the terminal run<br>
       `sudo python3.9 -m telegram-send -c -g`

    2. Paste your API token you just copied

    3. Send the password to your telegram bot click first on `start`

    4. In the terminal run<br>
       `sudo mv /etc/telegram-send.conf telegram.conf`

### 2. Configure `option.py`

1.  Playing

    |                     | Function                                                                | Default | Format               |
    | ------------------- | ----------------------------------------------------------------------- | ------- | -------------------- |
    | SKIP_SONGS          | If the program skips songs or not                                       | True    | True/False           |
    | SKIP_DELAY          | Amount of time in seconds that the program waits before skipping a song | 35      | All numbers above 30 |
    | RANDOM_ORDER_TRACKS | If the program shuffles the playlist                                    | True    | True/False           |

2.  API

    1. Get your API tokens

        1. Go to the [Spotify developer dashboard](https://developer.spotify.com/dashboard/applications)

        2. Log in with your Spotify account

        3. Click on `create an app`

        4. Pick an `app name` and `app description` of your choice and mark the checkboxes

        5. After creation, you see your `client Id` and you can click on `show client secret` to show your `client secret` and copy them

        6. Click on `edit settings` and add your redirection URL by `redirect uris` than click `save`

    |               | Function                          | Default                         | Format                                           |
    | ------------- | --------------------------------- | ------------------------------- | ------------------------------------------------ |
    | CLIENT_ID     | Spotify application client id     | XXXXX                           | Your client id                                   |
    | CLIENT_SECRET | Spotify application client secret | XXXXX                           | Your client secret                               |
    | REDIRECT_URI  | Your redirect uri                 | http://localhost:8888/callback/ | your redirect URI you added into the spotify API |

3.  Account

    |               | Function                                 | Default                                          | Format                            |
    | ------------- | ---------------------------------------- | ------------------------------------------------ | --------------------------------- |
    | USERNAME      | Your spotify username                    | USERNAME                                         | Your spotify username             |
    | PLAYLIST_NAME | The name of the playlist you want to use | PLAYLIST                                         | Your playlist name                |
    | SERVER_NAMES  | The names of devices you want to use     | ["SERVER-1", "SERVER-2", "SERVER-3", "SERVER-4"] | Python list with names of devices |

4.  Checks

    |                       | Function                                                           | Default | Format              |
    | --------------------- | ------------------------------------------------------------------ | ------- | ------------------- |
    | CHEAKS_BEFORE_PLAYING | Amount of checks if your account is free to use before playing     | 5       | All numbers above 0 |
    | TIME_BETWEEN_CHEAKS   | Amount of time in seconds between cheaks if account is free to use | 35      | All numbers above 0 |

5.  Errors

    |            | Function                                                 | Default | Format              |
    | ---------- | -------------------------------------------------------- | ------- | ------------------- |
    | RETRY_TIME | Amount of time in seconds before retrying after an error | 10      | all numbers above 0 |

6.  Notifications

    |                       | Function                                 | Default       | Format                                |
    | --------------------- | ---------------------------------------- | ------------- | ------------------------------------- |
    | NOTIFICATION_FILENAME | The name of the notification config file | telegram.conf | all files with a extension of `.conf` |
