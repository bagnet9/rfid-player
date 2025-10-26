import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import signal
import time
import os
import subprocess

continue_reading = True

# 🎵 Associe les UID aux fichiers audio
UID_TO_TRACK = {
    932076331178: "N_est-ce-pas-rossi.mp3",
    2362186431105: "La_Reine_des_Neiges_-_Je_voudrais_un_bonhomme_de_neige_I_Disney.mp3",
    # Ajoute autant de cartes que tu veux ici
}

# 🛑 UID spécial pour arrêter la musique
UID_STOP = 1601216431134  # Remplace ceci par l'UID réel de ta carte "STOP"

# 📁 Dossier contenant les fichiers audio
audio_folder = "/home/yassin/Music"

# 🛑 Capture CTRL+C pour quitter proprement
def end_read(signal, frame):
    global continue_reading
    print("\nArrêt du script.")
    continue_reading = False
    GPIO.cleanup()

signal.signal(signal.SIGINT, end_read)

reader = MFRC522()
dernier_uid = None
delai = 2  # anti-repétition

audio_process = None  # Processus VLC en cours

print("Approche une carte RFID...")

while continue_reading:
    (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

    if status == reader.MI_OK:
        print("Carte détectée.")
        (status, uid) = reader.MFRC522_Anticoll()

        if status == reader.MI_OK:
            # UID sous forme d'entier unique
            uid_int = int("".join([str(i) for i in uid]))

            if uid_int != dernier_uid:
                print(f"UID détecté : {uid_int}")
                dernier_uid = uid_int

                # 🔻 Carte STOP
                if uid_int == UID_STOP:
                    if audio_process and audio_process.poll() is None:
                        print("⏹️ Arrêt de la musique (VLC).")
                        audio_process.terminate()
                        audio_process = None
                    else:
                        print("Aucune musique en cours.")

                # 🎵 Carte musique
                elif uid_int in UID_TO_TRACK:
                    track_name = UID_TO_TRACK[uid_int]
                    audio_path = os.path.join(audio_folder, track_name)

                    if os.path.exists(audio_path):
                        print(f"Lecture de : {audio_path}")

                        # Stop musique en cours si besoin
                        if audio_process and audio_process.poll() is None:
                            audio_process.terminate()

                        # Lance VLC en mode console
                        subprocess.run(["amixer", "sset", "Master", "50%"])
                        audio_process = subprocess.Popen(
                            ["cvlc", "--play-and-exit", audio_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        
                    else:
                        print(f"Fichier introuvable : {audio_path}")
                else:
                    print(f"UID non reconnu : {uid_int}")

                time.sleep(delai)
