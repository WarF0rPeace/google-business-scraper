from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QIcon, QPixmap, qAlpha, QColor
from PySide6.QtCore import Qt, QSize
import os

class Sidebar(QFrame):
    def __init__(self, main_window, menu_items):
        super().__init__(main_window)
        self.main_window = main_window
        self.setFixedWidth(200)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)

        self.current_active_button = None

        for text, icon_path in menu_items:
            button = self.create_button(text, icon_path)
            self.layout.addWidget(button)

        self.layout.addStretch()

        self.load_stylesheet()

    def load_stylesheet(self):
        stylesheet_path = os.path.join(os.path.dirname(__file__), '../styles/sidebar.qss')
        with open(stylesheet_path, 'r', encoding="utf-8") as file:
            self.setStyleSheet(file.read())

    def create_button(self, text, icon_path):
        button = QPushButton(text)
        button.setObjectName(text)
        button.setIcon(self.load_icon(icon_path))
        button.setIconSize(QSize(48, 48))
        button.clicked.connect(self.on_button_click)

        self.add_shadow_effect(button)

        return button

    def load_icon(self, icon_path):
        icon = QIcon(icon_path)
        pixmap = icon.pixmap(QSize(24, 24))
        return QIcon(self.colorize_icon(pixmap))

    def colorize_icon(self, pixmap):
        image = pixmap.toImage()
        for x in range(image.width()):
            for y in range(image.height()):
                pixel_color = image.pixel(x, y)
                alpha = qAlpha(pixel_color)
                if alpha > 0:
                    image.setPixel(x, y, QColor(87, 149, 201, alpha).rgba())
        return QPixmap.fromImage(image)
    

    def add_shadow_effect(self, button):
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(100)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(20, 20)
        button.setGraphicsEffect(shadow)

    def set_active_button(self, button):
        if self.current_active_button:
            self.current_active_button.setProperty("active", False)
            self.current_active_button.style().unpolish(self.current_active_button)
            self.current_active_button.style().polish(self.current_active_button)
        
        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)
        
        self.current_active_button = button

    def on_button_click(self):
        sender = self.sender()
        page_id = self.get_page_id(sender.text())

        if page_id:
            self.main_window.update_content(page_id)
            self.set_active_button(sender)

    def get_page_id(self, button_text):
        for key, value in self.main_window.page_manager.get_menu_items().items():
            if value["name"] == button_text:
                return key
        return None
