import json
import logging
import os
import subprocess
import socket

class AudioPlayer:
    def __init__(self, audio_folder="Music", uid_stop="A079401F86"):
        self.audio_folder = audio_folder
        self.uid_stop = uid_stop
        self.audio_process = None
        self.socket_path = "/tmp/mpv-socket" # Chemin pour piloter mpv

    def _send_command(self, *command):
        """Envoie une commande JSON au socket mpv."""
        if not os.path.exists(self.socket_path):
            return False
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)
            data = {"command": list(command)}
            client.send(json.dumps(data).encode('utf-8') + b'\n')
            client.close()
            return True
        except Exception as e:
            logging.error(f"Erreur IPC mpv: {e}")
            return False

    def pause(self):
        """Met la musique en pause sans couper le processus."""
        logging.info("⏸️ Pause demandée")
        self._send_command("set_property", "pause", True)

    def resume(self):
        """Reprend la lecture."""
        logging.info("▶️ Reprise demandée")
        self._send_command("set_property", "pause", False)

    def get_tracks(self):
        with open('UID_TO_TRACK.json', 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        if self.uid_stop in tracks:
            logging.error("❌ UID_STOP est présent dans UID_TO_TRACK.json.")
            exit(1)
        return tracks

    def play_audio(self, audio_path):
        self.stop_song() # Nettoie l'ancien processus et le socket
        
        logging.info(f"▶️ Lancement de mpv avec IPC: {audio_path}")
        # On ajoute --input-ipc-server pour pouvoir faire pause/resume
        self.audio_process = subprocess.Popen(
            [
                "mpv", "--no-video", "--no-terminal", "--really-quiet", 
                f"--volume={os.environ.get('VOLUME', 50)}",
                f"--input-ipc-server={self.socket_path}",
                audio_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_song(self):
        if self.audio_process and self.audio_process.poll() is None:
            logging.info("⏹️ Arrêt complet du processus mpv")
            self.audio_process.terminate()
            try:
                self.audio_process.wait(timeout=2)
            except Exception:
                self.audio_process.kill()
        
        self.audio_process = None
        if os.path.exists(self.socket_path):
            try: os.remove(self.socket_path)
            except: pass

    def play_track(self, track_name):
        track_name_clean = track_name.replace("/", "_").replace(":", "_")
        audio_path = os.path.join(self.audio_folder, track_name_clean)
        if os.path.exists(audio_path):
            self.play_audio(audio_path)
        else:
            logging.warning(f"Fichier introuvable : {audio_path}")

    def close(self):
        self.stop_song()
