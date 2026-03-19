"""
AI Assistant Chat Panel UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit,
    QScrollArea, QFrame, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import config


# ─────────────────────────────────────────────────────────────────────────────
#  Background worker — keeps UI responsive during LLM call
# ─────────────────────────────────────────────────────────────────────────────

class QueryWorker(QThread):
    result_ready   = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, pipeline, question: str, mode: str = "qna"):
        super().__init__()
        self.pipeline = pipeline
        self.question = question
        self.mode     = mode

    def run(self):
        try:
            if self.mode == "mcq":
                answer = self.pipeline.query_mcq(self.question)
            else:
                answer = self.pipeline.query_qna(self.question)
            self.result_ready.emit(answer)
        except Exception as exc:
            self.error_occurred.emit(f"Error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  Typing indicator
# ─────────────────────────────────────────────────────────────────────────────

class TypingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_TERTIARY};
                border-radius: 8px;
                border: 1px solid {config.BORDER_COLOR};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)

        self._dots = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setFont(QFont("Arial", 7))
            dot.setStyleSheet(f"color: {config.TEXT_SECONDARY}; background: transparent;")
            layout.addWidget(dot)
            self._dots.append(dot)

        layout.addStretch()

        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._tick)
        self._step = 0
        self._timer.start()

    def _tick(self):
        for i, dot in enumerate(self._dots):
            active = (i == self._step % 3)
            dot.setStyleSheet(
                f"color: {config.TEXT_ACCENT if active else config.BORDER_COLOR}; background: transparent;"
            )
        self._step += 1

    def stop(self):
        self._timer.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Chat Panel
# ─────────────────────────────────────────────────────────────────────────────

class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pipeline       = None
        self._worker         = None
        self._typing_widget  = None
        self._mode           = "qna"
        self._init_ui()

    # ── public API ────────────────────────────────────────────────────

    def set_pipeline(self, pipeline):
        """Attach a ready RAGPipeline instance."""
        self._pipeline = pipeline

    def set_mode(self, mode: str):
        """Switch between 'qna' and 'mcq' — call from outside."""
        self._mode = mode

    # ── UI ────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setStyleSheet(f"QWidget {{ background-color: {config.BG_SECONDARY}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── scroll area ───────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {config.BG_PRIMARY};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {config.SCROLLBAR_HANDLE};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet("background: transparent;")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._chat_layout.setContentsMargins(10, 12, 10, 12)
        self._chat_layout.setSpacing(8)

        self._scroll.setWidget(self._chat_container)
        root.addWidget(self._scroll, 1)

        # ── input row ─────────────────────────────────────────────────
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_TERTIARY};
                border-top: 1px solid {config.BORDER_COLOR};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(8)

        self._input = QTextEdit()
        self._input.setFixedHeight(52)
        self._input.setPlaceholderText("Ask something about the document...")
        self._input.setFont(QFont(config.FONT_FAMILY, 10))
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {config.BG_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 6px;
                padding: 6px 8px;
                color: {config.TEXT_PRIMARY};
                font-size: {config.FONT_SIZE_NORMAL};
            }}
            QTextEdit:focus {{
                border-color: {config.TEXT_ACCENT};
            }}
        """)
        self._input.installEventFilter(self)

        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(40, 40)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.TEXT_ACCENT};
                border: none;
                border-radius: 6px;
                color: {config.BG_PRIMARY};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3ab49a;
            }}
            QPushButton:pressed {{
                background-color: #2d9080;
            }}
            QPushButton:disabled {{
                background-color: {config.BG_QUATERNARY};
                color: {config.TEXT_SECONDARY};
            }}
        """)
        self._send_btn.clicked.connect(self.handle_send)

        input_layout.addWidget(self._input)
        input_layout.addWidget(self._send_btn)

        root.addWidget(input_frame)

    # ── enter key ─────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self._input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.handle_send()
                    return True
        return super().eventFilter(obj, event)

    # ── messages ──────────────────────────────────────────────────────

    def add_message(self, message: str, is_user: bool = False):
        # Outer row widget to control left/right alignment with max width
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        bubble = QFrame()
        bubble.setMaximumWidth(int(self.width() * 0.82) if self.width() > 100 else 320)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setFont(QFont(config.FONT_FAMILY, 10))
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        if is_user:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {config.BUTTON_ACTIVE_BG};
                    border-radius: 8px;
                    border: 1px solid #1a6fa8;
                }}
                QLabel {{ color: {config.TEXT_PRIMARY}; background: transparent; }}
            """)
            bubble_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(bubble)
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {config.BG_TERTIARY};
                    border-radius: 8px;
                    border: 1px solid {config.BORDER_COLOR};
                }}
                QLabel {{ color: {config.TEXT_PRIMARY}; background: transparent; }}
            """)
            bubble_layout.addWidget(label)
            row_layout.addWidget(bubble)
            row_layout.addStretch()

        self._chat_layout.addWidget(row)
        self._scroll_to_bottom()

    # ── send / receive ────────────────────────────────────────────────

    def handle_send(self):     
        text = self._input.toPlainText().strip()
        if not text or self._worker is not None:
            return

        self._input.clear()
        self.add_message(text, is_user=True)

        if self._pipeline is None:
            self.add_message(
                "No document loaded yet. Open a PDF to get started.",
                is_user=False,
            )
            return

        self._show_typing()
        self._send_btn.setEnabled(False)

        self._worker = QueryWorker(self._pipeline, text, mode=self._mode)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _on_result(self, answer: str):
        self._hide_typing()
        self.add_message(answer, is_user=False)

    def _on_error(self, msg: str):
        self._hide_typing()
        self.add_message(msg, is_user=False)

    def _on_done(self):
        self._worker = None
        self._send_btn.setEnabled(True)

    # ── typing indicator ──────────────────────────────────────────────

    def _show_typing(self):
        self._typing_widget = TypingIndicator()
        self._chat_layout.addWidget(self._typing_widget, alignment=Qt.AlignLeft)
        self._scroll_to_bottom()

    def _hide_typing(self):
        if self._typing_widget:
            self._typing_widget.stop()
            self._chat_layout.removeWidget(self._typing_widget)
            self._typing_widget.deleteLater()
            self._typing_widget = None

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))
