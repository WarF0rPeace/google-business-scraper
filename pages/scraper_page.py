import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog,
    QTableWidget, QHeaderView, QMessageBox,
    QComboBox, QTableWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from modules.scraper import ScraperWorker
from modules.json_exporter import JsonExporter
from modules.csv_exporter import CsvExporter
from modules.xlsx_exporter import ExcelExporter
from utils.constants import CHECKBOX_OPTIONS
from modules.logger import get_logger

logger = get_logger(__name__)

class ScraperPage(QWidget):
    def __init__(self, settings_page):
        super().__init__()
        self.load_stylesheet("styles/scraper_styles.qss")
        self.settings_page = settings_page
        self.data_keys = {}
        self.settings_page.options_updated.connect(self.update_headers)

        logger.info("Initializing ScraperPage UI components.")
        self.init_ui()
        self.timer = QTimer()
        self.elapsed_time = 0
        self.timer.timeout.connect(self.update_time)

    def init_ui(self):
        logger.info("Setting up UI layouts.")
        self.setup_layouts()
        self.setup_buttons()
        self.setup_results_table()
        self.setup_timer_label()
        self.setup_total_data_label()
        self.setup_export_section()
    
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

    def setup_layouts(self):
        self.main_layout = QVBoxLayout(self)
        self.top_layout = QHBoxLayout()
        self.main_layout.addLayout(self.top_layout)
        self.table_layout = QVBoxLayout()
        self.main_layout.addLayout(self.table_layout)

    def setup_buttons(self):
        buttons = [
            ("Başlat", self.start_scraping),
            ("Durdur", self.stop_scraping),
        ]
        for text, callback in buttons:
            self.create_button(text, callback)

    def create_button(self, text, callback):
        button = QPushButton(text)
        button.setObjectName(text)
        button.clicked.connect(callback)
        self.top_layout.addWidget(button)

    def setup_export_section(self):
        self.export_layout = QHBoxLayout()        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "XLSX"])
        export_button = QPushButton("Dışa Aktar")
        export_button.clicked.connect(self.export_data)
        self.export_layout.addWidget(self.export_format_combo)
        self.export_layout.addWidget(export_button)
        self.main_layout.addLayout(self.export_layout)
        self.export_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

    def setup_results_table(self):
        self.results_table = QTableWidget()
        self.update_results_table()
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_layout.addWidget(self.results_table)

    def setup_timer_label(self):
        self.time_label = QLabel("Geçen Süre: 00:00:00")
        self.table_layout.addWidget(self.time_label)

    def setup_total_data_label(self):
        self.total_data_label = QLabel("Toplam Veri: 0")
        self.table_layout.addWidget(self.total_data_label)

    def update_headers(self):
        self.data_keys.clear()
        for key, value in self.settings_page.checkboxes.items():
            if value.isChecked():
                self.data_keys[CHECKBOX_OPTIONS[key]['label']] = key
        self.update_results_table()

    def update_results_table(self):
        self.results_table.setColumnCount(len(self.data_keys))
        self.results_table.setHorizontalHeaderLabels(list(self.data_keys.keys()))

    def start_scraping(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            logger.warning("Scraping process is already running.")
            QMessageBox.warning(self, "Uyarı", "Scraping işlemi zaten çalışıyor.")
            return

        queries = self.settings_page.get_queries()
        if queries:
            self.update_headers()
            selected_options = self.settings_page.get_selected_options()

            logger.info("Starting scraping process.")
            self.results_table.setRowCount(0)

            start_button = self.findChild(QPushButton, "Başlat")
            if start_button:
                start_button.setEnabled(False)

            self.worker = ScraperWorker(queries=queries, options=selected_options, max_concurrent_requests=5)
            self.worker.update_data.connect(self.add_row_to_table)
            self.worker.finished.connect(self.finish_scraping)
            self.timer.start(1000)
            self.elapsed_time = 0
            self.worker.start()
        else:
            logger.warning("No queries to scrape.")
            QMessageBox.warning(self, "Uyarı", "En az 1 adet sorgu girmeniz gerek.")

    def stop_scraping(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.worker.terminate()
            logger.info("Scraping process stopped.")
        self.timer.stop()
        
        start_button = self.findChild(QPushButton, "Başlat")
        if start_button:
            start_button.setEnabled(True)

    def finish_scraping(self):
        logger.info("Scraping process finished.")
        self.timer.stop()
        self.update_time()
        self.update_total_count()
        
        start_button = self.findChild(QPushButton, "Başlat")
        if start_button:
            start_button.setEnabled(True)

    def update_time(self):
        self.elapsed_time += 1
        hours, remainder = divmod(self.elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"Geçen Süre: {hours:02}:{minutes:02}:{seconds:02}")

    def update_total_count(self):
        total_rows = self.results_table.rowCount()
        self.total_data_label.setText(f"Toplam Veri: {total_rows}")

    def add_row_to_table(self, place):
        logger.debug(f"Adding place data: {place}")
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)

        for col, header in enumerate(self.data_keys.keys()):
            key = self.data_keys[header]
            value = place.get(key, "") or ""

            if isinstance(value, list):
                value = ", ".join(map(str, value))
            elif isinstance(value, (int, float)):
                value = str(value)

            self.results_table.setItem(row_position, col, QTableWidgetItem(str(value)))

        self.update_total_count()

    def export_data(self):
        selected_format = self.export_format_combo.currentText()
        logger.info(f"Exporting data in {selected_format} format.")
        file_dialog = QFileDialog.getSaveFileName(self, "Kaydetme Yeri Seçin", "", f"{selected_format} Files (*.{selected_format.lower()});;All Files (*)")
        file_path = file_dialog[0]

        if file_path:
            logger.info(f"File path selected for export: {file_path}.")
            data = []
            selected_options = self.settings_page.get_selected_options()
            for row in range(self.results_table.rowCount()):
                row_data = {}
                for col, header in enumerate(self.data_keys.keys()):
                    key = self.data_keys[header]
                    if key in selected_options:
                        cell_item = self.results_table.item(row, col)
                        value = cell_item.text() if cell_item else ""

                        if key == 'rating_score':
                            row_data[key] = float(value) if value else 0.0
                        elif key == 'review_count':
                            row_data[key] = int(value) if value else 0
                        else:
                            row_data[key] = value
                
                data.append(row_data)

            if selected_format == "JSON":
                exporter = JsonExporter()
            elif selected_format == "CSV":
                exporter = CsvExporter()
            elif selected_format == "XLSX":
                exporter = ExcelExporter()
            
            exporter.export(data, file_path)
        else:
            logger.warning("No file path selected for export.")
            QMessageBox.warning(self, "Uyarı", "Dosya seçilmedi.")
