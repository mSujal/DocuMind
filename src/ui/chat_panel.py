"""
AI Assistant Chat Panel UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
import config


class ChatPanel(QWidget):
    """Right sidebar AI Chat Interface"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # === Title ===
        title = QLabel("AI Assistant")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {config.TEXT_PRIMARY};
        """)
        # main_layout.addWidget(title)

        # === Chat Scroll Area ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_container.setLayout(self.chat_layout)

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area)

        # === Input Area ===
        input_layout = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setFixedHeight(50)
        self.input_field.setPlaceholderText("Ask something about the document...")
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {config.BG_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 6px;
                padding: 6px;
                color: {config.TEXT_PRIMARY};
            }}
        """)

        self.send_button = QPushButton("➤")
        self.send_button.setFixedWidth(40)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.TEXT_ACCENT};
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)

        self.send_button.clicked.connect(self.handle_send)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

    # =============================
    # Message Handling
    # =============================

    def handle_send(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        self.add_message(text, is_user=True)
        self.input_field.clear()

        # Dummy AI reply (replace later with real AI)
        self.add_message("This is a sample AI response.", is_user=False)

    def add_message(self, message, is_user=False):
        bubble = QFrame()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(10, 6, 10, 6)

        label = QLabel(message)
        label.setWordWrap(True)

        if is_user:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {config.TEXT_ACCENT};
                    border-radius: 8px;
                }}
                QLabel {{
                    color: white;
                }}
            """)
            bubble_layout.addWidget(label)
            bubble.setLayout(bubble_layout)
            self.chat_layout.addWidget(bubble, alignment=Qt.AlignRight)

        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {config.BG_PRIMARY};
                    border-radius: 8px;
                    border: 1px solid {config.BORDER_COLOR};
                }}
                QLabel {{
                    color: {config.TEXT_PRIMARY};
                }}
            """)
            bubble_layout.addWidget(label)
            bubble.setLayout(bubble_layout)
            self.chat_layout.addWidget(bubble, alignment=Qt.AlignLeft)

        # Auto-scroll
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )