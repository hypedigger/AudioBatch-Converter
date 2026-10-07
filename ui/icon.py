from PyQt6.QtGui  import QIcon, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF


def _render_icon(size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Rounded dark-purple background
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0.0, QColor(28, 14, 65))
    grad.setColorAt(1.0, QColor(55, 28, 110))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    radius = size * 0.22
    p.drawRoundedRect(0, 0, size, size, radius, radius)

    # Subtle inner glow rim
    rim = QLinearGradient(0, 0, size, size)
    rim.setColorAt(0.0, QColor(160, 100, 255, 60))
    rim.setColorAt(1.0, QColor(80,  40, 180, 20))
    from PyQt6.QtGui import QPen
    p.setBrush(Qt.BrushStyle.NoBrush)
    pen = QPen(QBrush(rim), max(1, size // 32))
    p.setPen(pen)
    p.drawRoundedRect(1, 1, size - 2, size - 2, radius - 1, radius - 1)

    # Musical note ♫ centred
    p.setPen(QColor(210, 160, 255))
    font = QFont("Segoe UI Emoji", int(size * 0.54))
    p.setFont(font)
    p.drawText(QRectF(0, -int(size * 0.05), size, size),
               Qt.AlignmentFlag.AlignCenter, "♫")

    p.end()
    return pix


def create_app_icon() -> QIcon:
    icon = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_render_icon(sz))
    return icon
