"""
Explorer panel — left sidebar showing opened PDF files.

For now holds the currently opened PDF.
Built to be extended later with:
  - multiple files / collections
  - folder grouping
  - right-click context menu (chunk single / chunk collection)
  - drag-and-drop adding
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap
from src.ui.icons import svg_to_icon, ICON_PDF_FILE, ICON_NEW_FOLDER, ICON_REFRESH, ICON_SEARCH
import config


class FileItem(QWidget):
    """A single clickable file row in the tree."""

    clicked = pyqtSignal(str)   # emits full file path

    def __init__(self, filepath: str, active: bool = False, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self._active = active
        self._init_ui()
        self._set_active(active)

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # File icon
        icon_label = QLabel()
        icon_label.setPixmap(
            svg_to_icon(ICON_PDF_FILE, color="#f87171", size=15).pixmap(15, 15)
        )
        icon_label.setFixedSize(15, 15)
        icon_label.setStyleSheet("background: transparent; border: none;")

        # File name
        self.name_label = QLabel(self.filename)
        self.name_label.setStyleSheet(f"""
            font-size: 13px;
            color: {config.TEXT_PRIMARY};
            background: transparent;
            border: none;
        """)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(icon_label)
        layout.addWidget(self.name_label)
        self.setLayout(layout)

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(28)

    def _set_active(self, active: bool):
        self._active = active
        if active:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {config.TEXT_ACCENT}22;
                    border-left: 2px solid {config.TEXT_ACCENT};
                    border-radius: 4px;
                }}
            """)
            self.name_label.setStyleSheet(f"""
                font-size: 13px;
                color: {config.TEXT_ACCENT};
                background: transparent;
                border: none;
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QWidget:hover {
                    background-color: rgba(255,255,255,0.05);
                }
            """)
            self.name_label.setStyleSheet(f"""
                font-size: 13px;
                color: {config.TEXT_PRIMARY};
                background: transparent;
                border: none;
            """)

    def set_active(self, active: bool):
        self._set_active(active)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.filepath)
        super().mousePressEvent(event)


class ExplorerPanel(QWidget):
    """
    Left sidebar explorer.

    Signals
    -------
    file_selected(str)  — emitted when user clicks a file, passes full path
    """

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[str] = []        # list of absolute paths
        self._active_path: str | None = None
        self._file_items: list[FileItem] = []
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_SECONDARY};
            }}
        """)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────── #
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_SECONDARY};
                border-bottom: 1px solid {config.BORDER_COLOR};
            }}
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(4)

        title = QLabel("EXPLORER")
        title.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {config.TEXT_SECONDARY};
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QPushButton:hover {{ background-color: {config.BUTTON_HOVER_BG}; }}
            QPushButton:pressed {{ background-color: {config.BUTTON_ACTIVE_BG}; }}
        """

        btn_new = QPushButton()
        btn_new.setIcon(svg_to_icon(ICON_NEW_FOLDER, color=config.ICON_COLOR, size=14))
        btn_new.setIconSize(QSize(14, 14))
        btn_new.setFixedSize(24, 24)
        btn_new.setToolTip("New collection")
        btn_new.setStyleSheet(btn_style)

        btn_refresh = QPushButton()
        btn_refresh.setIcon(svg_to_icon(ICON_REFRESH, color=config.ICON_COLOR, size=14))
        btn_refresh.setIconSize(QSize(14, 14))
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.setToolTip("Refresh")
        btn_refresh.setStyleSheet(btn_style)

        header_layout.addWidget(btn_new)
        header_layout.addWidget(btn_refresh)
        header.setLayout(header_layout)

        # ── Search bar ───────────────────────────────────────────────── #
        search_container = QWidget()
        search_container.setStyleSheet("background: transparent; border: none;")
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 6, 10, 6)
        search_layout.setSpacing(6)

        search_icon = QLabel()
        search_icon.setPixmap(
            svg_to_icon(ICON_SEARCH, color=config.TEXT_SECONDARY, size=13).pixmap(13, 13)
        )
        search_icon.setStyleSheet("background: transparent; border: none;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {config.TEXT_ACCENT};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        search_container.setLayout(search_layout)

        # ── Scroll area for file list ─────────────────────────────────── #
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {config.BG_SECONDARY};
                width: 4px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {config.BORDER_COLOR};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self.file_list_widget = QWidget()
        self.file_list_widget.setStyleSheet("background: transparent;")
        self.file_list_layout = QVBoxLayout()
        self.file_list_layout.setContentsMargins(6, 6, 6, 6)
        self.file_list_layout.setSpacing(2)
        self.file_list_layout.setAlignment(Qt.AlignTop)

        # Placeholder shown when no files are loaded
        self.placeholder = QLabel("No files open yet.\nOpen a PDF to get started.")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet(f"""
            color: {config.TEXT_SECONDARY};
            font-size: 12px;
            padding: 20px 10px;
            background: transparent;
            border: none;
        """)
        self.file_list_layout.addWidget(self.placeholder)

        self.file_list_widget.setLayout(self.file_list_layout)
        self.scroll_area.setWidget(self.file_list_widget)

        # ── Assemble ─────────────────────────────────────────────────── #
        root_layout.addWidget(header)
        root_layout.addWidget(search_container)
        root_layout.addWidget(self.scroll_area)
        self.setLayout(root_layout)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def add_file(self, filepath: str):
        """
        Add a file to the explorer and mark it as active.
        If already present, just activates it.
        """
        if filepath not in self._files:
            self._files.append(filepath)
            item = FileItem(filepath, active=False)
            item.clicked.connect(self._on_file_clicked)
            self._file_items.append(item)

            # Hide placeholder once we have files
            self.placeholder.hide()
            self.file_list_layout.addWidget(item)

        self._set_active(filepath)

    def _set_active(self, filepath: str):
        """Mark one file as active, deactivate all others."""
        self._active_path = filepath
        for item in self._file_items:
            item.set_active(item.filepath == filepath)

    def _on_file_clicked(self, filepath: str):
        self._set_active(filepath)
        self.file_selected.emit(filepath)

    def _on_search(self, text: str):
        query = text.lower()
        for item in self._file_items:
            item.setVisible(query == "" or query in item.filename.lower())

    def get_active_file(self) -> str | None:
        return self._active_path