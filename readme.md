# RFID Player

A Raspberry Pi-based RFID music player. When an RFID tag is presented to an MFRC522 reader, a mapped audio track is played using `mpv`. A simple Flask web UI lets you view the last scanned UID, upload tracks, and map UIDs to tracks.

## Table of Contents
- [Overview](#overview)
- [Stack](#stack)
- [Requirements](#requirements)
- [Setup](#setup)
- [Running](#running)
- [Scripts](#scripts)
- [Environment Variables](#environment-variables)
- [Configuration](#configuration)
- [Project Structure](#project-structure)

## Overview
- RFID reader: MFRC522 on Raspberry Pi (SPI)
- Audio playback: `mpv` (no video)
- Web UI: Flask app to upload/select tracks and manage UID➔track mapping
- Shared state: a small memory-mapped file (`shared_data.dat`) communicates the last scanned UID from the RFID service to the web UI
- Mapping file: `UID_TO_TRACK.json` stores UID→filename mappings

Main components:
- `rfid_player.py` — long-running process that reads UIDs from the MFRC522, writes last UID to `shared_data.dat`, and plays associated tracks with `mpv`
- `main_web.py` — Flask server exposing a UI (at `/`) to show the last UID, upload music to `Music/`, and assign a track to that UID


## Stack
- Language: Python 3
- Frameworks/Libraries:
  - Flask (web UI)
  - `mfrc522-python` (MFRC522 reader)
  - `RPi.GPIO` (GPIO access; system package on Raspberry Pi)
  - `mmap` (standard library) for shared state
- Web server: Flask development server; optional `gunicorn` (present in `requirements.txt`)
- Package manager: `pip` (requirements in `requirements.txt`)


## Requirements
Software:
- Python 3.9+ (earlier 3.x likely fine; tested version not pinned)  
- System packages on Raspberry Pi:
  - `mpv` media player (used by `rfid_player.py`)
  - `python3-rpi.gpio` (or available via `pip install RPi.GPIO` on Raspberry Pi OS)
  - SPI enabled (via `raspi-config`)

Python dependencies (install via `pip`):
- See `requirements.txt`:
  - `Flask`
  - `gunicorn` (optional, for production WSGI server)
  - `mmap` (note: `mmap` is part of the Python standard library; the entry here may not be necessary on all systems)

Hardware:
- Raspberry Pi with SPI enabled
- MFRC522 RFID reader wired to Raspberry Pi SPI pins
- Speaker/Audio output connected to the Pi (for `mpv` playback)


## Setup
1. Enable SPI on the Raspberry Pi:
   - `sudo raspi-config` → Interface Options → SPI → Enable
2. Install system packages:
   - `sudo apt update`
   - `sudo apt install -y mpv python3-pip python3-dev python3-rpi.gpio`
3. Clone this repository and change into it:
   - `git clone <your-repo-url> && cd rfid-player`
4. (Recommended) Create and activate a virtual environment:
   - `python3 -m venv .venv && source .venv/bin/activate`
5. Install Python dependencies:
   - `pip install --upgrade pip`
   - `pip install -r requirements.txt`
6. Prepare directories and files:
   - Ensure `Music/` exists (it is included). Put `.mp3` files here or use the web UI to upload.
   - Ensure `UID_TO_TRACK.json` exists (present). It stores UID→filename mappings.


## Running
There are two processes:
1) RFID service (`rfid_player.py`)
2) Web UI (`main_web.py`)

Run RFID service (needs hardware and `mpv`):
- Development/manual:
  - `python rfid_player.py --volume 50 --print_logs`
  - Requires root or appropriate group permissions for SPI/GPIO. If needed, run with `sudo`.

Run Web UI (development server):
- `python main_web.py`
- By default runs at `http://0.0.0.0:8080` (debug mode enabled in script).

Run Web UI with gunicorn (recommended without Flask debug):
- `gunicorn -b 0.0.0.0:8080 main_web:app`

Recommended command for gunicorn:
- `gunicorn -b 0.0.0.0:8080 main_web:app --timeout 300 --log-level info --reload > uvicorn.log 2>&1 &`
Explanation :
    - `--timeout 300` : request timeout to kill worker processes if stuck
    - `--log-level info` : logging level (debug is too verbose)
    - `--reload` : auto-reload on code changes, to not have to restart the server after each change
    - Redirect output to `uvicorn.log` and run in background (`&`) to keep the terminal clean and keep a log of the server's output.

Notes:
- The RFID service writes the last scanned UID into `shared_data.dat` via `mmap`. The Flask app reads it on each page load to show the current UID and propose mapping.
- Audio files must be placed in `Music/`. The Flask app also supports upload at `/upload`.
- The mapping file `UID_TO_TRACK.json` is updated via POST to `/change_music`.


## Scripts
- `autopull.sh` — checks for upstream changes and pulls updates periodically. Usage: `./autopull.sh <interval>`.


## Environment Variables
- Currently, there are no explicit environment variables consumed by the code. The music folder is defined in `main_web.py` as `app.config['MUSIC_FOLDER'] = './Music'`.
- TODO: Consider supporting an env var like `MUSIC_FOLDER` to override the default.
- TODO: Consider supporting an env var like `UID_TO_TRACK_FILE` to override the default.
- TODO: Consider supporting an env var like `UID_STOP` to override the default.

## Configuration
- Mapping stop UID: in `rfid_player.py`, `UID_STOP = "A079401F86"` stops playback when that tag is presented. Ensure it does not conflict with `UID_TO_TRACK.json` (script enforces this).
- Volume: pass `--volume <0-100>` to `rfid_player.py`.
- Logs: `rfid_player.py` writes to `rfid_player.log`; use `--print_logs` to also log to console.


## Project Structure
```
Music/
  <audio files...>
UID_TO_TRACK.json
autopull.sh
main_web.py               # Flask web UI
mfrc522/
  MFRC522.py
  SimpleMFRC522.py
  __init__.py
readme.md                 # This file
requirements.txt
rfid_player.py            # RFID reader + audio player
shared_data.dat           # Memory-mapped shared file (created/used at runtime)
templates/
  index.html              # Web UI template
```


## Deployment (optional)
You can run both services under `systemd` so they start on boot.

Example unit for the RFID service (`/etc/systemd/system/rfid-player.service`):
```
[Unit]
Description=RFID Player Service
After=network.target sound.target

[Service]
Type=simple
WorkingDirectory=/home/pi/rfid-player
ExecStart=/usr/bin/python3 /home/pi/rfid-player/rfid_player.py --volume 50
Restart=on-failure
# Grant access to SPI/GPIO as needed; consider using a non-root user in the gpio/spi groups.

[Install]
WantedBy=multi-user.target
```

Example unit for the Web UI (`/etc/systemd/system/rfid-player-web.service`):
```
[Unit]
Description=RFID Player Web UI
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/pi/rfid-player
ExecStart=/usr/bin/env gunicorn -b 0.0.0.0:8080 main_web:app --timeout 300 --log-level info --reload
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start:
```
sudo systemctl daemon-reload
sudo systemctl enable rfid-player.service rfid-player-web.service
sudo systemctl start rfid-player.service rfid-player-web.service
```


## Troubleshooting
- `ModuleNotFoundError: No module named 'RPi'` — ensure `python3-rpi.gpio` (APT) or `pip install RPi.GPIO` is installed on Raspberry Pi.
- `mpv` not found — install with `sudo apt install mpv`.
- MFRC522 not detected — verify wiring and that SPI is enabled via `raspi-config`.
- Audio not playing — check volume level, audio output device on the Pi, and that the mapped file exists in `Music/`.
- Permission errors on SPI/GPIO — run under a user in `gpio`/`spi` groups or use `sudo` (prefer groups for security).


## License
- TODO: Add license information (no license file found in the repository).


## Acknowledgements
- Uses `mfrc522-python` for RFID reader support. TODO : Add a sub repository instead of using copy/pasted code.
