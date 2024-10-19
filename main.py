import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QFrame, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QPixmap
from components.sidebar import Sidebar
from utils.page_manager import PageManager
from modules.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        logger.info("Initializing MainWindow for Google Business Scraper")
        
        self.setWindowTitle("Google Business Scraper")
        self.setGeometry(100, 100, 800, 600)
        
        self.set_icon("assets/icon.ico")
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        main_layout = QHBoxLayout(self.central_widget)
        self.page_manager = PageManager()
        menu_items = self.page_manager.get_menu_items()
        self.sidebar = Sidebar(self, [(info["name"], info["icon"]) for info in menu_items.values()])
        main_layout.addWidget(self.sidebar)

        self.content_area = QFrame(self)
        self.content_layout = QVBoxLayout(self.content_area)
        main_layout.addWidget(self.content_area)
        
        self.pages = {page_id: page for page_id, page in self.page_manager.pages.items()}
        
        self.current_page = None
        self.update_content("settings_page")
        self.sidebar.set_active_button(self.sidebar.findChild(QPushButton, "Ayarlar"))
        
        
        logger.info(f"Pages initialized: {list(self.pages.keys())}")

        try:
            self.load_stylesheet("styles/scraper_styles.qss")
            logger.info("Stylesheet loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load stylesheet: {e}")

    def load_stylesheet(self, path):
        base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
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
        base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, path)
        try:
            my_pixmap = QPixmap(icon_path)
            my_icon = QIcon(my_pixmap)
            self.setWindowIcon(my_icon)
            logger.info("Icon loaded successfully")
        except Exception as e:
            logger.error(f"Failed to set icon: {e}")

    def update_content(self, page_id):
        if self.current_page:
            self.current_page.hide()

        self.current_page = self.pages[page_id]
        if not self.current_page.isVisible():
            self.content_layout.addWidget(self.current_page)
        self.current_page.show()

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