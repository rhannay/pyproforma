"""Tests for the format_value function."""

import pytest

from pyproforma.table import Format, NumberFormatSpec, format_value


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


class TestNumberFormatSpec:
    """Test cases for NumberFormatSpec class."""

    def test_basic_integer_format(self):
        """Test basic integer formatting with thousands separator."""
        spec = NumberFormatSpec(decimals=0, thousands=True)
        assert format_value(1234.56, spec) == "1,235"
        assert format_value(123, spec) == "123"
        assert format_value(1234567, spec) == "1,234,567"

    def test_decimal_format(self):
        """Test decimal formatting."""
        spec = NumberFormatSpec(decimals=2, thousands=True)
        assert format_value(1234.56, spec) == "1,234.56"
        assert format_value(123.456, spec) == "123.46"
        assert format_value(123, spec) == "123.00"

    def test_no_thousands_separator(self):
        """Test formatting without thousands separator."""
        spec = NumberFormatSpec(decimals=0, thousands=False)
        assert format_value(1234.56, spec) == "1235"

        spec = NumberFormatSpec(decimals=2, thousands=False)
        assert format_value(1234.56, spec) == "1234.56"

    def test_prefix_suffix(self):
        """Test prefix and suffix."""
        spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
        assert format_value(1234.56, spec) == "$1,234.56"

        spec = NumberFormatSpec(decimals=0, thousands=False, suffix="%")
        assert format_value(50, spec) == "50%"

        spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$", suffix=" USD")
        assert format_value(1234.56, spec) == "$1,234.56 USD"

    def test_multiplier(self):
        """Test value multiplier."""
        # Percentage format (multiply by 100)
        spec = NumberFormatSpec(decimals=0, thousands=False, suffix="%", multiplier=100)
        assert format_value(0.1234, spec) == "12%"
        assert format_value(0.5, spec) == "50%"

        spec = NumberFormatSpec(decimals=1, thousands=False, suffix="%", multiplier=100)
        assert format_value(0.1234, spec) == "12.3%"

    def test_display_scale_millions(self):
        """Test millions display scale."""
        spec = NumberFormatSpec(decimals=1, thousands=False, display_scale="M")
        assert format_value(3100000, spec) == "3.1M"
        assert format_value(1500000, spec) == "1.5M"
        assert format_value(1234567, spec) == "1.2M"

    def test_display_scale_thousands(self):
        """Test thousands display scale."""
        spec = NumberFormatSpec(decimals=1, thousands=False, display_scale="K")
        assert format_value(3100, spec) == "3.1K"
        assert format_value(1500, spec) == "1.5K"
        assert format_value(999, spec) == "1.0K"

    def test_display_scale_billions(self):
        """Test billions display scale."""
        spec = NumberFormatSpec(decimals=2, thousands=False, display_scale="B")
        assert format_value(3_100_000_000, spec) == "3.10B"
        assert format_value(1_500_000_000, spec) == "1.50B"

    def test_display_scale_case_insensitive(self):
        """Test that display scale is case insensitive."""
        spec_upper = NumberFormatSpec(decimals=1, thousands=False, display_scale="M")
        spec_lower = NumberFormatSpec(decimals=1, thousands=False, display_scale="m")
        assert format_value(3100000, spec_upper) == "3.1M"
        assert format_value(3100000, spec_lower) == "3.1m"

    def test_negative_values(self):
        """Test formatting negative values."""
        spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
        assert format_value(-1234.56, spec) == "$-1,234.56"

        spec = NumberFormatSpec(decimals=1, thousands=False, display_scale="M")
        assert format_value(-3100000, spec) == "-3.1M"

    def test_serialization(self):
        """Test to_dict and from_dict methods."""
        spec = NumberFormatSpec(
            decimals=2,
            thousands=True,
            prefix="$",
            suffix=" USD",
            multiplier=1.0,
            display_scale="M",
        )

        # Serialize to dict
        spec_dict = spec.to_dict()
        assert spec_dict == {
            "decimals": 2,
            "thousands": True,
            "prefix": "$",
            "suffix": " USD",
            "multiplier": 1.0,
            "display_scale": "M",
        }

        # Deserialize from dict
        spec_restored = NumberFormatSpec.from_dict(spec_dict)
        assert spec_restored.decimals == 2
        assert spec_restored.thousands is True
        assert spec_restored.prefix == "$"
        assert spec_restored.suffix == " USD"
        assert spec_restored.multiplier == 1.0
        assert spec_restored.display_scale == "M"

    def test_serialization_defaults(self):
        """Test deserialization with missing fields uses defaults."""
        spec_dict = {"decimals": 3}
        spec = NumberFormatSpec.from_dict(spec_dict)

        assert spec.decimals == 3
        assert spec.thousands is True  # default
        assert spec.prefix == ""  # default
        assert spec.suffix == ""  # default
        assert spec.multiplier == 1.0  # default
        assert spec.display_scale is None  # default


class TestFormatConstants:
    """Test cases for Format namespace constants."""

    def test_format_no_decimals(self):
        """Test Format.NO_DECIMALS constant."""
        assert format_value(1234.56, Format.NO_DECIMALS) == "1,235"
        assert format_value(123, Format.NO_DECIMALS) == "123"

    def test_format_two_decimals(self):
        """Test Format.TWO_DECIMALS constant."""
        assert format_value(1234.56, Format.TWO_DECIMALS) == "1,234.56"
        assert format_value(123, Format.TWO_DECIMALS) == "123.00"

    def test_format_percent(self):
        """Test Format.PERCENT constant."""
        assert format_value(0.1234, Format.PERCENT) == "12%"
        assert format_value(0.5, Format.PERCENT) == "50%"

    def test_format_percent_one_decimal(self):
        """Test Format.PERCENT_ONE_DECIMAL constant."""
        assert format_value(0.1234, Format.PERCENT_ONE_DECIMAL) == "12.3%"
        assert format_value(0.5, Format.PERCENT_ONE_DECIMAL) == "50.0%"

    def test_format_percent_two_decimals(self):
        """Test Format.PERCENT_TWO_DECIMALS constant."""
        assert format_value(0.1234, Format.PERCENT_TWO_DECIMALS) == "12.34%"
        assert format_value(0.5, Format.PERCENT_TWO_DECIMALS) == "50.00%"

    def test_format_currency(self):
        """Test Format.CURRENCY constant."""
        assert format_value(1234.56, Format.CURRENCY) == "$1,234.56"
        assert format_value(123, Format.CURRENCY) == "$123.00"

    def test_format_currency_no_decimals(self):
        """Test Format.CURRENCY_NO_DECIMALS constant."""
        assert format_value(1234.56, Format.CURRENCY_NO_DECIMALS) == "$1,235"
        assert format_value(123, Format.CURRENCY_NO_DECIMALS) == "$123"

    def test_format_millions(self):
        """Test Format.MILLIONS constant."""
        assert format_value(3100000, Format.MILLIONS) == "3.1M"
        assert format_value(1500000, Format.MILLIONS) == "1.5M"

    def test_format_thousands(self):
        """Test Format.THOUSANDS constant."""
        assert format_value(3100, Format.THOUSANDS) == "3.1K"
        assert format_value(1500, Format.THOUSANDS) == "1.5K"
