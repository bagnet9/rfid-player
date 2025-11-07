import logging
import mmap
import time

from mfrc522 import MFRC522
from rfid_player import stop_event
import RPi.GPIO as GPIO


class RFIDReader:
    def __init__(self):
        self.shared_data = open('shared_data.dat', 'r+b')
        self.shared_data.seek(0)
        self.shared_data.write(b'\0' * 1024)
        self.shared_data.flush()
        self.mm = mmap.mmap(self.shared_data.fileno(), 1024)
        self.readCallback = None
        try:
            self.reader = MFRC522()
        except Exception as e:
            logging.exception("Failed to initialize MFRC522: %s", e)
            raise

    def close(self):
        self.shared_data.close()
        self.mm.close()
        try:
            GPIO.cleanup()
        except Exception:
            logging.exception("GPIO cleanup failed")

    def wait_for_release(self):
        while True:
            (status_check, _) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
            if status_check != self.reader.MI_OK:
                break
            time.sleep(0.1)

    def read_uid(self):
        (status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
        if status == self.reader.MI_OK:
            (status, uid) = self.reader.MFRC522_Anticoll()
            if status == self.reader.MI_OK:
                uid_str = "".join(f"{x:02X}" for x in uid)
                return uid_str
        return None

    def handle_uid_detection(self):
        while not stop_event.is_set():
            uid_str = self.read_uid()
            if not uid_str:
                self.wait_for_release()
                continue
            logging.info(f"🎴 UID détecté : {uid_str}")
            self.mm.seek(0)
            self.mm.write(uid_str.encode('utf-8') + b'\0')
            self.mm.flush()
            self.readCallback(uid_str)
        self.close()
