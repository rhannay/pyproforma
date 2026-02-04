"""
Demonstration of the table.show() method

This example demonstrates the new show() method for the Table class,
which provides a convenient way to display tables in Jupyter notebooks.
"""

from pyproforma.table import Table, Cell

# Create a sample table
table = Table(
    cells=[
        [
            Cell("Product", bold=True),
            Cell("Q1", bold=True),
            Cell("Q2", bold=True),
            Cell("Q3", bold=True),
            Cell("Q4", bold=True),
        ],
        [Cell("Revenue"), Cell(1000), Cell(1200), Cell(1400), Cell(1600)],
        [Cell("Expenses"), Cell(800), Cell(900), Cell(1000), Cell(1100)],
        [
            Cell("Profit", bold=True),
            Cell(200, bold=True),
            Cell(300, bold=True),
            Cell(400, bold=True),
            Cell(500, bold=True),
        ],
    ]
)

# Style the header row
table.style_row(0, align="center", background_color="lightblue")

# Style the total row
table.style_row(3, bottom_border="double", background_color="lightgray")

print("Table created successfully!")
print(f"Table dimensions: {table.row_count} rows x {table.col_count} columns")
print()

# In a Jupyter notebook, you would simply use:
#   table.show()
# This will automatically display the table with nice formatting.

# For this script, we'll demonstrate the HTML output instead
print("HTML output (first 500 chars):")
print(table.to_html()[:500])
print("...")
print()
print(
    "To use table.show() in a notebook, ensure IPython is installed:\n"
    "  pip install ipython\n"
    "or install the notebook optional dependency:\n"
    "  pip install pyproforma[notebook]"
)
