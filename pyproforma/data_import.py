import openpyxl
from pyproforma import LineItem, Model

def _excel_to_list(filename, sheet_name: str = None) -> list[dict]:
    wb = openpyxl.load_workbook(filename, data_only=True)
    if sheet_name:
        ws = wb[sheet_name]
    else:
        ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = rows[0]
    # Only keep columns up to the last non-None header
    if any(headers):
        last_idx = max(i for i, h in enumerate(headers) if h is not None) + 1
        headers = headers[:last_idx]
    data = []
    for row in rows[1:]:
        if not row or row[0] is None or str(row[0]).strip() == "":
            continue  # Skip rows where column A is blank
        item = dict(zip(headers, row[:len(headers)]))
        data.append(item)
    return data

def load_line_items_excel(filename: str, sheet_name: str = None) -> list[LineItem]:

    data = _excel_to_list(filename, sheet_name)
    if not data:
        raise ValueError("No data found in the Excel file.")
    line_items = []
    for row in data:
        line_items.append(LineItem.from_dict(row))

    return line_items