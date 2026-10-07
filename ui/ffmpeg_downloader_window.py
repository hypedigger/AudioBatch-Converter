import threading

from PyQt6.QtCore    import Qt, pyqtSignal, QObject
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QProgressBar, QPushButton, QWidget)
from PyQt6.QtGui     import QFont

from core.ffmpeg_manager import FFmpegManager
from ui.effects          import apply_acrylic


# ── Worker signals ───────────────────────────────────────────────────────────

class _Signals(QObject):
    progress = pyqtSignal(int, int)   # downloaded, total
    status   = pyqtSignal(str)
    done     = pyqtSignal()
    error    = pyqtSignal(str)


# ── Dialog ───────────────────────────────────────────────────────────────────

class FFmpegDownloaderWindow(QDialog):
    def __init__(self, ffmpeg_manager: FFmpegManager, parent=None):
        super().__init__(parent)
        self._mgr     = ffmpeg_manager
        self._signals = _Signals()
        self._done    = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 260)

        self._build_ui()
        self._connect()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("central_widget")
        card.setStyleSheet("""
            #central_widget {
                background: rgba(14, 12, 28, 230);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,14);
            }
        """)
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(36, 34, 36, 30)
        lay.setSpacing(16)

        # Icon + title
        title_row = QHBoxLayout()
        icon_lbl  = QLabel("⚡")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 28))
        icon_lbl.setStyleSheet("color: rgba(160,120,255,255);")
        title_row.addWidget(icon_lbl)

        title_lbl = QLabel("FFmpeg requis")
        title_lbl.setFont(QFont("Segoe UI Variable", 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: white; margin-left: 10px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        lay.addLayout(title_row)

        # Subtitle
        sub = QLabel(
            "FFmpeg est nécessaire pour la conversion audio.\n"
            "Il va être téléchargé automatiquement (~100 Mo)."
        )
        sub.setStyleSheet("color: rgba(200,200,220,150); font-size:13px;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # Status label
        self._status_lbl = QLabel("En attente…")
        self._status_lbl.setStyleSheet(
            "color: rgba(160,130,255,200); font-size:12px; font-style:italic;"
        )
        lay.addWidget(self._status_lbl)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(8)
        self._progress.setStyleSheet("""
            QProgressBar {
                background: rgba(255,255,255,12);
                border: none; border-radius: 4px;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(110,88,220,255), stop:1 rgba(190,140,255,255));
                border-radius: 4px;
            }
        """)
        lay.addWidget(self._progress)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.setFixedWidth(110)
        self._btn_cancel.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,10);
                color: rgba(255,255,255,160);
                border: 1px solid rgba(255,255,255,14);
                border-radius: 8px; padding: 8px 16px;
            }
            QPushButton:hover { background: rgba(255,255,255,18); }
        """)
        btn_row.addWidget(self._btn_cancel)

        self._btn_start = QPushButton("Télécharger")
        self._btn_start.setFixedWidth(130)
        self._btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(110,88,220,220), stop:1 rgba(160,110,255,220));
                color: white; border: none; border-radius: 8px;
                padding: 8px 16px; font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(130,108,240,255), stop:1 rgba(180,130,255,255));
            }
        """)
        btn_row.addWidget(self._btn_start)
        lay.addLayout(btn_row)

    def _connect(self):
        self._btn_start.clicked.connect(self._start_download)
        self._btn_cancel.clicked.connect(self.reject)
        self._signals.progress.connect(self._on_progress)
        self._signals.status.connect(self._on_status)
        self._signals.done.connect(self._on_done)
        self._signals.error.connect(self._on_error)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _start_download(self):
        self._btn_start.setEnabled(False)
        self._btn_start.setText("Téléchargement…")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self._mgr.download(
                progress_callback=lambda dl, total:
                    self._signals.progress.emit(dl, total),
                status_callback=lambda msg:
                    self._signals.status.emit(msg),
            )
            self._signals.done.emit()
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int(downloaded / total * 100)
            self._progress.setValue(pct)
            mb_dl  = downloaded / (1024 * 1024)
            mb_tot = total      / (1024 * 1024)
            self._status_lbl.setText(f"Téléchargement… {mb_dl:.1f} / {mb_tot:.1f} Mo")
        else:
            self._progress.setRange(0, 0)  # indeterminate

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_done(self):
        self._done = True
        self._status_lbl.setText("✓ FFmpeg installé avec succès !")
        self._progress.setValue(100)
        self._btn_cancel.setText("Fermer")
        self._btn_cancel.clicked.disconnect()
        self._btn_cancel.clicked.connect(self.accept)
        self._btn_start.hide()

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"Erreur : {msg}")
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._btn_start.setEnabled(True)
        self._btn_start.setText("Réessayer")

    # ── Events ────────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        apply_acrylic(hwnd, dark=True)
