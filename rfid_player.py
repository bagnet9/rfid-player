import signal
import threading
import os
import subprocess
import logging
from AudioPlayer import AudioPlayer
from RFIDReader import RFIDReader
import argparse

# 🔊 Config log
logging.basicConfig(
    filename="rfid_player.log",
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

UID_STOP = "A079401F86"
audio_folder = "Music"
stop_event = threading.Event()

signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

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

    audio_player = AudioPlayer(audio_folder, UID_STOP)
    rfid_reader = RFIDReader()
    UID_TO_TRACK = audio_player.get_tracks()
    def on_uid_detected(uid_str):
        if uid_str == UID_STOP:
            audio_player.stop_song()
        elif uid_str in UID_TO_TRACK:
            audio_player.play_track(UID_TO_TRACK[uid_str])
        else:
            logging.warning(f"UID non reconnu : {uid_str}")
            rfid_reader.wait_for_release()
    rfid_reader.readCallback = on_uid_detected
    rfid_reader.stop_event = stop_event
    rfid_reader.handle_uid_detection()
    # after loop ends -> perform cleanup once
    audio_player.close()
    rfid_reader.close()
    logging.info("🛑 End of execution")

if __name__ == "__main__":
    main()