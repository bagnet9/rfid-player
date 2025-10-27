import json
import signal
import time
import os
import subprocess
import logging
from mfrc522 import MFRC522
import RPi.GPIO as GPIO

# 🔊 Config log
logging.basicConfig(
    filename="rfid_player.log",
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

logging.info("🔍 DÉBUT DU SCRIPT PYTHON")

logging.info("🚀 Script RFID lancé via systemd")

# check if mpv is installed
if not subprocess.run(["which", "mpv"], stdout=subprocess.DEVNULL).returncode == 0:
    logging.error("❌ mpv n'est pas installé. Veuillez l'installer avec 'sudo apt install mpv'")
    exit(1)

continue_reading = True

volume = 50
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


def PlayAudio(audio_path):
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


while continue_reading:
    (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

    if status == reader.MI_OK:
        (status, uid) = reader.MFRC522_Anticoll()

        if status == reader.MI_OK:
            uid_str = "".join(f"{x:02X}" for x in uid)
            logging.info(f"🎴 UID détecté : {uid_str}")

            if uid_str != dernier_uid:
                dernier_uid = uid_str

                if uid_str == UID_STOP:
                    if audio_process and audio_process.poll() is None:
                        logging.info("⏹️ Arrêt de la musique en cours")
                        audio_process.terminate()
                        audio_process = None
                    else:
                        logging.info("Aucune musique en cours à arrêter")

                elif uid_str in UID_TO_TRACK:
                    track_name = UID_TO_TRACK[uid_str]
                    audio_path = os.path.join(audio_folder, track_name)

                    if os.path.exists(audio_path):
                        logging.info(f"🎵 Lecture du fichier : {audio_path}")

                        PlayAudio(audio_path)

                    elif 'http' in track_name or 'https' in track_name:
                        logging.info(f"🌐 Lecture du flux en ligne : {track_name}")
                        # TODO : cache the music for offline use
                        PlayAudio(track_name)
                    else:
                        logging.warning(f"Fichier introuvable : {audio_path}")
                else:
                    logging.warning(f"UID non reconnu : {uid_str}")

                # Attendre que la carte soit retirée avant de continuer
                while True:
                    (status_check, _) = reader.MFRC522_Request(reader.PICC_REQIDL)
                    if status_check != reader.MI_OK:
                        break
                    time.sleep(0.1)
