import logging
import mmap
import os
import time
from mfrc522 import MFRC522
import RPi.GPIO as GPIO


class RFIDReader:
    def __init__(self, shared_path='shared_data.dat', size=1024):
        # ensure file exists and is at least `size` bytes
        self.shared_path = shared_path
        self.size = size
        if not os.path.exists(self.shared_path):
            with open(self.shared_path, 'wb') as f:
                f.write(b'\0' * self.size)
        else:
            with open(self.shared_path, 'r+b') as f:
                f.seek(0, os.SEEK_END)
                cur = f.tell()
                if cur < self.size:
                    f.write(b'\0' * (self.size - cur))
        self.shared_data = open(self.shared_path, 'r+b')
        self.mm = mmap.mmap(self.shared_data.fileno(), 1024)
        self.readCallback = None
        self.stop_event = None
        try:
            self.reader = MFRC522()
        except Exception as e:
            logging.exception("Failed to initialize MFRC522: %s", e)
            raise

    def close(self):
        # close mmap first, then file, then GPIO
        try:
            if getattr(self, 'mm', None):
                self.mm.close()
        except Exception:
            logging.exception("mmap close failed")
        try:
            if getattr(self, 'shared_data', None):
                self.shared_data.close()
        except Exception:
            logging.exception("shared_data close failed")
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
        while not (self.stop_event and self.stop_event.is_set()):
            uid_str = self.read_uid()
            if not uid_str:
                self.wait_for_release()
                continue
            logging.info(f"🎴 UID détecté : {uid_str}")
            try:
                self.mm.seek(0)
                self.mm.write(uid_str.encode('utf-8') + b'\0')
                self.mm.flush()
            except Exception:
                logging.exception("Failed to write UID to shared mmap")
            if callable(self.readCallback):
                try:
                    self.readCallback(uid_str)
                except Exception:
                    logging.exception("readCallback raised an exception")
