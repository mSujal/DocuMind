"""
Main application window UI components and Layouts
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from PyQt5.QtCore import Qt
# from top_bar import TopBar
from src.ui.top_bar import TopBar
# from pdf_toolbar import PDFToolbar
# from pdf_viewer import PDFViewer
import config


class MainWindow(QWidget):
    """
    Main window containing the user interface

    Provides all the containers, widgets, labels and buttons
    Responsible for handling the user interactions and updates displays accordingly
    """

    def __init__(self):
        """Initialize the main window"""
        super().__init__()
        self.current_pdf = None
        self.init_ui()

    def init_ui(self):
        """Setup the user interface components and layouts"""
        # Set widget styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {config.BG_PRIMARY};
                color: {config.TEXT_PRIMARY};
                font-family: {config.FONT_FAMILY};
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create top bar
        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)
        
        # Create three-panel layout
        panels_layout = QHBoxLayout()
        panels_layout.setContentsMargins(0, 0, 0, 0)
        panels_layout.setSpacing(0)
        
        # Left panel - Explorer
        self.left_panel = self.create_explorer_panel()
        
        # Center panel - PDF Viewer
        self.center_panel = self.create_pdf_viewer_panel()
        
        # Right panel - AI Assistant
        self.right_panel = self.create_ai_assistant_panel()
        
        # Add panels to layout with proportions (1:3:2 ratio approximately)
        panels_layout.addWidget(self.left_panel, 1)
        panels_layout.addWidget(self.center_panel, 3)
        panels_layout.addWidget(self.right_panel, 2)
        
        # Add panels layout to main layout
        main_layout.addLayout(panels_layout)
        
        self.setLayout(main_layout)
    
    def create_explorer_panel(self):
        """Create the left explorer panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_SECONDARY};
                border-right: 1px solid {config.BORDER_COLOR};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Explorer title
        title = QLabel("EXPLORER")
        title.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {config.TEXT_SECONDARY};
            padding: 5px 0;
        """)
        
        # Placeholder content
        content = QLabel("File tree will go here")
        content.setStyleSheet(f"color: {config.TEXT_SECONDARY};")
        content.setAlignment(Qt.AlignTop)
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def create_pdf_viewer_panel(self):
        """Create the center PDF viewer panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder for PDF viewer
        viewer = QLabel("PDF Viewer")
        viewer.setAlignment(Qt.AlignCenter)
        viewer.setStyleSheet(f"""
            font-size: 24px;
            color: {config.TEXT_SECONDARY};
        """)
        
        layout.addWidget(viewer)
        
        panel.setLayout(layout)
        return panel
    
    def create_ai_assistant_panel(self):
        """Create the right AI assistant panel"""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {config.BG_SECONDARY};
                border-left: 1px solid {config.BORDER_COLOR};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # AI Assistant title
        title = QLabel("AI Assistant")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {config.TEXT_PRIMARY};
            padding: 5px 0;
        """)
        
        # Placeholder content
        content = QLabel("Chat interface will go here")
        content.setStyleSheet(f"color: {config.TEXT_SECONDARY};")
        content.setAlignment(Qt.AlignTop)
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel

    # def load_pdf(self, pdf_path):
    #     """
    #     Load a PDF file and update the display
        
    #     Args:
    #         pdf_path (str): Path to the PDF file to load
    #     """
    #     self.current_pdf = pdf_path
        
    #     # Extract filename from path
    #     import os
    #     filename = os.path.basename(pdf_path)
        
    #     # Update top bar with document name
    #     self.top_bar.set_document_name(filename)
        
    #     # Update PDF viewer
    #     self.pdf_viewer.load_pdf(pdf_path)
        
    #     # Reset to first page
    #     self.pdf_toolbar.current_page = 1
    #     self.pdf_toolbar.page_input.setText("1")
    #     self.pdf_toolbar.update_nav_buttons()
        
    #     print(f"PDF loaded: {pdf_path}")