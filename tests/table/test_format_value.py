"""Tests for the format_value function."""

import pytest

from pyproforma.table import format_value


class TestFormatValue:
    """Test cases for the format_value function."""

    def test_format_value_none(self):
        """Test that None value_format returns the original value."""
        assert format_value(123.45, None) == 123.45
        assert format_value("test", None) == "test"
        assert format_value(0, None) == 0

    def test_format_value_str(self):
        """Test string formatting."""
        assert format_value(123.45, "str") == "123.45"
        assert format_value(0, "str") == "0"
        assert format_value(-42, "str") == "-42"

    def test_format_value_no_decimals(self):
        """Test no_decimals formatting - should round and add commas."""
        assert format_value(123.45, "no_decimals") == "123"
        assert format_value(123.6, "no_decimals") == "124"  # rounds up
        assert format_value(123.5, "no_decimals") == "124"
        assert (
            format_value(1234567.89, "no_decimals") == "1,234,568"
        )  # rounds and adds commas
        assert format_value(0, "no_decimals") == "0"
        assert format_value(-123.45, "no_decimals") == "-123"

    def test_format_value_two_decimals(self):
        """Test two_decimals formatting."""
        assert format_value(123.456, "two_decimals") == "123.46"
        assert format_value(123, "two_decimals") == "123.00"
        assert format_value(0, "two_decimals") == "0.00"
        assert format_value(-123.456, "two_decimals") == "-123.46"
        assert (
            format_value(1234.56, "two_decimals") == "1,234.56"
        )  # Test with commas for larger numbers

    def test_format_value_percent(self):
        """Test percent formatting - should round to nearest whole percent."""
        assert format_value(0.1234, "percent") == "12%"
        assert format_value(0.1256, "percent") == "13%"  # rounds up
        assert format_value(0.5, "percent") == "50%"
        assert format_value(1.0, "percent") == "100%"
        assert format_value(0, "percent") == "0%"
        assert format_value(-0.1234, "percent") == "-12%"

    def test_format_value_percent_one_decimal(self):
        """Test percent_one_decimal formatting."""
        assert format_value(0.1234, "percent_one_decimal") == "12.3%"
        assert format_value(0.1256, "percent_one_decimal") == "12.6%"
        assert format_value(0.1255, "percent_one_decimal") == "12.6%"
        assert format_value(0.5, "percent_one_decimal") == "50.0%"
        assert format_value(0, "percent_one_decimal") == "0.0%"

    def test_format_value_percent_two_decimals(self):
        """Test percent_two_decimals formatting (note the typo in the original)."""
        assert format_value(0.1234, "percent_two_decimals") == "12.34%"
        assert format_value(0.1256, "percent_two_decimals") == "12.56%"
        assert format_value(0.5, "percent_two_decimals") == "50.00%"
        assert format_value(0, "percent_two_decimals") == "0.00%"

    def test_format_value_invalid_format(self):
        """Test that invalid value_format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid value_format: invalid_format"):
            format_value(123, "invalid_format")

    def test_format_value_edge_cases(self):
        """Test edge cases and boundary values."""
        # Test very large numbers
        assert format_value(1000000, "no_decimals") == "1,000,000"

        # Test very small percentages
        assert format_value(0.001, "percent") == "0%"  # rounds to 0
        assert format_value(0.005, "percent") == "0%"  # rounds to 0 (banker's rounding)
        assert format_value(0.006, "percent") == "1%"  # rounds to 1

        # Test negative values
        assert format_value(-1234.56, "no_decimals") == "-1,235"
        assert format_value(-0.1234, "percent") == "-12%"
