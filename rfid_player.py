import json
import signal
import time
import os
import subprocess
import logging
from mfrc522 import MFRC522
import RPi.GPIO as GPIO
import argparse
import mmap
# 🔊 Config log
logging.basicConfig(
    filename="rfid_player.log",
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

logging.info("🔍 DÉBUT DU SCRIPT PYTHON")

logging.info("🚀 Script RFID lancé via systemd")
"""
argument :
--volume : volume de lecture (0-100)
--print_logs : afficher les logs dans la console
"""

parser = argparse.ArgumentParser()
parser.add_argument("--volume", type=int, default=50)
parser.add_argument("--print_logs", action="store_true")
args = parser.parse_args()
volume = args.volume
if args.print_logs:
    logging.getLogger().setLevel(logging.INFO)
    # set logging output to both file and console
    logging.getLogger().addHandler(logging.StreamHandler())

# check if mpv is installed
if not subprocess.run(["which", "mpv"], stdout=subprocess.DEVNULL).returncode == 0:
    logging.error("❌ mpv n'est pas installé. Veuillez l'installer avec 'sudo apt install mpv'")
    exit(1)

continue_reading = True

logging.info("🎬 Script RFID démarré")

UID_TO_TRACK = json.load(open("UID_TO_TRACK.json"))

UID_STOP = "A079401F86"

# check that UID_STOP is not in UID_TO_TRACK
if UID_STOP in UID_TO_TRACK.values():
    logging.error("❌ UID_STOP est présent dans UID_TO_TRACK.json, veuillez le retirer.")
    exit(1)

audio_folder = "Music"

def end_read(signal, frame):
    global continue_reading
    logging.info("🛑 Arrêt du script demandé (CTRL+C)")
    continue_reading = False
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)

reader = MFRC522()
dernier_uid = None
delai = 2

audio_process = None


def play_audio(audio_path):
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()

    # Lecture avec mpv
    logging.info("▶️ Appel à mpv")
    audio_process = subprocess.Popen(
        ["mpv", "--no-video", "--no-terminal", "--really-quiet", f"--volume={volume}", audio_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    logging.info("🎧 mpv lancé")


def stop_song():
    global audio_process
    if audio_process and audio_process.poll() is None:
        logging.info("⏹️ Arrêt de la musique en cours")
        audio_process.terminate()
        audio_process = None
    else:
        logging.info("Aucune musique en cours à arrêter")


def play_track():
    track_name = UID_TO_TRACK[uid_str]
    track_name_clean = track_name.replace("/", "_").replace(":", "_")
    audio_path = os.path.join(audio_folder, track_name_clean)
    if os.path.exists(audio_path):
        logging.info(f"🎵 Lecture du fichier : {audio_path}")
        play_audio(audio_path)
    else:
        logging.warning(f"Fichier introuvable : {audio_path}")


def wait_for_release():
    while True:
        (status_check, _) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status_check != reader.MI_OK:
            break
        time.sleep(0.1)


def handle_uid_detection(mm,f):
    global uid_str
    while continue_reading:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                uid_str = "".join(f"{x:02X}" for x in uid)
                logging.info(f"🎴 UID détecté : {uid_str}")
                mm.seek(0)
                mm.write(uid_str.encode('utf-8') + b'\0')
                mm.flush()
                if uid_str == UID_STOP:
                    stop_song()
                elif uid_str in UID_TO_TRACK:
                    play_track()
                else:
                    logging.warning(f"UID non reconnu : {uid_str}")
            wait_for_release()


with open('shared_data.dat', 'w+b') as f:
    f.write(b'\0' * 1024)
    f.flush()
    with mmap.mmap(f.fileno(), 1024) as mm:
        handle_uid_detection(mm,f)
