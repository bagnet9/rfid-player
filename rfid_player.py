import json
import signal
import threading
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

UID_STOP = "A079401F86"
audio_folder = "Music"
stop_event = threading.Event()
try:
    reader = MFRC522()
except Exception as e:
    logging.exception("Failed to initialize MFRC522: %s", e)
    raise

def get_tracks():
    tracks = json.load(open("UID_TO_TRACK.json"))
    # check that UID_STOP is not in UID_TO_TRACK
    if UID_STOP in tracks.values():
        logging.error("❌ UID_STOP est présent dans UID_TO_TRACK.json, veuillez le retirer.")
        exit(1)
    return tracks

def play_audio(audio_path):
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()

    # Lecture avec mpv
    logging.info("▶️ Appel à mpv")
    audio_process = subprocess.Popen(
        ["mpv", "--no-video", "--no-terminal", "--really-quiet", f"--volume={os.environ["VOLUME"]}", audio_path],
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

def play_track(track_name):
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

def read_uid():
    (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
    if status == reader.MI_OK:
        (status, uid) = reader.MFRC522_Anticoll()
        if status == reader.MI_OK:
            uid_str = "".join(f"{x:02X}" for x in uid)
            return uid_str
    return None

def handle_uid_detection(mm,f):
    while not stop_event.is_set():
        uid_str = read_uid()
        if not uid_str:
            wait_for_release()
            continue
        logging.info(f"🎴 UID détecté : {uid_str}")
        mm.seek(0)
        mm.write(uid_str.encode('utf-8') + b'\0')
        mm.flush()
        UID_TO_TRACK = get_tracks()
        if uid_str == UID_STOP:
            stop_song()
        elif uid_str in UID_TO_TRACK:
            play_track(UID_TO_TRACK[uid_str])
        else:
            logging.warning(f"UID non reconnu : {uid_str}")
            wait_for_release()

signal.signal(signal.SIGINT, lambda s, f: stop_event.set())



audio_process = None



def main():
    logging.info("🔍 DÉBUT DU SCRIPT PYTHON")

    logging.info("🚀 Script RFID lancé via systemd")

    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, default=50)
    parser.add_argument("--print_logs", action="store_true")
    args = parser.parse_args()
    os.environ["VOLUME"] = str(args.volume)
    if args.print_logs:
        logging.getLogger().setLevel(logging.INFO)
        # set logging output to both file and console
        logging.getLogger().addHandler(logging.StreamHandler())

    # check if mpv is installed
    if not subprocess.run(["which", "mpv"], stdout=subprocess.DEVNULL).returncode == 0:
        logging.error("❌ mpv is not installed. Please install with 'sudo apt install mpv'")
        exit(1)

    with open('shared_data.dat', 'w+b') as f:
        f.write(b'\0' * 1024)
        f.flush()
        with mmap.mmap(f.fileno(), 1024) as mm:
            handle_uid_detection(mm,f)
            # after loop ends -> perform cleanup once
            if audio_process and audio_process.poll() is None:
                audio_process.terminate()
            try:
                GPIO.cleanup()
            except Exception:
                logging.exception("GPIO cleanup failed")
    logging.info("🛑 End of execution")

if __name__ == "__main__":
    main()