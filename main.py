import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap
from pages.scraper_page import ScraperPage
from modules.logger import get_logger
logger = get_logger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        logger.info("Initializing MainWindow for Google Business Scraper")
        
        self.setWindowTitle("Google Business Scraper")
        self.setGeometry(100, 100, 800, 600)
        
        self.set_icon("assets/icon.ico")
        
        self.stacked_widget = QStackedWidget()

        self.pages = {
            "scraper_page": ScraperPage(),
        }
        logger.info(f"Pages initialized: {list(self.pages.keys())}")
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.stacked_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        try:
            self.load_stylesheet("styles/scraper_styles.qss")
            logger.info("Stylesheet loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load stylesheet: {e}")

    def load_stylesheet(self, path):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, path)
        try:
            with open(full_path, "r") as file:
                self.setStyleSheet(file.read())
                logger.debug(f"Stylesheet applied from {full_path}")
        except FileNotFoundError:
            logger.error(f"Stylesheet file not found at {full_path}")
        except Exception as e:
            logger.exception(f"Unexpected error while loading stylesheet: {e}")
    
    def set_icon(self, path):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, path)
        try:
            my_pixmap = QPixmap(icon_path)
            my_icon = QIcon(my_pixmap)
            self.setWindowIcon(my_icon)
            logger.info("Icon loaded successfully")
        except Exception as e:
            logger.error(f"Failed to set icon: {e}")


if __name__ == "__main__":
    logger.info("Application started")
    app = QApplication(sys.argv)
    window = MainWindow()
    logger.info("MainWindow is being shown")
    window.show()
    try:
        sys.exit(app.exec())
        logger.info("Application exited successfully")
    except Exception as e:
        logger.exception(f"Application crashed: {e}")