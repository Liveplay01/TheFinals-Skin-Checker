import ctypes

from PyQt5.QtCore import Qt, QPoint, pyqtSlot
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QFontMetrics
from PyQt5.QtWidgets import QWidget

from data.storage import RARITY_ORDER


RARITY_COLORS = {
    "MYTHIC":    QColor(233, 30,  99),
    "LEGENDARY": QColor(255, 193, 7),
    "EPIC":      QColor(156, 39, 176),
    "RARE":      QColor(33,  150, 243),
    "COMMON":    QColor(158, 158, 158),
}

BG_COLOR        = QColor(13,  17,  23,  210)   # #0d1117 @ 82% opacity
PANEL_COLOR     = QColor(22,  27,  34,  220)   # #161b22
HEADER_COLOR    = QColor(22,  27,  34,  240)
TEXT_COLOR      = QColor(230, 237, 243)
DIM_TEXT_COLOR  = QColor(139, 148, 158)
ACCENT_COLOR    = QColor(232, 197, 71)          # Finals yellow

PANEL_W   = 260
ROW_H     = 26
HEADER_H  = 38
STATS_H   = 32
PADDING   = 10
RADIUS    = 10


def _make_click_through(hwnd: int):
    """Apply WS_EX_TRANSPARENT | WS_EX_LAYERED so the window passes clicks through."""
    GWL_EXSTYLE      = -20
    WS_EX_LAYERED    = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020

    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
    except Exception:
        pass  # Non-Windows platform


class OverlayWindow(QWidget):
    """
    Transparent always-on-top overlay showing detected skins.
    Click-through by default; hold Ctrl and drag title area to reposition.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skins: list = []
        self._counts: dict = {r: 0 for r in RARITY_ORDER}
        self._drag_pos: QPoint | None = None
        self._ctrl_held = False

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)

        self._update_size()
        self.move(20, 100)

    # ── Public API ──────────────────────────────────────────────────────────

    @pyqtSlot(list, dict)
    def update_data(self, skins: list, counts: dict):
        self._skins = skins
        self._counts = counts
        self._update_size()
        self.update()

    def set_position(self, x: int, y: int):
        self.move(x, y)

    # ── Window Management ────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        _make_click_through(hwnd)

    def _update_size(self):
        visible = [s for s in self._skins]
        h = HEADER_H + STATS_H + PADDING + ROW_H * max(len(visible), 1) + PADDING
        self.setFixedSize(PANEL_W, min(h, 600))

    # ── Drag (Ctrl + drag) ───────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self._ctrl_held = True
            # Temporarily remove click-through so dragging works
            self._set_interactive(True)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self._ctrl_held = False
            self._set_interactive(False)

    def _set_interactive(self, interactive: bool):
        hwnd = int(self.winId())
        GWL_EXSTYLE       = -20
        WS_EX_LAYERED     = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        try:
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if interactive:
                style &= ~WS_EX_TRANSPARENT
            else:
                style |= WS_EX_TRANSPARENT
            style |= WS_EX_LAYERED
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._ctrl_held:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos and self._ctrl_held:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()

        # Background panel
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, self.height(), RADIUS, RADIUS)
        painter.fillPath(path, BG_COLOR)

        # Header
        header_rect_path = QPainterPath()
        header_rect_path.addRoundedRect(0, 0, w, HEADER_H, RADIUS, RADIUS)
        painter.fillPath(header_rect_path, HEADER_COLOR)
        # Square off the bottom corners of the header
        painter.fillRect(0, HEADER_H - RADIUS, w, RADIUS, HEADER_COLOR)

        # Header text
        font_header = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(font_header)
        painter.setPen(QPen(ACCENT_COLOR))
        painter.drawText(PADDING, 0, w - PADDING * 2, HEADER_H, Qt.AlignVCenter | Qt.AlignLeft, "THE FINALS  —  SKINS")

        # Ctrl hint
        painter.setPen(QPen(DIM_TEXT_COLOR))
        font_hint = QFont("Segoe UI", 7)
        painter.setFont(font_hint)
        painter.drawText(PADDING, 0, w - PADDING * 2, HEADER_H, Qt.AlignVCenter | Qt.AlignRight, "Ctrl+drag")

        # Stats row
        stats_y = HEADER_H
        painter.fillRect(0, stats_y, w, STATS_H, PANEL_COLOR)
        stat_x = PADDING
        stat_font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(stat_font)
        fm = QFontMetrics(stat_font)

        for rarity in RARITY_ORDER:
            count = self._counts.get(rarity, 0)
            label = f"{rarity[0]} {count}"
            color = RARITY_COLORS.get(rarity, TEXT_COLOR)
            lw = fm.horizontalAdvance(label) + 12

            # Pill background
            pill_path = QPainterPath()
            pill_path.addRoundedRect(stat_x, stats_y + 6, lw, STATS_H - 12, 4, 4)
            bg = QColor(color)
            bg.setAlpha(40)
            painter.fillPath(pill_path, bg)

            painter.setPen(QPen(color))
            painter.drawText(stat_x + 6, stats_y, lw - 6, STATS_H, Qt.AlignVCenter, label)
            stat_x += lw + 4

        # Skin rows
        row_y = HEADER_H + STATS_H + PADDING
        row_font = QFont("Segoe UI", 9)
        badge_font = QFont("Segoe UI", 7, QFont.Bold)
        painter.setFont(row_font)

        if not self._skins:
            painter.setPen(QPen(DIM_TEXT_COLOR))
            painter.drawText(PADDING, row_y, w - PADDING * 2, ROW_H, Qt.AlignVCenter, "No skins detected yet...")
        else:
            for skin in self._skins:
                rarity = skin.rarity
                color = RARITY_COLORS.get(rarity, TEXT_COLOR)

                # Row background (alternating)
                row_bg = QColor(255, 255, 255, 6) if self._skins.index(skin) % 2 == 0 else QColor(0, 0, 0, 0)
                painter.fillRect(0, row_y, w, ROW_H, row_bg)

                # Rarity indicator bar
                painter.fillRect(0, row_y + 3, 3, ROW_H - 6, color)

                # Skin full name
                painter.setFont(row_font)
                painter.setPen(QPen(TEXT_COLOR))
                name_text = f"{skin.weapon}  {skin.name}"
                painter.drawText(PADDING + 4, row_y, w - 90, ROW_H, Qt.AlignVCenter, name_text)

                # Rarity badge
                badge_text = rarity[:5]
                painter.setFont(badge_font)
                badge_w = 48
                badge_x = w - badge_w - PADDING
                pill = QPainterPath()
                pill.addRoundedRect(badge_x, row_y + 5, badge_w, ROW_H - 10, 3, 3)
                bg2 = QColor(color)
                bg2.setAlpha(50)
                painter.fillPath(pill, bg2)
                painter.setPen(QPen(color))
                painter.drawText(badge_x, row_y + 5, badge_w, ROW_H - 10, Qt.AlignCenter, badge_text)

                row_y += ROW_H

        painter.end()
