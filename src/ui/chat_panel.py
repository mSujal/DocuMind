"""
AI Assistant Chat Panel UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit,
    QScrollArea, QFrame, QLabel, QSizePolicy,
    QStackedWidget, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import config
import re


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


#-----------------------------------------------------------
# Mcq parser
#-----------------------------------------------------------

# def parse_mcq_response(text):
#     questions = []

#     # split mcq markers
#     blocks = re.split(r'\*{0,2}MCQ\s*\d+[:.]\*{0,2}\s*', text, flags=re.IGNORECASE)
#     blocks = [b.strip() for b in blocks if b.strip()]

#     for block in blocks:
#         lines = [l.strip() for l in block.splitlines() if l.strip()]
#         if not lines:
#             continue

#         question_lines = []
#         option_lines = []
#         answer_lines = []
#         in_option = False
#         in_answer = False

#         for line in lines:
#             if re.match(r'^[A-D][(.]', line):
#                 in_option = True
#                 in_answer = False
#                 option_lines.append(line)
#             elif re.match(r'^\*{0,2}Answer\*{0,2}[:.]\s*', line, re.IGNORECASE):
#                 in_option = False
#                 in_answer = True
#                 # strip Answer prefic
#                 answer = re.sub(r'^\*{0,2}Answer\*{0,2}[:.]\s*', '', line, flags=re.IGNORECASE).strip()
#                 if answer:
#                     answer_lines.append(answer)
#                 elif in_answer:
#                     answer_lines.append(line)
#                 elif in_option:
#                     option_lines.append(line)
#                 else:
#                     question_lines.append(line)

#         question_text = ' '.join(question_lines).strip()
#         # clean markdow bold (sometimes visible)
#         question_text = re.sub(r'\*+', '', question_text).strip()

#         options = []
#         for option_line in option_lines:
#             cleaned = re.sub(r'^[A-D][).]\s*', '', option_line).strip()
#             options.append(cleaned)

#         #determine answer letter
#         answer_text = ' '.join(answer_lines).strip()
#         answer_text = re.sub(r'\*+', '', answer_text).strip()
#         answer_letter = None
#         m = re.match(r'^([A-D])[).:]?\s*(.*)', answer_text, re.DOTALL)

#         if m:
#             answer_letter = m.group(1)
#             explanation = m.group(2).strip()
#         else:
#             explanation = answer_text

#         if question_text and len(options) >=2 :
#             questions.append({
#                 'question':      question_text,
#                 'options':       options,
#                 'answer_letter': answer_letter,   # 'A','B','C','D' or None
#                 'explanation':   explanation,
#             })

#     return questions

def parse_mcq_response(text):
    questions = []

    # Split into blocks on "Question:" — handles single or multiple MCQs
    blocks = re.split(r'(?:^|\n)(?:Question:\s*)', text, flags=re.IGNORECASE)
    blocks = [b.strip() for b in blocks if b.strip()]

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        question_lines = []
        option_lines   = []
        answer_letter  = None
        explanation    = ""

        for line in lines:
            if re.match(r'^[(\[]?[A-D][)\].][\s)]', line):
                option_lines.append(line)
            elif re.match(r'^Correct Answer:\s*', line, re.IGNORECASE):
                rest = re.sub(r'^Correct Answer:\s*', '', line, flags=re.IGNORECASE).strip()
                m = re.match(r'^([A-D])', rest)
                if m:
                    answer_letter = m.group(1)
            elif re.match(r'^Explanation:\s*', line, re.IGNORECASE):
                explanation = re.sub(r'^Explanation:\s*', '', line, flags=re.IGNORECASE).strip()
            elif not option_lines and not answer_letter:
                question_lines.append(line)

        question_text = ' '.join(question_lines).strip()

        options = []
        for ol in option_lines:
            cleaned = re.sub(r'^[A-D]\)\s*', '', ol).strip()
            options.append(cleaned)

        if question_text and len(options) >= 2:
            questions.append({
                'question':      question_text,
                'options':       options,
                'answer_letter': answer_letter,
                'explanation':   explanation,
            })

    return questions

#-----------------------------------------------------------
# Mcq card widget
#-----------------------------------------------------------
OPTION_LETTERS = ['A', 'B', 'C', 'D']

class MCQCard(QFrame):
    def __init__(self, q_index, total, data):
        super().__init__()
        self._data = data
        self._selected = None
        self._revealed = False
        self._option_btns = {}

        self.setStyleSheet(f"""
            QFrame#mcqCard {{
                background-color: {config.BG_TERTIARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 10px;
            }}
        """)
        self.setObjectName("mcqCard")
 
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)
 
        # ── header: "Q 1 / 5" ────────────────────────────────────────
        header = QLabel(f"Question {q_index} of {total}")
        header.setStyleSheet(f"""
            color: {config.TEXT_ACCENT};
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        """)
        root.addWidget(header)
 
        # ── question text ─────────────────────────────────────────────
        q_label = QLabel(data['question'])
        q_label.setWordWrap(True)
        q_label.setStyleSheet(f"""
            color: {config.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            padding-bottom: 4px;
        """)
        root.addWidget(q_label)
 
        # ── options ───────────────────────────────────────────────────
        opts_frame = QFrame()
        opts_frame.setStyleSheet("background: transparent;")
        opts_layout = QVBoxLayout(opts_frame)
        opts_layout.setContentsMargins(0, 0, 0, 0)
        opts_layout.setSpacing(6)
 
        for i, opt_text in enumerate(data['options'][:4]):
            letter = OPTION_LETTERS[i]
            btn = QPushButton(f"  {letter}.  {opt_text}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._option_style_default())
            btn.clicked.connect(lambda checked, l=letter: self._on_option_clicked(l))
            opts_layout.addWidget(btn)
            self._option_btns[letter] = btn
 
        root.addWidget(opts_frame)
 
        # ── reveal button ─────────────────────────────────────────────
        self._reveal_btn = QPushButton("Reveal Answer")
        self._reveal_btn.setEnabled(False)
        self._reveal_btn.setCursor(Qt.PointingHandCursor)
        self._reveal_btn.setStyleSheet(self._reveal_btn_style(enabled=False))
        self._reveal_btn.clicked.connect(self._reveal_answer)
        root.addWidget(self._reveal_btn)
 
        # ── answer + explanation (hidden) ─────────────────────────────
        self._answer_frame = QFrame()
        self._answer_frame.setVisible(False)
        self._answer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        af_layout = QVBoxLayout(self._answer_frame)
        af_layout.setContentsMargins(12, 10, 12, 10)
        af_layout.setSpacing(4)
 
        ans_letter = data.get('answer_letter', '?')
        ans_header = QLabel(f"✓  Correct Answer: {ans_letter}")
        ans_header.setStyleSheet(f"""
            color: #4ec994;
            font-weight: 700;
            font-size: 13px;
            background: transparent;
        """)
        af_layout.addWidget(ans_header)
 
        if data.get('explanation'):
            exp_label = QLabel(data['explanation'])
            exp_label.setWordWrap(True)
            exp_label.setStyleSheet(f"""
                color: {config.TEXT_SECONDARY};
                font-size: 12px;
                background: transparent;
                padding-top: 2px;
            """)
            af_layout.addWidget(exp_label)
 
        root.addWidget(self._answer_frame)
 
    # ── styles ────────────────────────────────────────────────────────
 
    def _option_style_default(self):
        return f"""
            QPushButton {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {config.TEXT_ACCENT};
                background-color: {config.BG_TERTIARY};
            }}
        """
 
    def _option_style_selected(self):
        return f"""
            QPushButton {{
                background-color: {config.BUTTON_ACTIVE_BG};
                color: {config.TEXT_PRIMARY};
                border: 2px solid {config.TEXT_ACCENT};
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
            }}
        """
 
    def _option_style_correct(self):
        return f"""
            QPushButton {{
                background-color: #1a3d2b;
                color: #4ec994;
                border: 2px solid #4ec994;
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
            }}
        """
 
    def _option_style_wrong(self):
        return f"""
            QPushButton {{
                background-color: #3d1a1a;
                color: #e06c75;
                border: 2px solid #e06c75;
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
            }}
        """
 
    def _option_style_dimmed(self):
        return f"""
            QPushButton {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_SECONDARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 10px;
                text-align: left;
                font-size: 12px;
            }}
        """
 
    def _reveal_btn_style(self, enabled: bool):
        if enabled:
            return f"""
                QPushButton {{
                    background-color: {config.TEXT_ACCENT};
                    color: {config.BG_PRIMARY};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: #3ab49a; }}
                QPushButton:pressed {{ background-color: #2d9080; }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {config.BG_QUATERNARY};
                    color: {config.TEXT_SECONDARY};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                }}
            """
 
    # ── interaction ───────────────────────────────────────────────────
 
    def _on_option_clicked(self, letter: str):
        if self._revealed:
            return
        self._selected = letter
        for l, btn in self._option_btns.items():
            btn.setStyleSheet(
                self._option_style_selected() if l == letter else self._option_style_default()
            )
        self._reveal_btn.setEnabled(True)
        self._reveal_btn.setStyleSheet(self._reveal_btn_style(enabled=True))
 
    def _reveal_answer(self):
        if self._revealed:
            return
        self._revealed = True
        correct = self._data.get('answer_letter')
 
        for letter, btn in self._option_btns.items():
            btn.setEnabled(False)
            if letter == correct:
                btn.setStyleSheet(self._option_style_correct())
            elif letter == self._selected:
                btn.setStyleSheet(self._option_style_wrong())
            else:
                btn.setStyleSheet(self._option_style_dimmed())
 
        self._reveal_btn.setVisible(False)
        self._answer_frame.setVisible(True)


# ------------------------------------------------------
# mcq panel
# ------------------------------------------------------
class MCQPanel(QWidget):
    def __init__(self, questions):
        super().__init__()
        self._questions = questions
        self._index = 0
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        # Scrollable card area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {config.BG_PRIMARY};
                width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {config.SCROLLBAR_HANDLE};
                border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
 
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._stack_layout = QVBoxLayout(container)
        self._stack_layout.setContentsMargins(10, 12, 10, 12)
        self._stack_layout.setAlignment(Qt.AlignTop)
 
        # Build all cards; only first is visible
        self._cards = []
        total = len(self._questions)
        for i, q in enumerate(self._questions):
            card = MCQCard(i + 1, total, q)
            card.setVisible(i == 0)
            self._stack_layout.addWidget(card)
            self._cards.append(card)
 
        scroll.setWidget(container)
        root.addWidget(scroll, 1)
 
        # Navigation bar
        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_TERTIARY};
                border-top: 1px solid {config.BORDER_COLOR};
            }}
        """)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 8, 12, 8)
        nav_layout.setSpacing(8)
 
        self._prev_btn = QPushButton("← Prev")
        self._next_btn = QPushButton("Next →")
        self._counter  = QLabel()
        self._counter.setAlignment(Qt.AlignCenter)
        self._counter.setStyleSheet(f"color: {config.TEXT_SECONDARY}; background: transparent; font-size: 12px;")
 
        nav_btn_style = f"""
            QPushButton {{
                background-color: {config.BUTTON_BG};
                color: {config.TEXT_PRIMARY};
                border: 1px solid {config.BORDER_COLOR};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {config.BUTTON_HOVER_BG}; }}
            QPushButton:disabled {{
                color: {config.TEXT_SECONDARY};
                background-color: {config.BG_QUATERNARY};
                border-color: {config.BORDER_COLOR};
            }}
        """
        self._prev_btn.setStyleSheet(nav_btn_style)
        self._next_btn.setStyleSheet(nav_btn_style)
        self._prev_btn.setCursor(Qt.PointingHandCursor)
        self._next_btn.setCursor(Qt.PointingHandCursor)
 
        self._prev_btn.clicked.connect(self._go_prev)
        self._next_btn.clicked.connect(self._go_next)
 
        nav_layout.addWidget(self._prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self._counter)
        nav_layout.addStretch()
        nav_layout.addWidget(self._next_btn)
 
        nav_frame.setFixedHeight(48)
        root.addWidget(nav_frame)
 
        self._update_nav()
 
    def _show_card(self, index: int):
        for i, card in enumerate(self._cards):
            card.setVisible(i == index)
        self._index = index
        self._update_nav()
 
    def _go_prev(self):
        if self._index > 0:
            self._show_card(self._index - 1)
 
    def _go_next(self):
        if self._index < len(self._cards) - 1:
            self._show_card(self._index + 1)
 
    def _update_nav(self):
        total = len(self._cards)
        self._counter.setText(f"{self._index + 1} / {total}")
        self._prev_btn.setEnabled(self._index > 0)
        self._next_btn.setEnabled(self._index < total - 1)
 

# ------------------------------------------------------------
# Chat Panel
# ------------------------------------------------------------

class ChatPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pipeline       = None
        self._worker         = None
        self._typing_widget  = None
        self._mode           = "qna"
        self._init_ui()


    def set_pipeline(self, pipeline):
        """Attach a ready RAGPipeline instance."""
        self._pipeline = pipeline

    def set_mode(self, mode: str):
        """Switch between 'qna' and 'mcq'"""
        self._mode = mode
        if mode == "mcq":
            self._input.setPlaceholderText("Ask to generate MCQ questions")
        else:
            self._input.setPlaceholderText("Ask something about document")

    def _init_ui(self):
        self.setStyleSheet(f"QWidget {{ background-color: {config.BG_SECONDARY}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")

        self._chat_page = QWidget()
        self._chat_page.setStyleSheet("background: transparent;")
        chat_page_layout = QVBoxLayout(self._chat_page)
        chat_page_layout.setContentsMargins(0, 0, 0, 0)

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
        chat_page_layout.addWidget(self._scroll)

        self._mcq_page = QWidget()
        self._mcq_page.setStyleSheet("background: transparent;")
        self._mcq_page_layout = QVBoxLayout(self._mcq_page)
        self._mcq_page_layout.setContentsMargins(0, 0, 0, 0)
        self._mcq_placeholder()

        self._stack.addWidget(self._chat_page)
        self._stack.addWidget(self._mcq_page)

        root.addWidget(self._stack, 1)

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


    def _mcq_placeholder(self):
        """Empty state shown before any MCQ is generated."""
        ph = QLabel("Switch to MCQ mode and ask a question\nto generate interactive questions.")
        ph.setAlignment(Qt.AlignCenter)
        ph.setWordWrap(True)
        ph.setStyleSheet(f"color: {config.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        self._mcq_page_layout.addStretch()
        self._mcq_page_layout.addWidget(ph)
        self._mcq_page_layout.addStretch()
 
    def _replace_mcq_panel(self, questions: list[dict]):
        """Swap the MCQ page content with a fresh MCQPanel."""
        # Remove all children from mcq_page_layout
        while self._mcq_page_layout.count():
            item = self._mcq_page_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
 
        panel = MCQPanel(questions)
        self._mcq_page_layout.addWidget(panel)
        self._stack.setCurrentIndex(1)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj is self._input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.handle_send()
                    return True
        return super().eventFilter(obj, event)

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


    def handle_send(self):     
        text = self._input.toPlainText().strip()
        if not text or self._worker is not None:
            return

        self._input.clear()
        self._stack.setCurrentIndex(0)
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

    def _on_result(self, answer):
        self._hide_typing()

        if self._mode == "mcq":
            questions = parse_mcq_response(answer)
            if questions:
                self._replace_mcq_panel(questions)
            else:
                self.add_message("Couldn't parse MCQ Format. Raw response:\n\n" + answer, is_user=False)
            
        else:
            self.add_message(answer, is_user=False)
            

    def _on_error(self, msg):
        self._hide_typing()
        self._stack.setCurrentIndex(0)
        self.add_message(msg, is_user=False)

    def _on_done(self):
        self._worker = None
        self._send_btn.setEnabled(True)

    def _show_typing(self):
        self._stack.setCurrentIndex(0)
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
