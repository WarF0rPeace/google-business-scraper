import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.filters import AutoFilter
from modules.exporter import Exporter
from modules.logger import get_logger

logger = get_logger(__name__)

class ExcelExporter(Exporter):
    def export(self, data, file_path):
        try:
            if data:
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                headers = data[0].keys()
                sheet.append(list(headers))
                
                header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
                header_font = Font(bold=True)

                for col_num, header in enumerate(headers, 1):
                    cell = sheet.cell(row=1, column=col_num)
                    cell.fill = header_fill
                    cell.font = header_font

                for row in data:
                    sheet.append(list(row.values()))
                
                for col_num, header in enumerate(headers, 1):
                    column_letter = openpyxl.utils.get_column_letter(col_num)
                    max_length = len(header)
                    for row in data:
                        cell_value = row[header]
                        if isinstance(cell_value, (int, float)):
                            cell_value = str(cell_value)
                        if len(cell_value) > max_length:
                            max_length = len(cell_value)

                    sheet.column_dimensions[column_letter].width = max_length + 2

                sheet.auto_filter.ref = sheet.dimensions

                workbook.save(file_path)
                logger.info(f"Data successfully exported to Excel at {file_path}.")
            else:
                logger.warning("No data provided for export. Excel file was not created.")
        except Exception as e:
            logger.error(f"Failed to export data to Excel at {file_path}: {e}", exc_info=True)
