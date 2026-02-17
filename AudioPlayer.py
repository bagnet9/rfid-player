import json
import logging
import os
import mpv

class AudioPlayer:
    def __init__(self, audio_folder="Music", uid_stop="A079401F86"):
        self.audio_folder = audio_folder
        self.uid_stop = uid_stop
        self.player = mpv.MPV(
            video=False,
            ytdl=False,
            terminal=False,
            log_handler=logging.debug,
            input_default_bindings=True,
            input_vo_keyboard=True,
            volume=int(os.environ.get('VOLUME', 50))
        )

    def pause(self):
        """Met la musique en pause."""
        logging.info("⏸️ Pause demandée")
        self.player.pause = True

    def resume(self):
        """Reprend la lecture."""
        logging.info("▶️ Reprise demandée")
        self.player.pause = False

    def get_tracks(self):
        with open('UID_TO_TRACK.json', 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        if self.uid_stop in tracks:
            logging.error("❌ UID_STOP est présent dans UID_TO_TRACK.json.")
            exit(1)
        return tracks

    def play_audio(self, audio_path):
        logging.info(f"▶️ Lancement de mpv : {audio_path}")
        self.player.play(audio_path)

    def stop_song(self):
        logging.info("⏹️ Arrêt de la lecture")
        self.player.stop()

    def play_track(self, track_name):
        track_name_clean = track_name.replace("/", "_").replace(":", "_")
        audio_path = os.path.join(self.audio_folder, track_name_clean)
        if os.path.exists(audio_path):
            self.play_audio(audio_path)
        else:
            logging.warning(f"Fichier introuvable : {audio_path}")

    def close(self):
        self.player.terminate()
