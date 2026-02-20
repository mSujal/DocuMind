"""
Status bar — sits at the bottom of the explorer panel.
Shows size, page count, and last modified date of the active file.
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
import config


class StatusBar(QWidget):
    """
    File info strip shown at the bottom of the explorer panel.
    Call update_file(path, page_count) after a PDF is loaded.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_SECONDARY};
                border-top: 1px solid {config.BORDER_COLOR};
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(5)

        self.size_row     = self._make_row("Size",     "—")
        self.pages_row    = self._make_row("Pages",    "—")
        self.modified_row = self._make_row("Modified", "—")

        layout.addWidget(self.size_row)
        layout.addWidget(self.pages_row)
        layout.addWidget(self.modified_row)
        self.setLayout(layout)

    def _make_row(self, label_text: str, value_text: str) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: 11px;
            color: {config.TEXT_SECONDARY};
            background: transparent;
            border: none;
        """)

        value = QLabel(value_text)
        value.setAlignment(Qt.AlignRight)
        value.setStyleSheet(f"""
            font-size: 11px;
            color: {config.TEXT_PRIMARY};
            background: transparent;
            border: none;
        """)

        # store reference so we can update later
        row._value_label = value

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(value)
        row.setLayout(row_layout)
        return row

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def update_file(self, filepath: str, page_count: int = 0):
        """Refresh all three rows from a real file on disk."""
        try:
            size_bytes = os.path.getsize(filepath)
            size_str   = self._format_size(size_bytes)
        except OSError:
            size_str = "—"

        try:
            mtime    = os.path.getmtime(filepath)
            mod_str  = datetime.fromtimestamp(mtime).strftime("%b %d, %Y")
        except OSError:
            mod_str  = "—"

        pages_str = str(page_count) if page_count > 0 else "—"

        self.size_row._value_label.setText(size_str)
        self.pages_row._value_label.setText(pages_str)
        self.modified_row._value_label.setText(mod_str)

    def clear(self):
        """Reset to dashes when no file is active."""
        self.size_row._value_label.setText("—")
        self.pages_row._value_label.setText("—")
        self.modified_row._value_label.setText("—")

    # ------------------------------------------------------------------ #
    #  Helper                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_size(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"