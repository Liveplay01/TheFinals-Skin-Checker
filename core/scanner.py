from PyQt5.QtCore import QThread, pyqtSignal

from core.capture import capture_region
from core.ocr_engine import extract_text_candidates
from core.matcher import match_skins


class ScannerThread(QThread):
    """
    Background scan loop.
    Emits skin_detected(dict) for each newly matched skin.
    Emits status_update(str) for UI feedback.
    """

    skin_detected = pyqtSignal(dict)
    status_update = pyqtSignal(str)

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.region: dict | None = None
        self.interval_ms: int = 1500
        self.confidence_threshold: int = 65
        self._running = False

    def configure(self, region: dict, interval_ms: int, confidence_threshold: int):
        self.region = region
        self.interval_ms = interval_ms
        self.confidence_threshold = confidence_threshold

    def run(self):
        self._running = True
        self.status_update.emit("Scanning...")

        skin_names = self.database.get_all_names()

        while self._running:
            if not self.region:
                self.status_update.emit("No region selected.")
                self.msleep(500)
                continue

            try:
                frame = capture_region(self.region)
                candidates = extract_text_candidates(frame, self.confidence_threshold)
                matches = match_skins(candidates, skin_names, self.confidence_threshold)

                for full_name, score in matches:
                    skin = self.database.get_skin(full_name)
                    if skin:
                        self.skin_detected.emit(skin)

            except Exception as exc:
                self.status_update.emit(f"Scan error: {exc}")

            self.msleep(self.interval_ms)

        self.status_update.emit("Stopped.")

    def stop(self):
        self._running = False
        self.wait()
