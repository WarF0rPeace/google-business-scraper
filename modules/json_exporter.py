import json
from modules.exporter import Exporter
from modules.logger import get_logger

logger = get_logger(__name__)

class JsonExporter(Exporter):
    def export(self, data, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            
            logger.info(f"Data successfully exported to JSON at {file_path}.")
        except Exception as e:
            logger.error(f"Failed to export data to JSON at {file_path}: {e}", exc_info=True)
