#!/usr/bin/env python3
# /home/yassin/rfid_player2.py

import os
import sys
import time
import signal
import shutil
import subprocess
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "/home/yassin/rfid_player.log"

# --- Logging setup en premier ---
logger = logging.getLogger("rfid_player")
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("🔍 DÉBUT DU SCRIPT PYTHON (rfid_player2)")

# --- Imports matériels protégés ---
GPIO = None
MFRC522 = None
hw_ok = True

try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    logger.info("✅ Import RPi.GPIO réussi")
except Exception as e:
    hw_ok = False
    logger.error(f"❌ Erreur import RPi.GPIO : {e}")

try:
    from mfrc522 import MFRC522 as MFRC522_cls
    MFRC522 = MFRC522_cls
    logger.info("✅ Import MFRC522 réussi")
except Exception as e:
    hw_ok = False
    logger.error(f"❌ Erreur import MFRC522 : {e}")

if not hw_ok:
    logger.critical("🔥 Dépendances matérielles manquantes. Arrêt.")
    sys.exit(1)

# --- Mapping RFID → fichiers ---
UID_TO_TRACK = {
    "5DCF3F1FB2": "N_est-ce-pas-rossi.mp3",
    "ECDA401F69": "Abderrahman-Soudais_001.mp3",
    "3DD03F1FCD": "Abderrahman-Soudais_002.mp3",
    "7DC5401FE7": "Abderrahman-Soudais_003.mp3",
    "FD01401FA3": "Abderrahman-Soudais_004.mp3",
    "90F83F1F48": "Abderrahman-Soudais_005.mp3",
    # ... autres cartes ...
}

UID_STOP = "A079401F86"
AUDIO_DIR = "/home/yassin/Music"
MPG123_BIN = shutil.which("mpg123") or "/usr/bin/mpg123"

if not os.path.exists(MPG123_BIN):
    logger.critical(f"❌ mpg123 introuvable à {MPG123_BIN}. Installe-le: sudo apt-get install mpg123")
    sys.exit(1)

continue_reading = True
audio_process = None
dernier_uid = None

def stop_audio():
    global audio_process
    if audio_process and audio_process.poll() is None:
        logger.info("⏹️ Arrêt de la musique en cours")
        try:
            audio_process.terminate()
            try:
                audio_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Forçage kill de mpg123")
                audio_process.kill()
        except Exception as e:
            logger.error(f"Erreur à l'arrêt audio: {e}")
    audio_process = None

def end_read(signum=None, frame=None):
    global continue_reading
    logger.info("🛑 Arrêt demandé (signal reçu)")
    continue_reading = False

# Signal (utile si lancé manuellement)
signal.signal(signal.SIGINT, end_read)
signal.signal(signal.SIGTERM, end_read)

def main():
    global continue_reading, dernier_uid, audio_process

    reader = MFRC522()
    logger.info("🎬 Script RFID démarré")

    while continue_reading:
        try:
            status, tag_type = reader.MFRC522_Request(reader.PICC_REQIDL)
            if status == reader.MI_OK:
                status, uid = reader.MFRC522_Anticoll()
                if status == reader.MI_OK and uid:
                    uid_str = "".join(f"{x:02X}" for x in uid)
                    logger.info(f"🎴 UID détecté : {uid_str}")

                    if uid_str != dernier_uid:
                        dernier_uid = uid_str

                        if uid_str == UID_STOP:
                            stop_audio()

                        elif uid_str in UID_TO_TRACK:
                            track = UID_TO_TRACK[uid_str]
                            audio_path = os.path.join(AUDIO_DIR, track)

                            if os.path.exists(audio_path):
                                logger.info(f"🎵 Lecture du fichier : {audio_path}")

                                # Stopper l'éventuel morceau en cours
                                stop_audio()

                                
                                # Volume (optionnel)
                                try:
                                     subprocess.run(["amixer", "sset", "Master", "50%"], check=True)
                                except Exception as e:
                                     logging.warning(f"Erreur volume (amixer) : {e}")
                                
                                # Lancer mpg123 (silencieux côté stdout/err)
                                try:
                                    logger.info("▶️ Appel à mpg123")
                                    audio_process = subprocess.Popen(
                                        [MPG123_BIN, "-q", audio_path],  # -q = quiet
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                                    )
                                    logger.info("🎧 mpg123 lancé (PID %s)", audio_process.pid)
                                except Exception as e:
                                    logger.error(f"❌ Erreur lancement mpg123 : {e}")
                                    audio_process = None
                            else:
                                logger.warning(f"Fichier introuvable : {audio_path}")
                        else:
                            logger.warning(f"UID non reconnu : {uid_str}")

                        # Attendre que la carte soit retirée
                        while True:
                            status_check, _ = reader.MFRC522_Request(reader.PICC_REQIDL)
                            if status_check != reader.MI_OK:
                                break
                            time.sleep(0.1)
            else:
                # Pas de carte → micro-sommeil
                time.sleep(0.05)

        except Exception as e:
            logger.exception(f"💥 Exception dans la boucle principale: {e}")
            time.sleep(0.2)

    # Fin propre
    try:
        stop_audio()
    finally:
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception as e:
            logger.warning(f"GPIO.cleanup() a échoué: {e}")
        logger.info("👋 Sortie propre du script.")

if __name__ == "__main__":
    main()
