# spotiAFK

<div align="center">
    <img width="80%" src="https://i.imgur.com/VTRXwHa.png">
</div>

## What is it?

It is a simple AFK program that plays Spotify when you are not using your account. To support your favorite artists on the platform.

## How does it work?

It uses the Spotify API to check if you are listening to music and if you don't for a while, it starts playing on a device you specify.

## Setting it up

The fastest way is the interactive wizard, which walks you through the Spotify app, your account details, and the optional Telegram bot, and writes `options.py` and `telegram.conf` for you:

```bash
./scripts/setup-wizard.sh
```

Prefer to do it by hand? Follow the steps below.

### 1. Configure telegram bot for notifications

1.  Make the bot

    1. Open a dm with [BotFather](https://t.me/BotFather) and click on start

    2. Send a message with the text `/newbot` and follow the instructions

    3. Send a message with the text `/mybots` and select the bot we just created

        - Note that if you want to customize your bot, you can do that also here with `Edit Bot`

    4. Select `API Token` and copy the token and<br>
       ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️<br>
       DON'T SHARE THOSE STRINGS WITH ANYONE<br>
       ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

2.  Make `telegram.conf`

    1. Copy the template: `cp telegram.conf.example telegram.conf`

    2. Fill in your bot token and chat id (get your chat id by messaging [@userinfobot](https://t.me/userinfobot)), or generate the file with `python3 -m telegram_send --configure --config telegram.conf` and follow the instructions

    3. Keep it private: `chmod 600 telegram.conf`

    > `telegram.conf`, your Spotify token cache, `logs/` and `time.txt` are all in `.gitignore` so credentials and runtime output never get committed.

    Don't want notifications? Set `NOTIFICATION_ENABLED = False` in `options.py` and skip this step.

### 2. Configure `options.py`

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

        5. After creation, you see your `client Id` and you can click on `show client secret` to show your `client secret` and copy them<br>
           ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️<br>
           DON'T SHARE THOSE STRINGS WITH ANYONE<br>
           ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

        6. Click on `edit settings` and add your redirection URL by `redirect uris` than click `save`

    |               | Function                          | Default                         | Format                                           |
    | ------------- | --------------------------------- | ------------------------------- | ------------------------------------------------ |
    | CLIENT_ID     | Spotify application client id     | XXXXX                           | Your client id                                   |
    | CLIENT_SECRET | Spotify application client secret | XXXXX                           | Your client secret                               |
    | REDIRECT_URI  | Your redirect uri                 | http://localhost:8888/callback/ | Your redirect URI you added into the spotify API |

3.  Account

    |               | Function                                 | Default                                          | Format                            |
    | ------------- | ---------------------------------------- | ------------------------------------------------ | --------------------------------- |
    | USERNAME      | Your spotify username                    | USERNAME                                         | Your spotify username             |
    | PLAYLIST_NAME | The name of the playlist you want to use | PLAYLIST                                         | Your playlist name                |
    | SERVER_NAMES  | The names of devices you want to use     | ["SERVER-1", "SERVER-2", "SERVER-3", "SERVER-4"] | Python list with names of devices |

    > **What is a "server"?**
    >
    > In this application, a "server" is any device (like your computer, phone, or smart speaker) that can play music from your Spotify account.
    >
    > You need to tell the script which device to use by editing the `SERVER_NAMES` list in `options.py`. To find the correct name for your device, open the Spotify app, click on the "Connect to a device" icon, and use the name you see there.
    >
    > **Hint:** A great way to use this is with a Raspberry Pi running `spotifyd`. This allows you to have a dedicated, low-power device to act as a "server" without needing speakers connected to it.

4.  Checks

    |                       | Function                                                           | Default | Format              |
    | --------------------- | ------------------------------------------------------------------ | ------- | ------------------- |
    | CHECKS_BEFORE_PLAYING | Amount of checks if your account is free to use before playing     | 5       | All numbers above 0 |
    | TIME_BETWEEN_CHECKS   | Amount of time in seconds between checks if account is free to use | 30      | All numbers above 0 |

5.  Errors

    |            | Function                                                 | Default | Format              |
    | ---------- | -------------------------------------------------------- | ------- | ------------------- |
    | RETRY_TIME | Amount of time in seconds before retrying after an error | 10      | All numbers above 0 |

6.  Notifications

    |                              | Function                                                         | Default             | Format                                |
    | ---------------------------- | ---------------------------------------------------------------- | ------------------- | ------------------------------------- |
    | NOTIFICATION_ENABLED         | If notifications are sent at all                                 | True                | True/False                            |
    | NOTIFICATION_FILENAME        | The name of the notification config file                         | telegram.conf       | Any string preferred with a extension |
    | UPDATE_PLAYLIST_NOTIFICATION | Text of notification when the playlist is refreshed              | Updated playlist 🎵 | Any string                            |
    | START_PROGRAM_NOTIFICATION   | Text of notification when program starts                         | Starting program 🏁 | Any string                            |
    | START_PLAYING_NOTIFICATION   | Text of notification when the music starts playing on the server | Started playing 🟩  | Any string                            |
    | STOP_PLAYING_NOTIFICATION    | Text of notification when the music stops playing on the server  | Stopped playing 🟥  | Any string                            |
    | SEND_NOTIFICATION_ON_ERROR   | If you want an error notification                                | True                | True/False                            |

7.  Timelogging

    |                  | Function                     | Default  | Format                                |
    | ---------------- | ---------------------------- | -------- | ------------------------------------- |
    | TIMELOG_FILENAME | The name of the timelog file | time.txt | Any string preferred with a extension |

### 3. Running the program

1.  **Install dependencies:**

    ```bash
    pipenv install
    ```

2.  **Run the script:**

    ```bash
    pipenv run python3 spotiAFK.py
    ```

    Or use the restarter scripts, which relaunch the program automatically if it crashes (a clean Ctrl-C stops it for good):

    ```bash
    ./restarter.sh        # Linux/macOS
    restarter.bat         # Windows
    ```

The program writes its logs to `logs/` and the total played time (in seconds) to `time.txt`, both next to the script.

## Development

The code lives in the `spotiafk/` package; `spotiAFK.py` is just the entry point. Install the dev tools with `pipenv install --dev`, then:

```bash
pipenv run pytest        # run the test suite
pipenv run ruff check .  # lint
```

CI runs both on every push and pull request.

<br>

<div align="center">
    <img alt="GitHub code size" src="https://img.shields.io/github/languages/code-size/staninna/spotiAFK">
    <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/Staninna/spotiAFK">
</div>
