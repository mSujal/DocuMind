"""
Top bar component containing the document title and the action buttons
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from src.ui.icons import (
    svg_to_icon,
    ICON_LOGO,
    ICON_TOGGLE_SIDEBAR,
    ICON_UPLOAD,
    ICON_PRINT,
    ICON_DOWNLOAD,
    ICON_TOGGLE_CHAT,
    ICON_SETTINGS,
)
import config


class TopBar(QWidget):
    """Top bar with app title, document name and action buttons"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the top bar ui"""
        self.setFixedHeight(config.TOPBAR_HEIGHT)

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_SECONDARY};
                color: {config.TEXT_PRIMARY};
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # App logo icon + title
        logo_label = QLabel()
        logo_label.setPixmap(
            svg_to_icon(ICON_LOGO, color=config.TEXT_ACCENT, size=18).pixmap(18, 18)
        )
        layout.addWidget(logo_label)

        app_title = QLabel("Documind")
        app_title.setStyleSheet(f"""
            font-size: {config.FONT_SIZE_LARGE};
            font-weight: 600;
            color: {config.TEXT_ACCENT};
            padding: 0px 4px;
            background-color: transparent;
        """)
        layout.addWidget(app_title)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"color: {config.BORDER_COLOR};")
        layout.addWidget(separator)

        # Document name
        self.doc_name = QLabel("No document loaded")
        self.doc_name.setStyleSheet(f"""
            font-size: {config.FONT_SIZE_NORMAL};
            color: {config.TEXT_SECONDARY};
            padding: 0px 4px;
            background-color: transparent;
        """)
        layout.addWidget(self.doc_name)

        # Spacer
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Action buttons
        self.create_action_buttons(layout)

        self.setLayout(layout)

    def create_action_buttons(self, layout):
        """Create action buttons with SVG icons"""
        button_style = f"""
            QPushButton {{
                background-color: {config.BUTTON_BG};
                border: none;
                border-radius: {config.BUTTON_BORDER_RADIUS};
                padding: {config.BUTTON_PADDING};
                min-width: 32px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {config.BUTTON_HOVER_BG};
            }}
            QPushButton:pressed {{
                background-color: {config.BUTTON_ACTIVE_BG};
            }}
        """

        buttons = [
            (ICON_TOGGLE_SIDEBAR, "Toggle sidebar"),
            (ICON_UPLOAD,         "Upload PDF"),
            (ICON_PRINT,          "Print"),
            (ICON_TOGGLE_CHAT,    "Toggle AI chat"),
            (ICON_SETTINGS,       "Settings"),
        ]

        for icon_svg, tooltip in buttons:
            btn = QPushButton()
            btn.setIcon(svg_to_icon(icon_svg, color=config.ICON_COLOR, size=16))
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip(tooltip)
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

    def set_document_name(self, name):
        """Update the document name displayed"""
        self.doc_name.setText(name)