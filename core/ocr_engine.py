import os
import cv2
import numpy as np
import pytesseract
from pytesseract import Output


def configure_tesseract(path: str):
    """Set Tesseract executable path and auto-set TESSDATA_PREFIX if not already set."""
    if not (path and os.path.isfile(path)):
        return
    pytesseract.pytesseract.tesseract_cmd = path
    if not os.environ.get("TESSDATA_PREFIX"):
        tessdata = os.path.join(os.path.dirname(path), "tessdata")
        if os.path.isdir(tessdata):
            os.environ["TESSDATA_PREFIX"] = tessdata


def preprocess_image(frame: np.ndarray) -> np.ndarray:
    """
    Preprocess a BGR frame for OCR:
    - Grayscale
    - Upscale 2x for better character recognition
    - CLAHE contrast enhancement
    - Slight denoise
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    upscaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(upscaled)
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
    return denoised


def extract_text_candidates(frame: np.ndarray, confidence_threshold: int = 65) -> list[str]:
    """
    Extract potential skin name strings from a preprocessed image.
    Returns a list of candidate multi-word strings above the confidence threshold.
    """
    processed = preprocess_image(frame)
    config = "--psm 6 -l eng --oem 3"
    data = pytesseract.image_to_data(processed, config=config, output_type=Output.DICT)

    words = []
    confidences = data["conf"]
    texts = data["text"]
    block_nums = data["block_num"]
    line_nums = data["line_num"]

    current_line = []
    current_line_key = (-1, -1)

    for i, (text, conf, block, line) in enumerate(zip(texts, confidences, block_nums, line_nums)):
        text = text.strip()
        if not text:
            continue
        try:
            conf_val = int(conf)
        except (ValueError, TypeError):
            continue
        if conf_val < confidence_threshold:
            continue

        line_key = (block, line)
        if line_key != current_line_key:
            if current_line:
                words.append(" ".join(current_line))
            current_line = [text]
            current_line_key = line_key
        else:
            current_line.append(text)

    if current_line:
        words.append(" ".join(current_line))

    # Filter out too-short or numeric-only strings
    candidates = [
        w for w in words
        if len(w) >= 3 and not w.replace(" ", "").isdigit()
    ]
    return candidates
