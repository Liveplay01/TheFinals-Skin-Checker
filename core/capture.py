import mss
import numpy as np


def capture_region(region: dict) -> np.ndarray:
    """
    Captures a screen region using mss.
    region: {"left": x, "top": y, "width": w, "height": h}
    Returns a numpy array in BGR format (OpenCV compatible).
    """
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        frame = np.array(screenshot)
        # mss returns BGRA, drop alpha channel → BGR
        return frame[:, :, :3]


def get_screen_size() -> tuple:
    """Returns (width, height) of the primary monitor."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        return monitor["width"], monitor["height"]


def get_all_monitors() -> list:
    """Returns list of monitor dicts from mss."""
    with mss.mss() as sct:
        return sct.monitors[1:]  # skip index 0 (all-monitors combined)
