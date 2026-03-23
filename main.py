import json
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG = {
    "capture_region": None,
    "scan_interval_ms": 1500,
    "ocr_confidence_threshold": 65,
    "overlay_opacity": 0.85,
    "overlay_position": {"x": 20, "y": 100},
}

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DB_PATH     = os.path.join(BASE_DIR, "skin_db.json")


def load_config() -> dict:
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = {**DEFAULT_CONFIG, **saved}
            return config
        except (json.JSONDecodeError, OSError):
            pass
    config = DEFAULT_CONFIG.copy()
    _save_config(config)
    return config


def _save_config(config: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass


def find_tesseract() -> str | None:
    """
    Resolve Tesseract path in priority order:
    1. Bundled in the PyInstaller package (vendor/tesseract/)
    2. Next to the executable / project root (vendor/tesseract/)
    3. System PATH
    4. Standard Windows install paths
    """
    # Determine base directory (works both frozen and from source)
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", BASE_DIR)   # PyInstaller temp extraction dir
    else:
        base = BASE_DIR

    bundled_exe = os.path.join(base, "tesseract", "tesseract.exe")
    if os.path.isfile(bundled_exe):
        # Tell pytesseract where to find tessdata
        tessdata = os.path.join(base, "tesseract", "tessdata")
        if os.path.isdir(tessdata):
            os.environ["TESSDATA_PREFIX"] = tessdata
        return bundled_exe

    # System PATH
    import shutil
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path

    # Standard Windows install locations
    for candidate in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.isfile(candidate):
            return candidate

    return None


def main():
    # High-DPI support
    if hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy"):
        from PyQt5.QtCore import Qt as _Qt
        QApplication.setAttribute(_Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(_Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("TheFinalsStats")
    app.setOrganizationName("Antigravity")

    config = load_config()

    # Load skin database
    try:
        from data.database import SkinDatabase
        database = SkinDatabase(DB_PATH)
    except FileNotFoundError as exc:
        QMessageBox.critical(None, "Database Missing", str(exc))
        sys.exit(1)

    # Load or resume session storage
    from data.storage import SkinStorage
    storage = SkinStorage()
    storage.load_session()

    # Auto-resolve and configure Tesseract (bundled or system)
    from core.ocr_engine import configure_tesseract
    tess_path = find_tesseract()
    if tess_path:
        configure_tesseract(tess_path)

    # Launch main window
    from ui.main_window import MainWindow
    window = MainWindow(config, database, storage)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
