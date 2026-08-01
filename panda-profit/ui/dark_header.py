"""Custom header view that paints corner button dark."""

from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt


class DarkHeaderView(QHeaderView):
    """QHeaderView subclass that paints the corner area dark."""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.dark_color = QColor("#1a3a5e")
        self.setStyleSheet("""
            QHeaderView {
                background-color: #1a3a5e;
            }
            QHeaderView::section {
                background-color: #1a3a5e;
                color: #00ff88;
                padding: 5px;
                border: none;
                border-right: 1px solid #222222;
                border-bottom: 1px solid #222222;
            }
        """)

    def paintEvent(self, event):
        """Override paint event to draw dark corner."""
        # Call parent to paint sections
        super().paintEvent(event)

        # Paint over corner button area with dark color
        painter = QPainter(self.viewport())
        painter.fillRect(event.rect(), self.dark_color)
        painter.end()
