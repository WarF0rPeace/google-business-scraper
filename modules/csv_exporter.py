import csv
from modules.exporter import Exporter
from modules.logger import get_logger

logger = get_logger(__name__)

class CsvExporter(Exporter):
    def export(self, data, file_path):
        try:
            if data:
                headers = data[0].keys()
                with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(data)
                
                logger.info(f"Data successfully exported to CSV at {file_path}.")
            else:
                logger.warning("No data provided for export. CSV file was not created.")
        except Exception as e:
            logger.error(f"Failed to export data to CSV at {file_path}: {e}", exc_info=True)
