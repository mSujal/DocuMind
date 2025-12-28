"""Main application window UI components and Layouts"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

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
        layout = QVBoxLayout()

        ############### just as placeholders
        # widgets
        self.label = QLabel('Hello World')
        self.button = QPushButton('Click')

        # connect signal
        self.button.clicked.connect(self.on_button_clicked)
        ######################################
        # adding widget to layout
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        # set the layout
        self.setLayout(layout)

    def load_pdf(self, pdf_path):
        """
        Load and Display PDF file

        Args:
            pdf_path (str): path to the pdf file
        """
        # need to implement the pdf loading here
        self.label.setText(f"Loaded file from {pdf_path}")

 
    def on_button_clicked(self):
        """Just a placeholder butten action. No need for the application itself"""
        self.label.setText(f"Button clicked")
    
