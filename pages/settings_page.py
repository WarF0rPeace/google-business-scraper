import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog,
    QPushButton, QListWidget, QLineEdit, QCheckBox, QMessageBox,
    QAbstractItemView, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from utils.constants import CHECKBOX_OPTIONS
from modules.logger import get_logger

logger = get_logger(__name__)

class SettingsPage(QWidget):
    options_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.load_stylesheet("styles/scraper_styles.qss")
        self.checkboxes = {key: QCheckBox(value["description"]) for key, value in CHECKBOX_OPTIONS.items()}

        self.setup_options_layout()
        self.setup_query_input_and_list()
        self.setup_buttons()
    
    def setup_options_layout(self):
        option_layout = QHBoxLayout()
        for index, (key, checkbox) in enumerate(self.checkboxes.items()):
            option_layout.addWidget(checkbox)
            checkbox.stateChanged.connect(self.emit_options_updated)
            if (index + 1) % 4 == 0:
                self.layout.addLayout(option_layout)
                option_layout = QHBoxLayout()
        if option_layout.count():
            self.layout.addLayout(option_layout)

    def setup_query_input_and_list(self):
        left_layout = QVBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Yeni sorgu giriniz...")
        self.query_input.setFixedWidth(300)
        left_layout.addWidget(self.query_input)

        self.query_list_widget = QListWidget()
        self.query_list_widget.setFixedWidth(300)
        self.query_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.query_list_widget.itemDoubleClicked.connect(self.edit_query)
        left_layout.addWidget(self.query_list_widget)

        self.layout.addLayout(left_layout)

    def setup_buttons(self):
        logger.debug("Creating action buttons.")
        buttons = [
            ("Sorgu Ekle", self.add_query),
            ("Seçilenleri Sil", self.remove_selected_queries),
            ("Tümünü Sil", self.remove_all_queries),
            ("Dosyadan Yükle", self.load_queries_from_file),
        ]
        for text, callback in buttons:
            self.create_button(text, callback)
        
    def create_button(self, text, callback):
        logger.debug(f"Creating button: {text}.")
        button = QPushButton(text)
        button.setFixedWidth(300)
        button.clicked.connect(callback)
        self.layout.addWidget(button)

    def load_stylesheet(self, path):
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, path)

        try:
            with open(full_path, "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
                logger.debug(f"Stylesheet applied from {full_path}")
        except FileNotFoundError:
            logger.error(f"Stylesheet file not found at {full_path}")
        except Exception as e:
            logger.exception(f"Unexpected error while loading stylesheet: {e}")


    def add_query(self):
        query_text = self.query_input.text().strip()
        if query_text:
            self.query_list_widget.addItem(query_text)
            self.query_input.clear()
            logger.info(f"Query added: {query_text}.")
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir sorgu girin.")
    
    def remove_selected_queries(self):
        for item in self.query_list_widget.selectedItems():
            self.query_list_widget.takeItem(self.query_list_widget.row(item))
        logger.info("Selected queries removed.")
    
    def edit_query(self, item):
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.query_list_widget.editItem(item)

    def remove_all_queries(self):
        self.query_list_widget.clear()
        logger.info("All queries removed.")
    
    def load_queries_from_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Dosya Seç", "", "Text Dosyaları (*.txt);;Tüm Dosyalar (*)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    queries = [line.strip() for line in file if line.strip()]
                self.query_list_widget.clear()
                for query in queries:
                    self.query_list_widget.addItem(QListWidgetItem(query))
                logger.info(f"Queries loaded from file: {file_name}.")
            except Exception as e:
                QMessageBox.warning(self, "Uyarı", f"Dosya yüklenirken bir hata oluştu: {str(e)}")
                logger.error(f"Error loading queries from file: {e}")
    
    def emit_options_updated(self):
        options = {key: checkbox.isChecked() for key, checkbox in self.checkboxes.items()}
        self.options_updated.emit(options)
        logger.debug(f"Options updated: {options}")

    def get_queries(self):
        return [self.query_list_widget.item(i).text() for i in range(self.query_list_widget.count())]

    def get_selected_options(self):
        return {key: checkbox.isChecked() for key, checkbox in self.checkboxes.items()}
