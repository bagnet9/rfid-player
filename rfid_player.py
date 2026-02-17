import shutil
import signal
import threading
import os
import logging
import RPi.GPIO as GPIO
import time
from AudioPlayer import AudioPlayer
from RFIDReader import RFIDReader
import argparse

# Configuration Moteur & Capteur Hall
IN1, IN2, IN3, IN4 = 14, 15, 18, 23
PINS_MOTEUR = [IN1, IN2, IN3, IN4]
SENSOR_PIN = 17
SEQ_HALF_STEP = [
    [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
    [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1],
]
STEP_DELAY = 0.0015

UID_STOP = "A079401F86"
audio_folder = "Music"
stop_event = threading.Event()
motor_run = threading.Event()

signal.signal(signal.SIGINT, lambda s, f: stop_event.set())

def set_step(values):
    for pin, val in zip(PINS_MOTEUR, values):
        GPIO.output(pin, val)

def motor_worker():
    i = 0
    while not stop_event.is_set():
        if motor_run.is_set():
            set_step(SEQ_HALF_STEP[i])
            i = (i + 1) % len(SEQ_HALF_STEP)
            time.sleep(STEP_DELAY)
        else:
            set_step([0, 0, 0, 0])
            time.sleep(0.1)

def main():
    logging.info("🔍 DÉBUT DU SCRIPT (RFID + HALL PAUSE/RESUME)")

    # ... (Garde ton bloc argparse ici)

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS_MOTEUR: GPIO.setup(pin, GPIO.OUT, initial=0)
    GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    audio_player = None
    rfid_reader = None
    current_uid = None

    try:
        audio_player = AudioPlayer(audio_folder, UID_STOP)
        rfid_reader = RFIDReader()

        def sync_state():
            """Applique pause/resume et moteur selon l'état du capteur Hall."""
            nonlocal current_uid
            hall_active = (GPIO.input(SENSOR_PIN) == 0) # Détecté si 0
            
            if current_uid and current_uid != UID_STOP:
                if hall_active:
                    audio_player.resume()
                    motor_run.set()
                else:
                    audio_player.pause()
                    motor_run.clear()

        def on_uid_detected(uid_str):
            nonlocal current_uid
            UID_TO_TRACK = audio_player.get_tracks()
            
            if uid_str == UID_STOP:
                current_uid = None
                audio_player.stop_song()
                motor_run.clear()
            elif uid_str in UID_TO_TRACK:
                current_uid = uid_str
                audio_player.play_track(UID_TO_TRACK[uid_str])
                # Après lancement, on vérifie si on doit mettre en pause direct
                sync_state()
            else:
                logging.warning(f"UID non reconnu : {uid_str}")

        # Interruption Capteur Hall
        GPIO.add_event_detect(SENSOR_PIN, GPIO.BOTH, callback=lambda ch: sync_state(), bouncetime=50)

        # Thread Moteur
        threading.Thread(target=motor_worker, daemon=True).start()

        rfid_reader.readCallback = on_uid_detected
        rfid_reader.stop_event = stop_event
        rfid_reader.handle_uid_detection()

    finally:
        stop_event.set()
        motor_run.clear()
        if audio_player: audio_player.close()
        if rfid_reader: rfid_reader.close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
