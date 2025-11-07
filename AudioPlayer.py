import json
import logging
import os
import subprocess

from rfid_player import audio_folder


class AudioPlayer:
    def __init__(self,audio_folder="Music", uid_stop="A079401F86"):
        self.audio_folder = audio_folder
        self.uid_stop = uid_stop
        self.audio_process = None

    def get_tracks(self):
        tracks = json.load(open("UID_TO_TRACK.json"))
        # check that UID_STOP is not in UID_TO_TRACK
        if self.uid_stop in tracks.values():
            logging.error("❌ UID_STOP est présent dans UID_TO_TRACK.json, veuillez le retirer.")
            exit(1)
        return tracks

    def play_audio(self,audio_path):
        if self.audio_process and self.audio_process.poll() is None:
            self.audio_process.terminate()

        # Lecture avec mpv
        logging.info("▶️ Appel à mpv")
        audio_process = subprocess.Popen(
            ["mpv", "--no-video", "--no-terminal", "--really-quiet", f"--volume={os.environ["VOLUME"]}", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info("🎧 mpv lancé")

    def stop_song(self):
        if self.audio_process and self.audio_process.poll() is None:
            logging.info("⏹️ Arrêt de la musique en cours")
            self.audio_process.terminate()
            self.audio_process = None
        else:
            logging.info("Aucune musique en cours à arrêter")

    def play_track(self,track_name):
        track_name_clean = track_name.replace("/", "_").replace(":", "_")
        audio_path = os.path.join(audio_folder, track_name_clean)
        if os.path.exists(audio_path):
            logging.info(f"🎵 Lecture du fichier : {audio_path}")
            self.play_audio(audio_path)
        else:
            logging.warning(f"Fichier introuvable : {audio_path}")

    def close(self):
        if self.audio_process and self.audio_process.poll() is None:
            self.audio_process.terminate()
