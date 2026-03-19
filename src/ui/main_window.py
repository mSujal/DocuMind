"""
Main application window UI components and Layouts
"""

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.top_bar import TopBar
from src.ui.chat_panel import ChatPanel
from src.ui.pdf_toolbar import PDFToolbar
from src.ui.pdf_viewer import PDFViewer
from src.ui.explorer_panel import ExplorerPanel
from src.ui.status_bar import StatusBar
import config


class MainWindow(QWidget):
    """
    Main window containing the user interface.

    Layout (top to bottom):
        TopBar
        Left (ExplorerPanel + StatusBar) | Center (toolbar + viewer) | Right (ChatPanel)
    """

    pdf_opened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_pdf = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                font-family: {config.FONT_FAMILY};
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.top_bar = TopBar()
        self.top_bar.upload_requested.connect(self._on_upload_requested)
        self.top_bar.toggle_explorer.connect(self._toggle_explorer)
        self.top_bar.toggle_chat.connect(self._toggle_chat)
        main_layout.addWidget(self.top_bar)

        panels_layout = QHBoxLayout()
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(0)

        self.left_panel   = self._create_left_panel()
        self.center_panel = self._create_pdf_panel()
        self.right_panel  = self._create_ai_panel()

        panels_layout.addWidget(self.left_panel,   1)
        panels_layout.addWidget(self.center_panel, 3)
        panels_layout.addWidget(self.right_panel,  2)

        main_layout.addLayout(panels_layout)
        self.setLayout(main_layout)

    # ------------------------------------------------------------------ #
    #  Panel builders                                                      #
    # ------------------------------------------------------------------ #

    def _create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_SECONDARY};
                border-right: 1px solid {config.BORDER_COLOR};
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.explorer = ExplorerPanel(parent=panel)
        self.explorer.file_selected.connect(self._on_explorer_file_selected)
        self.status_bar = StatusBar(parent=panel)

        layout.addWidget(self.explorer, 1)
        layout.addWidget(self.status_bar)
        panel.setLayout(layout)
        return panel

    def _create_pdf_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background-color: {config.BG_PRIMARY}; }}")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.pdf_toolbar = PDFToolbar(parent=panel)
        self.pdf_viewer  = PDFViewer(parent=panel)

        self.pdf_toolbar.go_to_page.connect(self.pdf_viewer.go_to_page)
        self.pdf_toolbar.zoom_changed.connect(self.pdf_viewer.set_zoom)
        self.pdf_toolbar.fit_width_requested.connect(self.pdf_viewer.fit_width)
        self.pdf_toolbar.fit_page_requested.connect(self.pdf_viewer.fit_page)
        self.pdf_toolbar.rotate_requested.connect(self.pdf_viewer.rotate)

        self.pdf_viewer.page_changed.connect(self.pdf_toolbar.set_current_page)
        self.pdf_viewer.zoom_changed.connect(self.pdf_toolbar.set_zoom)
        self.pdf_viewer.pdf_loaded.connect(self.pdf_toolbar.set_total_pages)
        self.pdf_viewer.pdf_loaded.connect(self._on_pdf_loaded_pages)

        layout.addWidget(self.pdf_toolbar)
        layout.addWidget(self.pdf_viewer)
        panel.setLayout(layout)
        return panel

    def _create_ai_panel(self):
        """Right panel — ChatPanel fills the entire space."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_SECONDARY};
                border-left: 1px solid {config.BORDER_COLOR};
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── optional "AI Assistant" title bar ─────────────────────────
        title_bar = QFrame()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_TERTIARY};
                border-bottom: 1px solid {config.BORDER_COLOR};
            }}
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title = QLabel("AI Assistant")
        title.setStyleSheet(f"""
            font-size: {config.FONT_SIZE_LARGE};
            font-weight: bold;
            color: {config.TEXT_PRIMARY};
        """)
        title_layout.addWidget(title)

        self.chat_panel = ChatPanel()

        layout.addWidget(title_bar)
        layout.addWidget(self.chat_panel)
        panel.setLayout(layout)
        return panel

    # ------------------------------------------------------------------ #
    #  Pipeline wiring                                                     #
    # ------------------------------------------------------------------ #

    def attach_pipeline(self, pipeline):
        """
        Call this after RAGPipeline.index() finishes to enable chat.

        In your App class:
            def _on_indexing_done(self, pipeline):
                self.main_window.attach_pipeline(pipeline)
        """
        self.chat_panel.set_pipeline(pipeline)

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #

    def _toggle_explorer(self):
        self.left_panel.setVisible(not self.left_panel.isVisible())

    def _toggle_chat(self):
        self.right_panel.setVisible(not self.right_panel.isVisible())

    def _on_upload_requested(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.load_pdf(file_path)

    def _on_pdf_loaded_pages(self, page_count: int):
        if self.current_pdf:
            self.status_bar.update_file(self.current_pdf, page_count)

    def _on_explorer_file_selected(self, filepath: str):
        self.load_pdf(filepath)

    # ------------------------------------------------------------------ #
    #  Load PDF                                                            #
    # ------------------------------------------------------------------ #

    def load_pdf(self, pdf_path: str):
        self.current_pdf = pdf_path
        filename = os.path.basename(pdf_path)

        self.top_bar.set_document_name(filename)
        self.explorer.add_file(pdf_path)
        self.pdf_viewer.load_pdf(pdf_path)

        self.pdf_opened.emit(pdf_path)

    def set_pipeline_status(self, message: str):
        if hasattr(self, "status_bar"):
            self.status_bar.set_status_text(message)
