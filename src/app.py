"""Initalization of the application"""

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction
from src.ui.main_window import MainWindow
import os

class App(QMainWindow):
    """
    Main Application class  

    Sets up the main windows, manage the application state and coordinate the ui compoments

    Attributes:
        main_winodw (MainWindoe) : central widget containig the ui
        current_pdf (str): path to currently opned pdf
    """

    def __init__(self):
        """Initalization of applicaition and main window"""
        super().__init__()
        self.current_pdf = None
        self.main_window = MainWindow()
        self.setCentralWidget(self.main_window)
        self.setup_menu()
        self.update_title()
        self.setGeometry(100, 100, 800, 600)
        # geometry is set as x, y, height, width

    def setup_menu(self):
        """setup application menu bar"""
        menubar = self.menuBar()

        # menu entries
        file_menu = menubar.addMenu("Files") # just for now...
        
        # action
        open_action = QAction("Open PDF", self)
        
        # could add the shortcuts...

        # triggers 
        open_action.triggered.connect(self.open_file_dialog)

        # action entries
        file_menu.addAction(open_action)

    def open_file_dialog(self):
        """Open file dialog to select a PDF file"""
        file_path, temp = QFileDialog.getOpenFileName(
            self, 
            'Open PDF File',
            '', 
            'PDF Files (*.pdf)'''
        ) # returns file path and file type

        if file_path:
            self.open_pdf(file_path)
            # print(temp)


    def open_pdf(self, pdf_path):
        """
        Open pdf file and update window title dynamically 
        
        Args: 
            pdf_path (str): path to pdf file
        """
        self.current_pdf = pdf_path
        self.update_title()
        
        # for now showing the pdf path in main windows
        self.main_window.load_pdf(pdf_path)
    
    def update_title(self):
        """Update window title based on opened pdf"""
        # print("updated title")
        if self.current_pdf:
            filename = os.path.basename(self.current_pdf)
            self.setWindowTitle(f"{filename} - DocuMind")
            # print(filename)
        else:
            self.setWindowTitle("DocuMind")


