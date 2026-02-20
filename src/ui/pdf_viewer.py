"""
Native PyQt5 PDF viewer using PyMuPDF (fitz) for rendering.
Supports scrolling, zoom, fit-width, fit-page, and rotation.
Emits page_changed so the toolbar can stay in sync.
"""

import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import config


class RenderWorker(QThread):
    """Renders PDF pages off the main thread."""
    page_ready = pyqtSignal(int, QPixmap)

    def __init__(self, doc, zoom, rotation, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.zoom = zoom
        self.rotation = rotation   # degrees: 0, 90, 180, 270
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        mat = fitz.Matrix(self.zoom, self.zoom).prerotate(self.rotation)
        for i in range(len(self.doc)):
            if self._abort:
                return
            page = self.doc[i]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = QImage(
                pix.samples, pix.width, pix.height,
                pix.stride, QImage.Format_RGB888
            )
            self.page_ready.emit(i, QPixmap.fromImage(img))


class PDFViewer(QWidget):
    """
    Native PDF viewer widget.

    Signals emitted:
        page_changed(int)   — current 1-based page as user scrolls
        zoom_changed(float) — zoom level after ctrl+scroll or fit
        pdf_loaded(int)     — total page count, emitted after load
    """

    page_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(float)
    pdf_loaded   = pyqtSignal(int)

    MIN_ZOOM  = 0.25
    MAX_ZOOM  = 4.0
    ZOOM_STEP = 0.25
    PAGE_GAP  = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc         = None
        self.zoom        = 1.5
        self.rotation    = 0
        self.page_labels = []
        self.worker      = None
        self._init_ui()

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignHCenter)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {config.BG_PRIMARY};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {config.BG_SECONDARY};
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {config.BORDER_COLOR};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {config.BG_SECONDARY};
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {config.BORDER_COLOR};
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{ width: 0; }}
        """)

        self.pages_container = QWidget()
        self.pages_container.setStyleSheet(
            f"background-color: {config.BG_PRIMARY};"
        )
        self.pages_layout = QVBoxLayout()
        self.pages_layout.setContentsMargins(20, 20, 20, 20)
        self.pages_layout.setSpacing(self.PAGE_GAP)
        self.pages_layout.setAlignment(Qt.AlignHCenter)
        self.pages_container.setLayout(self.pages_layout)

        self.scroll_area.setWidget(self.pages_container)
        self.scroll_area.verticalScrollBar().valueChanged.connect(
            self._on_scroll
        )

        self.placeholder = QLabel("Open a PDF to get started ˙◠˙")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"""
            font-size: 18px;
            color: {config.TEXT_SECONDARY};
            background-color: {config.BG_PRIMARY};
        """)
        self.placeholder.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        layout.addWidget(self.placeholder)
        layout.addWidget(self.scroll_area)
        self.scroll_area.hide()
        self.setLayout(layout)

    # ------------------------------------------------------------------ #
    #  Public API / slots                                                  #
    # ------------------------------------------------------------------ #

    def load_pdf(self, pdf_path):
        if self.doc:
            self.doc.close()
        self.rotation = 0
        self.doc = fitz.open(str(pdf_path))
        self._build_page_slots()
        self._render()
        self.placeholder.hide()
        self.scroll_area.show()
        self.pdf_loaded.emit(len(self.doc))

    def go_to_page(self, page_num: int):
        idx = page_num - 1
        if 0 <= idx < len(self.page_labels):
            label = self.page_labels[idx]
            pos = label.mapTo(self.pages_container, label.rect().topLeft())
            self.scroll_area.verticalScrollBar().setValue(
                pos.y() - self.PAGE_GAP
            )

    def set_zoom(self, zoom: float):
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        if self.doc:
            self._render()

    def fit_width(self):
        if not self.doc:
            return
        page_w = self.doc[0].rect.width
        viewport_w = self.scroll_area.viewport().width() - 40
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, viewport_w / page_w))
        self._render()
        self.zoom_changed.emit(self.zoom)

    def fit_page(self):
        if not self.doc:
            return
        page = self.doc[0]
        vw = self.scroll_area.viewport().width() - 40
        vh = self.scroll_area.viewport().height() - 40
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM,
                        min(vw / page.rect.width, vh / page.rect.height)))
        self._render()
        self.zoom_changed.emit(self.zoom)

    def rotate(self):
        self.rotation = (self.rotation + 90) % 360
        if self.doc:
            self._render()

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #

    def _build_page_slots(self):
        for label in self.page_labels:
            self.pages_layout.removeWidget(label)
            label.deleteLater()
        self.page_labels.clear()

        for _ in range(len(self.doc)):
            label = QLabel()
            label.setAlignment(Qt.AlignHCenter)
            label.setStyleSheet("background-color: white; border-radius: 2px;")
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self.pages_layout.addWidget(label)
            self.page_labels.append(label)

    def _render(self):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait()

        self.worker = RenderWorker(self.doc, self.zoom, self.rotation, parent=self)
        self.worker.page_ready.connect(self._on_page_ready)
        self.worker.start()

    def _on_page_ready(self, index, pixmap):
        if index < len(self.page_labels):
            label = self.page_labels[index]
            label.setPixmap(pixmap)
            label.setFixedSize(pixmap.size())

    def _on_scroll(self, value):
        if not self.page_labels:
            return
        viewport_mid = value + self.scroll_area.viewport().height() // 2
        best, best_dist = 0, float("inf")
        for i, label in enumerate(self.page_labels):
            pos = label.mapTo(self.pages_container, label.rect().topLeft())
            dist = abs(pos.y() + label.height() // 2 - viewport_mid)
            if dist < best_dist:
                best_dist, best = dist, i
        self.page_changed.emit(best + 1)

    # ------------------------------------------------------------------ #
    #  Events                                                              #
    # ------------------------------------------------------------------ #

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom = min(self.zoom + self.ZOOM_STEP, self.MAX_ZOOM)
            else:
                self.zoom = max(self.zoom - self.ZOOM_STEP, self.MIN_ZOOM)
            if self.doc:
                self._render()
            self.zoom_changed.emit(self.zoom)
            event.accept()
        else:
            super().wheelEvent(event)