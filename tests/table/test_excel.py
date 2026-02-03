import os
import tempfile
import time

from pyproforma.table import Cell, Table, to_excel, Format
from pyproforma.table.excel import value_format_to_excel_format


class TestValueFormatToExcelFormat:
    """Test cases for the value_format_to_excel_format function."""

    def test_none_format(self):
        """Test that None value_format returns General."""
        assert value_format_to_excel_format(None) == "General"

    def test_no_decimals_format(self):
        """Test no_decimals format returns correct Excel format."""
        assert value_format_to_excel_format(Format.NO_DECIMALS) == "#,##0"

    def test_two_decimals_format(self):
        """Test two_decimals format returns correct Excel format."""
        assert value_format_to_excel_format(Format.TWO_DECIMALS) == "#,##0.00"

    def test_percent_format(self):
        """Test percent format returns correct Excel format."""
        assert value_format_to_excel_format(Format.PERCENT) == "0%"

    def test_percent_one_decimal_format(self):
        """Test percent_one_decimal format returns correct Excel format."""
        assert value_format_to_excel_format(Format.PERCENT_ONE_DECIMAL) == "0.0%"

    def test_percent_two_decimals_format(self):
        """Test percent_two_decimals format returns correct Excel format."""
        assert value_format_to_excel_format(Format.PERCENT_TWO_DECIMALS) == "0.00%"

    def test_currency_format(self):
        """Test currency format returns correct Excel format."""
        assert value_format_to_excel_format(Format.CURRENCY) == "$#,##0.00"

    def test_unknown_format(self):
        """Test unknown format type returns reasonable default."""
        # String should return General
        assert value_format_to_excel_format("unknown_format") == "General"
        
        # Invalid dict is converted to default NumberFormatSpec which returns #,##0
        assert value_format_to_excel_format({"invalid": "dict"}) == "#,##0"

    def test_all_known_formats(self):
        """Test all known Format constants are correctly mapped."""
        format_mappings = {
            None: "General",
            Format.NO_DECIMALS: "#,##0",
            Format.TWO_DECIMALS: "#,##0.00",
            Format.PERCENT: "0%",
            Format.PERCENT_ONE_DECIMAL: "0.0%",
            Format.PERCENT_TWO_DECIMALS: "0.00%",
            Format.CURRENCY: "$#,##0.00",
            Format.CURRENCY_NO_DECIMALS: "$#,##0",
        }

        for value_format, expected_excel_format in format_mappings.items():
            result = value_format_to_excel_format(value_format)
            assert result == expected_excel_format, (
                f"Expected {expected_excel_format} for {value_format}, got {result}"
            )
        assert value_format_to_excel_format(" no_decimals") == "General"
        assert value_format_to_excel_format("no_decimals ") == "General"
        assert value_format_to_excel_format(" str ") == "General"

    def test_edge_cases(self):
        """Test edge cases and special values."""
        # Empty string
        assert value_format_to_excel_format("") == "General"

        # Very long string
        long_format = "a" * 1000
        assert value_format_to_excel_format(long_format) == "General"

        # Special characters
        assert value_format_to_excel_format("no-decimals") == "General"
        assert value_format_to_excel_format("no_decimals!") == "General"

    def test_return_type(self):
        """Test that the function always returns a string."""
        result = value_format_to_excel_format(None)
        assert isinstance(result, str)

        result = value_format_to_excel_format(Format.NO_DECIMALS)
        assert isinstance(result, str)

        result = value_format_to_excel_format({"invalid": "dict"})
        assert isinstance(result, str)


class TestToExcelIntegration:
    """Integration tests for to_excel function with value_format_to_excel_format."""

    def test_to_excel_with_different_formats(self):
        """Test that to_excel properly applies different value formats."""
        cells = [
            [
                Cell(value="Item", bold=True),
                Cell(value="Amount", bold=True),
                Cell(value="Percentage", bold=True),
                Cell(value="Text", bold=True),
            ],
            [
                Cell(value="Revenue", value_format="str"),
                Cell(value=1234567.89, value_format=Format.NO_DECIMALS),
                Cell(value=0.1234, value_format=Format.PERCENT_TWO_DECIMALS),
                Cell(value="Sample text", value_format="str"),
            ],
            [
                Cell(value="Expense", value_format="str"),
                Cell(value=987654.32, value_format=Format.TWO_DECIMALS),
                Cell(value=0.0567, value_format=Format.PERCENT_ONE_DECIMAL),
                Cell(value="Another text", value_format=None),  # Test None format
            ],
        ]

        table = Table(cells=cells)

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_name = tmp_file.name

        try:
            # This should not raise any exceptions
            to_excel(table, tmp_name)

            # Verify file was created
            assert os.path.exists(tmp_name)
            assert os.path.getsize(tmp_name) > 0

        finally:
            # Clean up
            if os.path.exists(tmp_name):
                # On Windows, need to wait briefly for file handle to be released
                time.sleep(0.1)
                os.unlink(tmp_name)

    def test_to_excel_with_all_format_types(self):
        """Test to_excel with all supported value format types."""
        # Create a table with one column for each format type
        cells = [
            [
                Cell(value="None Format", bold=True),
                Cell(value="No Decimals", bold=True),
                Cell(value="Two Decimals", bold=True),
                Cell(value="Percent", bold=True),
                Cell(value="Percent One Decimal", bold=True),
                Cell(value="Percent Two Decimals", bold=True),
                Cell(value="String", bold=True),
                Cell(value="Unknown Format", bold=True),
            ],
            [
                Cell(value=12345.67, value_format=None),
                Cell(value=12345.67, value_format=Format.NO_DECIMALS),
                Cell(value=12345.67, value_format=Format.TWO_DECIMALS),
                Cell(value=0.1234, value_format=Format.PERCENT),
                Cell(value=0.1234, value_format=Format.PERCENT_ONE_DECIMAL),
                Cell(value=0.1234, value_format=Format.PERCENT_TWO_DECIMALS),
                Cell(value=12345.67, value_format="str"),
                Cell(value=12345.67, value_format="unknown_format"),
            ]
        ]

        table = Table(cells=cells)

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_name = tmp_file.name

        try:
            # This should not raise any exceptions
            to_excel(table, tmp_name)

            # Verify file was created
            assert os.path.exists(tmp_name)
            assert os.path.getsize(tmp_name) > 0

        finally:
            # Clean up
            if os.path.exists(tmp_name):
                # On Windows, need to wait briefly for file handle to be released
                time.sleep(0.1)
                os.unlink(tmp_name)

    def test_to_excel_empty_table(self):
        """Test to_excel with an empty table."""
        cells = []
        table = Table(cells=cells)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            tmp_name = tmp_file.name

        try:
            to_excel(table, tmp_name)
            assert os.path.exists(tmp_name)
            assert os.path.getsize(tmp_name) > 0
        finally:
            if os.path.exists(tmp_name):
                # On Windows, need to wait briefly for file handle to be released
                time.sleep(0.1)
                os.unlink(tmp_name)
