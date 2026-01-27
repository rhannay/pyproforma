import os
import tempfile
import time

from pyproforma.tables.excel import to_excel, value_format_to_excel_format
from pyproforma.tables.table_class import Cell, Column, Row, Table


class TestValueFormatToExcelFormat:
    """Test cases for the value_format_to_excel_format function."""

    def test_none_format(self):
        """Test that None value_format returns General."""
        assert value_format_to_excel_format(None) == "General"

    def test_no_decimals_format(self):
        """Test no_decimals format returns correct Excel format."""
        assert value_format_to_excel_format("no_decimals") == "#,##0"

    def test_two_decimals_format(self):
        """Test two_decimals format returns correct Excel format."""
        assert value_format_to_excel_format("two_decimals") == "#,##0.00"

    def test_percent_format(self):
        """Test percent format returns correct Excel format."""
        assert value_format_to_excel_format("percent") == "0%"

    def test_percent_one_decimal_format(self):
        """Test percent_one_decimal format returns correct Excel format."""
        assert value_format_to_excel_format("percent_one_decimal") == "0.0%"

    def test_percent_two_decimals_format(self):
        """Test percent_two_decimals format returns correct Excel format."""
        assert value_format_to_excel_format("percent_two_decimals") == "0.00%"

    def test_typo_in_format_name(self):
        """Test that the typo 'percent_two_decinals' is handled correctly."""
        # The original test file has a typo: 'percent_two_decinals' instead of 'percent_two_decimals'  # noqa: E501
        # Our function should handle this typo and return the same format as the correct spelling  # noqa: E501
        assert value_format_to_excel_format("percent_two_decinals") == "0.00%"

    def test_str_format(self):
        """Test str format returns correct Excel format."""
        assert value_format_to_excel_format("str") == "@"

    def test_unknown_format(self):
        """Test unknown format returns General as fallback."""
        assert value_format_to_excel_format("unknown_format") == "General"
        assert value_format_to_excel_format("invalid") == "General"
        assert value_format_to_excel_format("") == "General"

    def test_all_known_formats(self):
        """Test all known formats are correctly mapped."""
        format_mappings = {
            None: "General",
            "no_decimals": "#,##0",
            "two_decimals": "#,##0.00",
            "percent": "0%",
            "percent_one_decimal": "0.0%",
            "percent_two_decimals": "0.00%",
            "percent_two_decinals": "0.00%",  # Handle typo in codebase
            "str": "@",
        }

        for value_format, expected_excel_format in format_mappings.items():
            result = value_format_to_excel_format(value_format)
            assert result == expected_excel_format, (
                f"Expected {expected_excel_format} for {value_format}, got {result}"
            )

    def test_case_sensitivity(self):
        """Test that the function is case sensitive."""
        # These should return General since they don't match exactly
        assert value_format_to_excel_format("NO_DECIMALS") == "General"
        assert value_format_to_excel_format("Two_Decimals") == "General"
        assert value_format_to_excel_format("PERCENT") == "General"
        assert value_format_to_excel_format("STR") == "General"

    def test_whitespace_handling(self):
        """Test that whitespace in format strings returns General."""
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

        result = value_format_to_excel_format("no_decimals")
        assert isinstance(result, str)

        result = value_format_to_excel_format("unknown")
        assert isinstance(result, str)


class TestToExcelIntegration:
    """Integration tests for to_excel function with value_format_to_excel_format."""

    def test_to_excel_with_different_formats(self):
        """Test that to_excel properly applies different value formats."""
        columns = [
            Column(label="Item"),
            Column(label="Amount"),
            Column(label="Percentage"),
            Column(label="Text"),
        ]

        rows = [
            Row(
                cells=[
                    Cell(value="Revenue", value_format="str"),
                    Cell(value=1234567.89, value_format="no_decimals"),
                    Cell(value=0.1234, value_format="percent_two_decimals"),
                    Cell(value="Sample text", value_format="str"),
                ]
            ),
            Row(
                cells=[
                    Cell(value="Expense", value_format="str"),
                    Cell(value=987654.32, value_format="two_decimals"),
                    Cell(value=0.0567, value_format="percent_one_decimal"),
                    Cell(value="Another text", value_format=None),  # Test None format
                ]
            ),
        ]

        table = Table(columns=columns, rows=rows)

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
        columns = [
            Column(label="None Format"),
            Column(label="No Decimals"),
            Column(label="Two Decimals"),
            Column(label="Percent"),
            Column(label="Percent One Decimal"),
            Column(label="Percent Two Decimals"),
            Column(label="String"),
            Column(label="Unknown Format"),
        ]

        rows = [
            Row(
                cells=[
                    Cell(value=12345.67, value_format=None),
                    Cell(value=12345.67, value_format="no_decimals"),
                    Cell(value=12345.67, value_format="two_decimals"),
                    Cell(value=0.1234, value_format="percent"),
                    Cell(value=0.1234, value_format="percent_one_decimal"),
                    Cell(value=0.1234, value_format="percent_two_decimals"),
                    Cell(value=12345.67, value_format="str"),
                    Cell(value=12345.67, value_format="unknown_format"),
                ]
            )
        ]

        table = Table(columns=columns, rows=rows)

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
        columns = [Column(label="Test")]
        rows = []
        table = Table(columns=columns, rows=rows)

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
