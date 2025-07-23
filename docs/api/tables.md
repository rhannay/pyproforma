# Tables API

The Tables API provides functionality for creating, formatting, and exporting tables based on model data.

## Table Class

The `Table` class is the main class for creating tables.

```python
from pyproforma.tables import Table
```

### Creating a Table

```python
table = Table("Income Statement")  # Create a table with a title
```

### Methods

#### add_row

Add a row to the table.

```python
table.add_row(label, source, format_spec=None)
```

**Parameters:**

- `label` (str): The label for the row
- `source` (str): The name of the line item to use as the source for this row
- `format_spec` (str, optional): Format specification (e.g., ",.2f" for comma as thousand separator and 2 decimal places)

**Example:**

```python
table.add_row("Revenue", "revenue", ",.0f")
table.add_row("Expenses", "expenses", ",.0f")
table.add_row("Profit", "profit", ",.0f")
```

#### add_header_row

Add a header row to the table.

```python
table.add_header_row(label)
```

**Parameters:**

- `label` (str): The label for the header row

**Example:**

```python
table.add_header_row("Income Statement")
```

#### add_separator

Add a separator row to the table.

```python
table.add_separator()
```

#### generate

Generate the table data from model results.

```python
table_data = table.generate(results)
```

**Parameters:**

- `results` (Results): The results object from a calculated model

**Returns:**

- `TableData`: An object containing the generated table

#### to_excel

Export the table to an Excel file.

```python
table.to_excel(filename, results, sheet_name=None, start_row=0, start_col=0)
```

**Parameters:**

- `filename` (str): The name of the Excel file to create
- `results` (Results): The results object from a calculated model
- `sheet_name` (str, optional): The name of the sheet to create
- `start_row` (int, optional): The starting row for the table
- `start_col` (int, optional): The starting column for the table

**Example:**

```python
table.to_excel("financial_statements.xlsx", results, sheet_name="Income Statement")
```

## RowType Class

The `RowType` class defines different types of rows that can be used in a table.

```python
from pyproforma.tables import RowType
```

### Available Row Types

- `RowType.DATA`: A regular data row
- `RowType.HEADER`: A header row
- `RowType.SEPARATOR`: A separator line
- `RowType.SUBTOTAL`: A subtotal row
- `RowType.TOTAL`: A total row

### Example

```python
from pyproforma.tables import Table, RowType

table = Table("Income Statement")

# Add different types of rows
table.add_row("Revenue", "revenue", row_type=RowType.DATA)
table.add_row("Expenses", "expenses", row_type=RowType.DATA)
table.add_row("Profit", "profit", row_type=RowType.TOTAL)
```

## Excel Class

The `Excel` class provides more advanced Excel export functionality.

```python
from pyproforma.tables import Excel
```

### Creating an Excel Workbook

```python
excel = Excel("financial_model.xlsx")
```

### Methods

#### add_table

Add a table to the workbook.

```python
excel.add_table(table, results, sheet_name=None, start_row=0, start_col=0)
```

**Parameters:**

- `table` (Table): The table to add
- `results` (Results): The results object from a calculated model
- `sheet_name` (str, optional): The name of the sheet
- `start_row` (int, optional): The starting row
- `start_col` (int, optional): The starting column

#### save

Save the workbook to a file.

```python
excel.save()
```

### Example

```python
from pyproforma.tables import Table, Excel

# Create tables
income_table = Table("Income Statement")
income_table.add_row("Revenue", "revenue")
income_table.add_row("Expenses", "expenses")
income_table.add_row("Profit", "profit")

balance_table = Table("Balance Sheet")
balance_table.add_row("Assets", "assets")
balance_table.add_row("Liabilities", "liabilities")
balance_table.add_row("Equity", "equity")

# Create Excel workbook and add tables
excel = Excel("financial_statements.xlsx")
excel.add_table(income_table, results, sheet_name="Income Statement")
excel.add_table(balance_table, results, sheet_name="Balance Sheet")
excel.save()
```
