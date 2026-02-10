"""
Top bar component containing the document title and the action buttons
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
import config


class TopBar(QWidget):
    """Top bar with app title, document name and action buttons"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the top bar ui"""
        self.setFixedHeight(config.TOPBAR_HEIGHT)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.TOPBAR_BG};
                color: {config.TEXT_PRIMARY};
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)
        
        # app icon(maybe) and title
        app_title = QLabel("Documind")
        app_title.setStyleSheet(f"""
            font-size: {config.FONT_SIZE_LARGE};
            font-weight: 600;
            color: {config.TEXT_ACCENT};
            padding: 0px 8px;
            background-color: transparent;
        """)
        layout.addWidget(app_title)
        
        # seperator plane 
        seperator = QFrame()
        seperator.setFrameShape(QFrame.VLine)
        seperator.setStyleSheet(f"color: {config.BORDER_COLOR};")
        layout.addWidget(seperator)
        
        # Document name
        self.doc_name = QLabel("DocName.pdf")
        self.doc_name.setStyleSheet(f"""
            font-size: {config.FONT_SIZE_NORMAL};
            color: {config.TEXT_SECONDARY};
            padding: 0px 4px;
            background-color: transparent;
        """)
        layout.addWidget(self.doc_name)
        
        # spacer to push buttons to the right
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Action buttons
        self.create_action_buttons(layout)
        
        self.setLayout(layout)
    
    def create_action_buttons(self, layout):
        """create action buttons"""
        button_style = f"""
            QPushButton {{
                background-color: {config.BUTTON_BG};
                border: none;
                border-radius: {config.BUTTON_BORDER_RADIUS};
                padding: {config.BUTTON_PADDING};     
                color: {config.ICON_COLOR};
                font-size: 16px;
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
        
        # Button icons (using unicode symbols)
        buttons = [
            ("⊟", "Split view"),
            ("", "Upload"),
            ("🖨", "Print"),
            ("↓", "Download"),
            ("💬", "Comments"),
            ("⚙", "Settings"),
        ]
        
        for icon_text, tooltip in buttons:
            btn = QPushButton(icon_text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
    
    def set_document_name(self, name):
        """Update the document name displayed"""
        self.doc_name.setText(name)  