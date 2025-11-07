import shutil
import signal
import threading
import os
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
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(logging.INFO)

    # check if mpv is installed
    if shutil.which("mpv") is None:
        logging.error("❌ mpv is not installed. Please install with 'sudo apt install mpv'")
        exit(1)

    audio_player = None
    rfid_reader = None

    try:
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

        logging.info("🚀 Starting RFID loop")
        rfid_reader.handle_uid_detection()

    except Exception:
        logging.exception("Unhandled exception in main loop")
    finally:
        logging.info("🧹 Performing cleanup")
        try:
            if audio_player:
                audio_player.close()
        except Exception:
            logging.exception("AudioPlayer.close failed")
        try:
            if rfid_reader:
                rfid_reader.close()
        except Exception:
            logging.exception("RFIDReader.close failed")
        logging.info("🛑 End of execution")

if __name__ == "__main__":
    main()