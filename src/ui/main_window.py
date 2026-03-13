"""
Main application window UI components and Layouts
"""

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from src.ui.top_bar import TopBar
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
        ── three panels ──────────────────────────────────────────────────
        Left (ExplorerPanel + StatusBar) | Center (toolbar + viewer) | Right (AI chat)
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
        self.top_bar.upload_requested.connect(self._on_upload_requested)  # connect upload signal
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


    def _create_left_panel(self):
        """Explorer tree on top, status bar pinned to bottom."""
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

        # Explorer takes all available space
        self.explorer = ExplorerPanel(parent=panel)
        self.explorer.file_selected.connect(self._on_explorer_file_selected)

        # Status bar pinned to bottom
        self.status_bar = StatusBar(parent=panel)

        layout.addWidget(self.explorer, 1)
        layout.addWidget(self.status_bar)

        panel.setLayout(layout)
        return panel

    def _create_pdf_panel(self):
        """Center panel: PDFToolbar on top, PDFViewer below."""
        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background-color: {config.BG_PRIMARY}; }}")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.pdf_toolbar = PDFToolbar(parent=panel)
        self.pdf_viewer  = PDFViewer(parent=panel)

        # Toolbar → viewer
        self.pdf_toolbar.go_to_page.connect(self.pdf_viewer.go_to_page)
        self.pdf_toolbar.zoom_changed.connect(self.pdf_viewer.set_zoom)
        self.pdf_toolbar.fit_width_requested.connect(self.pdf_viewer.fit_width)
        self.pdf_toolbar.fit_page_requested.connect(self.pdf_viewer.fit_page)
        self.pdf_toolbar.rotate_requested.connect(self.pdf_viewer.rotate)

        # Viewer → toolbar
        self.pdf_viewer.page_changed.connect(self.pdf_toolbar.set_current_page)
        self.pdf_viewer.zoom_changed.connect(self.pdf_toolbar.set_zoom)
        self.pdf_viewer.pdf_loaded.connect(self.pdf_toolbar.set_total_pages)

        # Viewer → status bar (page count)
        self.pdf_viewer.pdf_loaded.connect(self._on_pdf_loaded_pages)

        layout.addWidget(self.pdf_toolbar)
        layout.addWidget(self.pdf_viewer)
        panel.setLayout(layout)
        return panel

    def _create_ai_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_SECONDARY};
                border-left: 1px solid {config.BORDER_COLOR};
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("AI Assistant")
        title.setStyleSheet(f"""
            font-size: 14px; font-weight: bold;
            color: {config.TEXT_PRIMARY}; padding: 5px 0;
        """)
        self.chat_label = QLabel("Load a file first")
        self.chat_label.setStyleSheet(f"color: {config.TEXT_SECONDARY};")
        self.chat_label.setAlignment(Qt.AlignTop)

        layout.addWidget(title)
        layout.addWidget(self.chat_label)
        layout.addStretch()
        panel.setLayout(layout)
        return panel


    def _on_upload_requested(self):
        """Open file dialog when upload button in top bar is clicked."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        if file_path:
            self.load_pdf(file_path)

    def _on_pdf_loaded_pages(self, page_count: int):
        """Forward page count to status bar after PDF is rendered."""
        if self.current_pdf:
            self.status_bar.update_file(self.current_pdf, page_count)

    def _on_explorer_file_selected(self, filepath: str):
        """User clicked a file in the explorer — load it."""
        self.load_pdf(filepath)



    def load_pdf(self, pdf_path: str):
        """
        Load a PDF — called by App when the user picks a file,
        or by the explorer when a file is clicked.
        """
        self.current_pdf = pdf_path
        filename = os.path.basename(pdf_path)

        # Update top bar
        self.top_bar.set_document_name(filename)

        # Add to explorer and mark active
        self.explorer.add_file(pdf_path)

        # Render PDF (triggers pdf_loaded → toolbar + status bar)
        self.pdf_viewer.load_pdf(pdf_path)

        # Update chat panel
        self.chat_label.setText(f"Ready to chat about:\n\n{filename}")

        # set the opened pdf
        self.pdf_opened.emit(pdf_path)

    def set_pipeline_status(self, message: str):
            """
            Updates the status bar with the current RAG pipeline phase.
            """
            if hasattr(self, 'status_bar'):
                self.status_bar.set_status_text(message) 