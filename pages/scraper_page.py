from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem,
    QAbstractItemView, QMessageBox, QLineEdit,
    QComboBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from modules.scraper import ScraperWorker
from modules.json_exporter import JsonExporter
from modules.csv_exporter import CsvExporter
from modules.xlsx_exporter import ExcelExporter
from modules.logger import get_logger

logger = get_logger(__name__)

class ScraperPage(QWidget):
    def __init__(self):
        super().__init__()
        self.data_keys = {
            "İşletme": "title",
            "Telefon numarası": "phone_number",
            "Website": "url",
            "Puan": "rating_score",
            "Yorum Sayısı": "review_count",
            "Addres": "address",
            "Kategori": "category",
            # "Feature ID": "feature_id",
        }
        
        logger.info("Initializing ScraperPage UI components.")
        self.init_ui()
        self.timer = QTimer()
        self.elapsed_time = 0
        self.timer.timeout.connect(self.update_time)

    def init_ui(self):
        logger.info("Setting up UI layouts.")
        self.setup_layouts()
        self.setup_query_list()
        self.setup_buttons()
        self.setup_results_table()
        self.setup_timer_label()
        self.setup_total_data_label()

    def setup_layouts(self):
        logger.debug("Creating main layout and child layouts.")
        self.main_layout = QHBoxLayout(self)
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addItem(spacer)
        self.main_layout.addLayout(self.right_layout)

    def setup_query_list(self):
        logger.debug("Setting up query list widget.")
        self.query_list_widget = QListWidget()
        self.query_list_widget.setFixedWidth(300)
        self.query_list_widget.setEditTriggers(QListWidget.EditTrigger.DoubleClicked)
        self.query_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.left_layout.addWidget(self.query_list_widget)

        self.query_input = QLineEdit()
        self.query_input.setFixedWidth(300)
        self.query_input.setPlaceholderText("Yeni sorgu giriniz...")
        self.left_layout.addWidget(self.query_input)

    def setup_buttons(self):
        logger.debug("Creating action buttons.")
        buttons = [
            ("Sorgu Ekle", self.add_query),
            ("Seçilenleri Sil", self.delete_selected_queries),
            ("Hepsini Sil", self.delete_all_queries),
            ("Dosyadan Yükle", self.browse_file),
            ("Başlat", self.start_scraping),
        ]
        for text, callback in buttons:
            self.create_button(text, callback)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "XLSX"])
        self.left_layout.addWidget(self.export_format_combo)

        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_data)
        self.left_layout.addWidget(export_button)

    def create_button(self, text, callback):
        logger.debug(f"Creating button: {text}.")
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.left_layout.addWidget(button)

    def setup_results_table(self):
        logger.debug("Setting up results table.")
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(len(self.data_keys))
        self.results_table.setHorizontalHeaderLabels(list(self.data_keys.keys()))
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.right_layout.addWidget(self.results_table)

    def setup_timer_label(self):
        logger.debug("Adding timer label.")
        self.time_label = QLabel("Geçen Süre: 00:00:00")
        self.right_layout.addWidget(self.time_label)
    
    def setup_total_data_label(self):
        logger.debug("Adding total data label.")
        self.total_data_label = QLabel("Toplam Veri: 0")
        self.right_layout.addWidget(self.total_data_label)

    def load_stylesheet(self, filename):
        logger.info(f"Loading stylesheet from {filename}.")
        with open(filename, "r") as file:
            self.setStyleSheet(file.read())

    def browse_file(self):
        logger.info("Opening file dialog to load queries.")
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            logger.info(f"File selected: {file_name}")
            self.load_queries_from_file(file_name)
        else:
            logger.warning("No file selected.")

    def load_queries_from_file(self, file_name):
        logger.info(f"Loading queries from file: {file_name}.")
        with open(file_name, 'r', encoding='utf-8') as file:
            queries = [line.strip() for line in file.readlines()]

        self.query_list_widget.clear()
        for query in queries:
            item = QListWidgetItem(query)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.query_list_widget.addItem(item)

    def start_scraping(self):
        queries = [self.query_list_widget.item(i).text() for i in range(self.query_list_widget.count())]
        if queries:
            logger.info("Starting scraping process.")
            self.worker = ScraperWorker(queries)
            self.worker.update_data.connect(self.add_row_to_table)
            self.worker.finished.connect(self.finish_scraping)
            self.timer.start(1000)
            self.elapsed_time = 0
            self.worker.start()
        else:
            logger.warning("No queries to scrape.")
            QMessageBox.warning(self, "Warning", "En az 1 adet sorgu girmeniz gerek.")

    def finish_scraping(self):
        logger.info("Scraping process finished.")
        self.timer.stop()
        self.update_time()
        self.update_total_count()

    def update_time(self):
        self.elapsed_time += 1
        hours, remainder = divmod(self.elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"Geçen Süre: {hours:02}:{minutes:02}:{seconds:02}")
    
    def update_total_count(self):
        total_rows = self.results_table.rowCount()
        self.total_data_label.setText(f"Toplam Veri: {total_rows}")

    def add_row_to_table(self, place):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        logger.debug(f"Adding new row to table at position {row_position}.")

        for col, header in enumerate(self.data_keys.keys()):
            key = self.data_keys[header]
            value = place.get(key, "")
            if value is None:
                value = ""
            self.results_table.setItem(row_position, col, QTableWidgetItem(str(value)))
        
        self.update_total_count()

    def delete_selected_queries(self):
        logger.info("Deleting selected queries.")
        for item in self.query_list_widget.selectedItems():
            self.query_list_widget.takeItem(self.query_list_widget.row(item))

    def delete_all_queries(self):
        logger.info("Deleting all queries.")
        self.query_list_widget.clear()

    def add_query(self):
        query_text = self.query_input.text().strip()
        if query_text:
            logger.info(f"Adding new query: {query_text}.")
            self.query_list_widget.addItem(query_text)
            self.query_input.clear()
        else:
            logger.warning("Attempted to add an empty query.")
            QMessageBox.warning(self, "Warning", "Lütfen bir sorgu girin.")

    def export_data(self):
        selected_format = self.export_format_combo.currentText()
        logger.info(f"Exporting data in {selected_format} format.")
        file_dialog = QFileDialog.getSaveFileName(self, "Select Save Location", "", f"{selected_format} Files (*.{selected_format.lower()});;All Files (*)")
        file_path = file_dialog[0]

        if file_path:
            logger.info(f"File path selected for export: {file_path}.")
            data = []
            for row in range(self.results_table.rowCount()):
                row_data = {}
                for col, header in enumerate(self.data_keys.keys()):
                    key = self.data_keys[header]
                    cell_item = self.results_table.item(row, col)
                    row_data[key] = cell_item.text() if cell_item else ""
                
                row_data['rating_score'] = float(row_data['rating_score']) if row_data['rating_score'] else 0
                row_data['review_count'] = int(row_data['review_count'])
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
            QMessageBox.warning(self, "Warning", "Dosya seçilmedi.")
