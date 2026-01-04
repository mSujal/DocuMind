"""Main application window UI components and Layouts"""

import config
import os
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

class MainWindow(QWidget):
    """
    Main windoe containing the user interface

    Provides all the containers, widgets, labels and buttons
    Responsible for handling the user interactions and updates displays accordingly
    """

    def __init__(self):
        """Initialize the main window"""
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Setup the iser interface and components and layouts"""
        # Layout creation
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # create three sections
        self.left_sidebar = self.create_left_sidebar() # doc preview
        self.center_area = self.create_center_area() # pdf doc 
        self.right_sidebar = self.create_right_sidebar() # chat 

        # adding sections to main layouts
        main_layout.addWidget(self.left_sidebar, 1) # 1 part preview area 
        main_layout.addWidget(self.center_area, 2) # 2 part pdf area 
        main_layout.addWidget(self.right_sidebar, 2) # 2 part chat area

        # set the layout
        self.setLayout(main_layout)

    def create_left_sidebar(self):
        """Creates and returns left sidebar"""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setStyleSheet(f"""
            background-color: {config.SIDEBAR_BG};
            border-right: {config.SIDEBAR_BORDER_RIGHT}
        """)

        sidebar.setMinimumWidth(config.SIDEBAR_MIN_WIDTH)
        sidebar.setMaximumWidth(config.SIDEBAR_MAX_WIDTH)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # sidebar titles
        title = QLabel("Navigation")
        title.setStyleSheet(f"""
            font-size: {config.SIDEBAR_TITLE_FONT_SIZE}; 
            font-weight: {config.SIDEBAR_TITLE_FONT_WEIGHT}; 
            padding: {config.SIDEBAR_TITLE_PADDING}
        """
        )
        layout.addWidget(title)

        # control buttons (placeholder for now)
        btn1 = QPushButton("Thumbnails")
        btn2 = QPushButton("Bookmarks")
        btn3 = QPushButton("Annotations")

        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        layout.addStretch() # push all to the top

        sidebar.setLayout(layout)
        return sidebar

    def create_center_area(self):
        """Creates and returns the center (PDF viwer) area"""
        center = QFrame()
        center.setFrameShape(QFrame.StyledPanel)
        center.setStyleSheet(
            f"background-color: {config.CENTER_BG}"
        )

        layout = QVBoxLayout()

        self.pdf_label = QLabel("NO PDF LOADED ˙◠˙")
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_label.setStyleSheet(f"""
            background-color: "#666";
            font-size: 16px;
            padding: 20px;
        """)
        layout.addWidget(self.pdf_label)

        center.setLayout(layout)
        return center
    
    def create_right_sidebar(self):
        """Creates and returns right sidebar"""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setStyleSheet(f"""
            background-color: {config.SIDEBAR_BG}; 
            border-left: {config.SIDEBAR_BORDER_LEFT}
        """)
        sidebar.setMinimumWidth(config.SIDEBAR_MIN_WIDTH)
        sidebar.setMaximumWidth(config.SIDEBAR_MAX_WIDTH)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # sidebar titles
        title = QLabel("Chat")
        title.setStyleSheet( f"""
            font-size: {config.SIDEBAR_TITLE_FONT_SIZE}; 
            font-weight: {config.SIDEBAR_TITLE_FONT_WEIGHT}; 
            padding: {config.SIDEBAR_TITLE_PADDING}
        """)
        layout.addWidget(title)

        self.chat_label = QLabel('Load a file first')
        self.chat_label.setStyleSheet(f"""
            font-size: {config.SIDEBAR_TITLE_FONT_SIZE};
            padding: {config.SIDEBAR_FONT_PADDING}
        """)

        layout.addWidget(self.chat_label)
        sidebar.setLayout(layout)
        return sidebar


    def load_pdf(self, pdf_path):
        """
        Load and Display PDF file

        Args:
            pdf_path (str): path to the pdf file
        """
        filename = os.path.basename(pdf_path)
        filesize = os.path.getsize(pdf_path)
        # need to implement the pdf loading here
        self.pdf_label.setText(
            f"Loaded ˙◡˙.✦ ݁˖\n\n" 
            f"file: {filename} \n\n"
            f"{pdf_path}"
        )

        self.chat_label.setText(f"Ready to chat about:\n\n{filename}")

 
    def on_button_clicked(self):
        """Just a placeholder butten action. No need for the application itself"""
        self.label.setText(f"Button clicked")
    
