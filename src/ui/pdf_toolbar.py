"""
PDF control toolbar — sits between the top bar and the PDF viewer.
Controls: previous/next page, page input, zoom out/in/level, fit width,
fit page, rotate.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIntValidator
from src.ui.icons import (
    svg_to_icon,
    ICON_PREV_PAGE,
    ICON_NEXT_PAGE,
    ICON_ZOOM_OUT,
    ICON_ZOOM_IN,
    ICON_FIT_WIDTH,
    ICON_FIT_PAGE,
    ICON_ROTATE,
)
import config


def _separator():
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(1)
    sep.setStyleSheet(f"background-color: {config.BORDER_COLOR}; border: none;")
    return sep


class PDFToolbar(QWidget):
    """
    Toolbar that emits signals consumed by PDFViewer.

    Signals
    -------
    go_to_page(int)          — 1-based page number
    zoom_changed(float)      — absolute zoom factor (e.g. 1.5)
    fit_width_requested()
    fit_page_requested()
    rotate_requested()
    """

    go_to_page          = pyqtSignal(int)
    zoom_changed        = pyqtSignal(float)
    fit_width_requested = pyqtSignal()
    fit_page_requested  = pyqtSignal()
    rotate_requested    = pyqtSignal()

    ZOOM_PRESETS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 3.0, 4.0]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total_pages  = 1
        self._current_page = 1
        self._zoom         = 1.5
        self._init_ui()

    # ------------------------------------------------------------------ #
    #  Build UI                                                            #
    # ------------------------------------------------------------------ #

    def _init_ui(self):
        self.setFixedHeight(42)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_SECONDARY};
                border-bottom: 1px solid {config.BORDER_COLOR};
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        # ── Page navigation ──────────────────────────────────────────── #
        self.btn_prev = self._icon_btn(ICON_PREV_PAGE, "Previous page")
        self.btn_prev.clicked.connect(self._prev_page)

        self.page_input = QLineEdit(str(self._current_page))
        self.page_input.setFixedWidth(36)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setValidator(QIntValidator(1, 9999))
        self.page_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {config.TEXT_ACCENT};
            }}
        """)
        self.page_input.returnPressed.connect(self._on_page_entered)

        self.page_total = QLabel(f"/ {self._total_pages}")
        self.page_total.setStyleSheet(
            f"color: {config.TEXT_SECONDARY}; font-size: 13px; "
            f"background: transparent; border: none;"
        )

        self.btn_next = self._icon_btn(ICON_NEXT_PAGE, "Next page")
        self.btn_next.clicked.connect(self._next_page)

        layout.addWidget(self.btn_prev)
        layout.addWidget(self.page_input)
        layout.addWidget(self.page_total)
        layout.addWidget(self.btn_next)
        layout.addWidget(_separator())

        # ── Zoom controls ────────────────────────────────────────────── #
        self.btn_zoom_out = self._icon_btn(ICON_ZOOM_OUT, "Zoom out")
        self.btn_zoom_out.clicked.connect(self._zoom_out)

        self.zoom_combo = QComboBox()
        self.zoom_combo.setFixedWidth(72)
        self.zoom_combo.setEditable(True)
        self.zoom_combo.lineEdit().setAlignment(Qt.AlignCenter)
        for z in self.ZOOM_PRESETS:
            self.zoom_combo.addItem(f"{int(z * 100)}%", z)
        self.zoom_combo.setCurrentText("150%")
        self.zoom_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 4px;
                padding: 2px 4px;
                font-size: 13px;
            }}
            QComboBox:focus {{ border: 1px solid {config.TEXT_ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox QAbstractItemView {{
                background-color: {config.BG_SECONDARY};
                color: {config.TEXT_PRIMARY};
                selection-background-color: {config.TEXT_ACCENT};
            }}
        """)
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_preset)
        self.zoom_combo.lineEdit().returnPressed.connect(self._on_zoom_typed)

        self.btn_zoom_in = self._icon_btn(ICON_ZOOM_IN, "Zoom in")
        self.btn_zoom_in.clicked.connect(self._zoom_in)

        layout.addWidget(self.btn_zoom_out)
        layout.addWidget(self.zoom_combo)
        layout.addWidget(self.btn_zoom_in)
        layout.addWidget(_separator())

        # ── Fit modes ────────────────────────────────────────────────── #
        self.btn_fit_width = self._icon_btn(ICON_FIT_WIDTH, "Fit width")
        self.btn_fit_width.clicked.connect(self.fit_width_requested.emit)

        self.btn_fit_page = self._icon_btn(ICON_FIT_PAGE, "Fit page")
        self.btn_fit_page.clicked.connect(self.fit_page_requested.emit)

        layout.addWidget(self.btn_fit_width)
        layout.addWidget(self.btn_fit_page)
        layout.addWidget(_separator())

        # ── Rotate ───────────────────────────────────────────────────── #
        self.btn_rotate = self._icon_btn(ICON_ROTATE, "Rotate clockwise")
        self.btn_rotate.clicked.connect(self.rotate_requested.emit)
        layout.addWidget(self.btn_rotate)

        layout.addStretch()
        self.setLayout(layout)
        self._update_nav_buttons()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def set_total_pages(self, n: int):
        self._total_pages = max(1, n)
        self.page_total.setText(f"/ {self._total_pages}")
        self.page_input.setValidator(QIntValidator(1, self._total_pages))
        self._update_nav_buttons()

    def set_current_page(self, n: int):
        self._current_page = n
        self.page_input.setText(str(n))
        self._update_nav_buttons()

    def set_zoom(self, zoom: float):
        self._zoom = zoom
        self.zoom_combo.setCurrentText(f"{int(zoom * 100)}%")

    # ------------------------------------------------------------------ #
    #  Internal slots                                                      #
    # ------------------------------------------------------------------ #

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self.page_input.setText(str(self._current_page))
            self._update_nav_buttons()
            self.go_to_page.emit(self._current_page)

    def _next_page(self):
        if self._current_page < self._total_pages:
            self._current_page += 1
            self.page_input.setText(str(self._current_page))
            self._update_nav_buttons()
            self.go_to_page.emit(self._current_page)

    def _on_page_entered(self):
        try:
            n = max(1, min(int(self.page_input.text()), self._total_pages))
            self._current_page = n
            self.page_input.setText(str(n))
            self._update_nav_buttons()
            self.go_to_page.emit(n)
        except ValueError:
            self.page_input.setText(str(self._current_page))

    def _zoom_in(self):
        self._apply_zoom(min(self._zoom + 0.25, 4.0))

    def _zoom_out(self):
        self._apply_zoom(max(self._zoom - 0.25, 0.25))

    def _on_zoom_preset(self, index):
        zoom = self.zoom_combo.itemData(index)
        if zoom:
            self._apply_zoom(zoom)

    def _on_zoom_typed(self):
        text = self.zoom_combo.currentText().replace("%", "").strip()
        try:
            self._apply_zoom(max(0.25, min(float(text) / 100, 4.0)))
        except ValueError:
            self.zoom_combo.setCurrentText(f"{int(self._zoom * 100)}%")

    def _apply_zoom(self, zoom: float):
        self._zoom = zoom
        self.zoom_combo.setCurrentText(f"{int(zoom * 100)}%")
        self.zoom_changed.emit(zoom)

    def _update_nav_buttons(self):
        self.btn_prev.setEnabled(self._current_page > 1)
        self.btn_next.setEnabled(self._current_page < self._total_pages)

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #

    def _icon_btn(self, icon_svg: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(svg_to_icon(icon_svg, color=config.ICON_COLOR, size=15))
        btn.setIconSize(QSize(15, 15))
        btn.setToolTip(tooltip)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {config.BUTTON_HOVER_BG};
            }}
            QPushButton:pressed {{
                background-color: {config.BUTTON_ACTIVE_BG};
            }}
            QPushButton:disabled {{
                opacity: 0.35;
            }}
        """)
        return btn