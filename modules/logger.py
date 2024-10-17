import logging
import os
from datetime import datetime

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(module_name: str) -> logging.Logger:
    date_str = datetime.now().strftime("%Y-%m-%d")

    log_filename = os.path.join(LOG_DIR, f"{date_str}_{module_name}.log")
    error_log_filename = os.path.join(LOG_DIR, f"{date_str}_error.log")
    
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        error_file_handler = logging.FileHandler(error_log_filename, encoding="utf-8")
        error_file_handler.setLevel(logging.ERROR)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler.setFormatter(formatter)
        error_file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(error_file_handler)
        logger.addHandler(console_handler)

    return logger
