from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor
from PyQt5.QtWidgets import QWidget, QApplication


class AreaSelector(QWidget):
    """
    Full-screen transparent overlay that lets the user draw a capture region.
    Emits region_selected(dict) on mouse release, or cancelled() on ESC.
    """

    region_selected = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._origin = None
        self._current = None
        self._selecting = False

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            self._current = event.pos()
            self.update()

            rect = QRect(self._origin, self._current).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.region_selected.emit({
                    "left":   rect.left(),
                    "top":    rect.top(),
                    "width":  rect.width(),
                    "height": rect.height(),
                })
            else:
                self.cancelled.emit()
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dim the whole screen
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._origin and self._current:
            rect = QRect(self._origin, self._current).normalized()

            # Cut out the selected area (transparent)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw border around selection
            pen = QPen(QColor(232, 197, 71), 2)  # Finals yellow
            painter.setPen(pen)
            painter.drawRect(rect)

            # Corner handles
            handle_size = 8
            handle_color = QColor(232, 197, 71)
            painter.setBrush(handle_color)
            painter.setPen(Qt.NoPen)
            for corner in [
                rect.topLeft(), rect.topRight(),
                rect.bottomLeft(), rect.bottomRight()
            ]:
                painter.drawRect(
                    corner.x() - handle_size // 2,
                    corner.y() - handle_size // 2,
                    handle_size, handle_size
                )

            # Dimension label
            label = f"{rect.width()} × {rect.height()} px"
            font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(QColor(232, 197, 71)))
            painter.drawText(rect.left() + 4, rect.top() - 6, label)

        # Instruction text
        painter.setPen(QPen(QColor(230, 230, 230, 200)))
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignBottom | Qt.AlignHCenter,
            "Click and drag to select the capture region  |  ESC to cancel",
        )


def select_area(parent=None) -> "AreaSelector":
    """Create and show the area selector widget."""
    selector = AreaSelector()
    selector.showFullScreen()
    return selector
