import os
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QSpinBox,
    QGroupBox, QFormLayout, QProgressBar,
)

from data.storage import RARITY_ORDER, SkinStorage
from ui.area_selector import select_area


RARITY_COLORS = {
    "MYTHIC":    "#e91e63",
    "LEGENDARY": "#ffc107",
    "EPIC":      "#9c27b0",
    "RARE":      "#2196f3",
    "COMMON":    "#9e9e9e",
}

QSS = """
QMainWindow, QWidget#centralWidget {
    background-color: #0d1117;
    color: #e6edf3;
}
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 10px;
    font-weight: bold;
    color: #e6edf3;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #e8c547;
}
QLabel {
    color: #e6edf3;
    background: transparent;
}
QLabel#dimLabel {
    color: #8b949e;
    font-size: 10px;
}
QPushButton {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 11px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton#btnStart {
    background-color: #1a7f37;
    border-color: #2ea043;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 18px;
    color: #ffffff;
}
QPushButton#btnStart:hover {
    background-color: #2ea043;
}
QPushButton#btnStop {
    background-color: #8b1a1a;
    border-color: #da3633;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 18px;
    color: #ffffff;
}
QPushButton#btnStop:hover {
    background-color: #da3633;
}
QPushButton#btnExport {
    background-color: #1f4d8c;
    border-color: #388bfd;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#btnExport:hover {
    background-color: #388bfd;
}
QPushButton#btnRegion {
    background-color: #4a3000;
    border-color: #e8c547;
    color: #e8c547;
    font-weight: bold;
}
QPushButton#btnRegion:hover {
    background-color: #6a4800;
}
QTableWidget {
    background-color: #0d1117;
    alternate-background-color: #111820;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
    font-size: 11px;
}
QTableWidget::item {
    padding: 4px 8px;
}
QTableWidget::item:selected {
    background-color: #1f4d8c;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #161b22;
    color: #e8c547;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 6px 8px;
    font-weight: bold;
    font-size: 10px;
}
QScrollBar:vertical {
    background: #161b22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
}
QProgressBar {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 4px;
    text-align: center;
    color: #e6edf3;
}
QProgressBar::chunk {
    background-color: #e8c547;
    border-radius: 4px;
}
QFrame#separator {
    background-color: #30363d;
    max-height: 1px;
}
"""


def _rarity_badge(rarity: str) -> QTableWidgetItem:
    item = QTableWidgetItem(rarity)
    item.setTextAlignment(Qt.AlignCenter)
    color = RARITY_COLORS.get(rarity, "#9e9e9e")
    item.setForeground(QColor(color))
    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
    return item


class ScraperThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path

    def run(self):
        from data.scraper import run_scraper
        success, msg = run_scraper(self.db_path, progress_callback=self._cb)
        self.finished.emit(success, msg)

    def _cb(self, done, total, weapon):
        self.progress.emit(done, total, weapon)


class MainWindow(QMainWindow):
    def __init__(self, config: dict, database, storage: SkinStorage):
        super().__init__()
        self.config = config
        self.database = database
        self.storage = storage
        self._scanner = None
        self._overlay = None
        self._scraper_thread = None

        self.setWindowTitle("THE FINALS — Skin Scanner")
        self.setMinimumWidth(460)
        self.setMaximumWidth(520)
        self.setObjectName("centralWidget")

        self._build_ui()
        self.setStyleSheet(QSS)

        self._refresh_table()
        self._update_region_label()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        root.addWidget(self._build_header())
        root.addWidget(self._build_region_group())
        root.addWidget(self._build_scanner_group())
        root.addWidget(self._build_stats_bar())
        root.addWidget(self._build_skin_table(), stretch=1)
        root.addWidget(self._build_action_bar())
        root.addWidget(self._build_settings_group())

    def _build_header(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("THE FINALS  Skin Scanner")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #e8c547;")

        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("Segoe UI", 16))
        self._status_dot.setStyleSheet("color: #8b949e;")
        self._status_dot.setToolTip("Idle")

        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(self._status_dot)
        return w

    def _build_region_group(self) -> QGroupBox:
        box = QGroupBox("Capture Region")
        lay = QHBoxLayout(box)
        lay.setSpacing(8)

        self._region_label = QLabel("Not set")
        self._region_label.setObjectName("dimLabel")
        self._region_label.setFont(QFont("Consolas", 9))

        btn = QPushButton("Select Region")
        btn.setObjectName("btnRegion")
        btn.setFixedWidth(120)
        btn.clicked.connect(self._on_select_region)

        lay.addWidget(self._region_label, stretch=1)
        lay.addWidget(btn)
        return box

    def _build_scanner_group(self) -> QGroupBox:
        box = QGroupBox("Scanner")
        lay = QHBoxLayout(box)
        lay.setSpacing(8)

        self._status_label = QLabel("Idle — press Start to begin scanning.")
        self._status_label.setObjectName("dimLabel")
        self._status_label.setWordWrap(True)

        self._btn_start = QPushButton("▶  Start Scan")
        self._btn_start.setObjectName("btnStart")
        self._btn_start.setFixedWidth(130)
        self._btn_start.clicked.connect(self._on_start)

        self._btn_stop = QPushButton("■  Stop")
        self._btn_stop.setObjectName("btnStop")
        self._btn_stop.setFixedWidth(100)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop)

        self._btn_overlay = QPushButton("Overlay")
        self._btn_overlay.setCheckable(True)
        self._btn_overlay.setFixedWidth(80)
        self._btn_overlay.toggled.connect(self._on_toggle_overlay)

        lay.addWidget(self._status_label, stretch=1)
        lay.addWidget(self._btn_start)
        lay.addWidget(self._btn_stop)
        lay.addWidget(self._btn_overlay)
        return box

    def _build_stats_bar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #161b22; border-radius: 6px; padding: 4px;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        self._stat_labels: dict[str, QLabel] = {}
        for rarity in RARITY_ORDER:
            color = RARITY_COLORS[rarity]
            lbl = QLabel(f"<b style='color:{color}'>{rarity[0]}</b> 0")
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet("background: transparent;")
            lay.addWidget(lbl)
            self._stat_labels[rarity] = lbl

        lay.addStretch()
        total_lbl = QLabel("Total: 0")
        total_lbl.setFont(QFont("Segoe UI", 9))
        total_lbl.setStyleSheet("color: #8b949e; background: transparent;")
        lay.addWidget(total_lbl)
        self._total_label = total_lbl
        return w

    def _build_skin_table(self) -> QTableWidget:
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Weapon", "Skin Name", "Rarity", "Detected"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)
        self._table.setMinimumHeight(220)
        return self._table

    def _build_action_bar(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._btn_export = QPushButton("Export to Excel")
        self._btn_export.setObjectName("btnExport")
        self._btn_export.clicked.connect(self._on_export)

        btn_clear = QPushButton("Clear Session")
        btn_clear.clicked.connect(self._on_clear)

        self._btn_update_db = QPushButton("Update DB from Wiki")
        self._btn_update_db.clicked.connect(self._on_update_db)

        lay.addWidget(self._btn_export)
        lay.addWidget(btn_clear)
        lay.addStretch()
        lay.addWidget(self._btn_update_db)
        return w

    def _build_settings_group(self) -> QGroupBox:
        box = QGroupBox("Settings")
        form = QFormLayout(box)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(500, 10000)
        self._spin_interval.setSingleStep(100)
        self._spin_interval.setSuffix(" ms")
        self._spin_interval.setValue(self.config.get("scan_interval_ms", 1500))
        self._spin_interval.valueChanged.connect(lambda v: self._save_config("scan_interval_ms", v))

        self._spin_confidence = QSpinBox()
        self._spin_confidence.setRange(30, 99)
        self._spin_confidence.setSuffix(" %")
        self._spin_confidence.setValue(self.config.get("ocr_confidence_threshold", 65))
        self._spin_confidence.valueChanged.connect(lambda v: self._save_config("ocr_confidence_threshold", v))

        self._scraper_progress = QProgressBar()
        self._scraper_progress.setVisible(False)
        self._scraper_status = QLabel("")
        self._scraper_status.setObjectName("dimLabel")
        self._scraper_status.setVisible(False)

        db_info = QLabel(f"DB: {self.database.count()} skins  |  v{self.database.version}  |  {self.database.last_updated}")
        db_info.setObjectName("dimLabel")
        self._db_info_label = db_info

        form.addRow("Scan interval:", self._spin_interval)
        form.addRow("OCR confidence:", self._spin_confidence)
        form.addRow("Database:", self._db_info_label)
        form.addRow(self._scraper_progress)
        form.addRow(self._scraper_status)

        return box

    # ── Region Selection ─────────────────────────────────────────────────────

    def _on_select_region(self):
        self.hide()
        selector = select_area()
        selector.region_selected.connect(self._on_region_confirmed)
        selector.cancelled.connect(self.show)

    def _on_region_confirmed(self, region: dict):
        self.config["capture_region"] = region
        self._save_config_all()
        self._update_region_label()
        self.show()

    def _update_region_label(self):
        r = self.config.get("capture_region")
        if r:
            self._region_label.setText(
                f"x={r['left']}  y={r['top']}  {r['width']}×{r['height']} px"
            )
        else:
            self._region_label.setText("Not set — click 'Select Region'")

    # ── Scanner ───────────────────────────────────────────────────────────────

    def _on_start(self):
        if not self.config.get("capture_region"):
            QMessageBox.warning(self, "No Region", "Please select a capture region first.")
            return

        from core.scanner import ScannerThread
        from core.ocr_engine import configure_tesseract

        configure_tesseract(self.config.get("tesseract_path", ""))

        self._scanner = ScannerThread(self.database)
        self._scanner.configure(
            region=self.config["capture_region"],
            interval_ms=self.config.get("scan_interval_ms", 1500),
            confidence_threshold=self.config.get("ocr_confidence_threshold", 65),
        )
        self._scanner.skin_detected.connect(self._on_skin_detected)
        self._scanner.status_update.connect(self._on_status_update)
        self._scanner.start()

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status_dot.setStyleSheet("color: #2ea043;")
        self._status_dot.setToolTip("Scanning")

    def _on_stop(self):
        if self._scanner:
            self._scanner.stop()
            self._scanner = None
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status_dot.setStyleSheet("color: #8b949e;")
        self._status_label.setText("Stopped.")

    def _on_skin_detected(self, skin_entry: dict):
        added = self.storage.add(skin_entry)
        if added:
            self._refresh_table()
            self._update_overlay()

    def _on_status_update(self, msg: str):
        self._status_label.setText(msg)

    # ── Overlay ───────────────────────────────────────────────────────────────

    def _on_toggle_overlay(self, checked: bool):
        if checked:
            from ui.overlay import OverlayWindow
            if self._overlay is None:
                self._overlay = OverlayWindow()
                pos = self.config.get("overlay_position", {"x": 20, "y": 100})
                self._overlay.set_position(pos["x"], pos["y"])
            self._update_overlay()
            self._overlay.show()
            self._btn_overlay.setText("Hide")
        else:
            if self._overlay:
                self._overlay.hide()
            self._btn_overlay.setText("Overlay")

    def _update_overlay(self):
        if self._overlay and self._overlay.isVisible():
            self._overlay.update_data(
                self.storage.get_all(),
                self.storage.count_by_rarity(),
            )

    # ── Table ─────────────────────────────────────────────────────────────────

    def _refresh_table(self):
        skins = self.storage.get_all()
        self._table.setRowCount(0)
        for skin in skins:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(skin.weapon))
            self._table.setItem(row, 1, QTableWidgetItem(skin.name))
            self._table.setItem(row, 2, _rarity_badge(skin.rarity))
            self._table.setItem(row, 3, QTableWidgetItem(skin.first_seen))

        self._update_stats()

    def _update_stats(self):
        counts = self.storage.count_by_rarity()
        for rarity, lbl in self._stat_labels.items():
            color = RARITY_COLORS[rarity]
            lbl.setText(f"<b style='color:{color}'>{rarity[0]}</b> {counts[rarity]}")
        self._total_label.setText(f"Total: {self.storage.count()}")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_export(self):
        skins = self.storage.get_all()
        if not skins:
            QMessageBox.information(self, "Nothing to Export", "No skins detected yet.")
            return

        default_name = f"TheFinals_Skins_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", default_name, "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            from data.exporter import export_xlsx
            export_xlsx(skins, path)
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _on_clear(self):
        reply = QMessageBox.question(
            self, "Clear Session",
            "Remove all detected skins from the current session?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.storage.clear()
            self._refresh_table()
            self._update_overlay()

    def _on_update_db(self):
        if self._scraper_thread and self._scraper_thread.isRunning():
            return

        self._btn_update_db.setEnabled(False)
        self._scraper_progress.setVisible(True)
        self._scraper_progress.setValue(0)
        self._scraper_status.setVisible(True)
        self._scraper_status.setText("Connecting to wiki...")

        db_path = self.database.db_path
        self._scraper_thread = ScraperThread(db_path)
        self._scraper_thread.progress.connect(self._on_scraper_progress)
        self._scraper_thread.finished.connect(self._on_scraper_done)
        self._scraper_thread.start()

    def _on_scraper_progress(self, done: int, total: int, weapon: str):
        self._scraper_progress.setMaximum(total)
        self._scraper_progress.setValue(done)
        self._scraper_status.setText(f"Scraping: {weapon}...")

    def _on_scraper_done(self, success: bool, msg: str):
        self._scraper_progress.setVisible(False)
        self._scraper_status.setVisible(False)
        self._btn_update_db.setEnabled(True)

        if success:
            self.database.reload()
            self._db_info_label.setText(
                f"DB: {self.database.count()} skins  |  v{self.database.version}  |  {self.database.last_updated}"
            )
            QMessageBox.information(self, "Database Updated", msg)
        else:
            QMessageBox.warning(self, "Update Failed", msg)

    # ── Config ────────────────────────────────────────────────────────────────

    def _save_config(self, key: str, value):
        self.config[key] = value
        self._save_config_all()

    def _save_config_all(self):
        import json
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        try:
            with open(os.path.abspath(config_path), "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except OSError:
            pass

    # ── Close ─────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._scanner:
            self._scanner.stop()
        if self._overlay:
            self._overlay.close()
        self._save_config_all()
        event.accept()
