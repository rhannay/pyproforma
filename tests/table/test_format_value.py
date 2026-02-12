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

    def test_format_value_invalid_type(self):
        """Test that invalid value_format type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown format string"):
            format_value(123, "invalid_format_string")
        
        with pytest.raises(ValueError, match="Invalid value_format type: int"):
            format_value(123, 42)
        
        with pytest.raises(ValueError, match="Invalid value_format type: list"):
            format_value(123, [1, 2, 3])


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

    def test_scale_millions_with_suffix(self):
        """Test millions scale with suffix."""
        spec = NumberFormatSpec(decimals=1, thousands=False, scale="millions", suffix="M")
        assert format_value(3100000, spec) == "3.1M"
        assert format_value(1500000, spec) == "1.5M"
        assert format_value(1234567, spec) == "1.2M"

    def test_scale_thousands_with_suffix(self):
        """Test thousands scale with suffix."""
        spec = NumberFormatSpec(decimals=1, thousands=False, scale="thousands", suffix="K")
        assert format_value(3100, spec) == "3.1K"
        assert format_value(1500, spec) == "1.5K"
        assert format_value(999, spec) == "1.0K"

    def test_scale_billions_with_suffix(self):
        """Test billions scale with suffix."""
        spec = NumberFormatSpec(decimals=2, thousands=False, scale="billions", suffix="B")
        assert format_value(3_100_000_000, spec) == "3.10B"
        assert format_value(1_500_000_000, spec) == "1.50B"

    def test_scale_thousands(self):
        """Test scale parameter for thousands without suffix."""
        spec = NumberFormatSpec(decimals=1, thousands=True, scale="thousands")
        assert format_value(3456789, spec) == "3,456.8"
        assert format_value(1234, spec) == "1.2"
        assert format_value(999, spec) == "1.0"

    def test_scale_millions(self):
        """Test scale parameter for millions without suffix."""
        spec = NumberFormatSpec(decimals=2, thousands=True, scale="millions")
        assert format_value(3456789, spec) == "3.46"
        assert format_value(1500000, spec) == "1.50"
        assert format_value(123456, spec) == "0.12"

    def test_scale_billions(self):
        """Test scale parameter for billions without suffix."""
        spec = NumberFormatSpec(decimals=2, thousands=True, scale="billions")
        assert format_value(3_500_000_000, spec) == "3.50"
        assert format_value(1_234_567_890, spec) == "1.23"

    def test_scale_case_insensitive(self):
        """Test that scale parameter is case insensitive."""
        spec_lower = NumberFormatSpec(decimals=1, thousands=True, scale="thousands")
        spec_upper = NumberFormatSpec(decimals=1, thousands=True, scale="THOUSANDS")
        spec_mixed = NumberFormatSpec(decimals=1, thousands=True, scale="Thousands")
        
        assert format_value(3456, spec_lower) == "3.5"
        assert format_value(3456, spec_upper) == "3.5"
        assert format_value(3456, spec_mixed) == "3.5"

    def test_scale_invalid_value(self):
        """Test that invalid scale value raises ValueError."""
        spec = NumberFormatSpec(decimals=1, thousands=True, scale="invalid")
        with pytest.raises(ValueError, match="Invalid scale: invalid"):
            format_value(1234, spec)

    def test_negative_values(self):
        """Test formatting negative values."""
        spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
        assert format_value(-1234.56, spec) == "$-1,234.56"

        spec = NumberFormatSpec(decimals=1, thousands=False, scale="millions", suffix="M")
        assert format_value(-3100000, spec) == "-3.1M"

    def test_serialization(self):
        """Test to_dict and from_dict methods."""
        spec = NumberFormatSpec(
            decimals=2,
            thousands=True,
            prefix="$",
            suffix=" USD",
            multiplier=1.0,
        )

        # Serialize to dict
        spec_dict = spec.to_dict()
        assert spec_dict == {
            "decimals": 2,
            "thousands": True,
            "prefix": "$",
            "suffix": " USD",
            "multiplier": 1.0,
            "scale": None,
        }

        # Deserialize from dict
        spec_restored = NumberFormatSpec.from_dict(spec_dict)
        assert spec_restored.decimals == 2
        assert spec_restored.thousands is True
        assert spec_restored.prefix == "$"
        assert spec_restored.suffix == " USD"
        assert spec_restored.multiplier == 1.0
        assert spec_restored.scale is None

    def test_serialization_with_scale(self):
        """Test serialization with scale parameter."""
        spec = NumberFormatSpec(
            decimals=1,
            thousands=True,
            scale="thousands",
        )

        # Serialize to dict
        spec_dict = spec.to_dict()
        assert spec_dict == {
            "decimals": 1,
            "thousands": True,
            "prefix": "",
            "suffix": "",
            "multiplier": 1.0,
            "scale": "thousands",
        }

        # Deserialize from dict
        spec_restored = NumberFormatSpec.from_dict(spec_dict)
        assert spec_restored.decimals == 1
        assert spec_restored.thousands is True
        assert spec_restored.scale == "thousands"

    def test_serialization_defaults(self):
        """Test deserialization with missing fields uses defaults."""
        spec_dict = {"decimals": 3}
        spec = NumberFormatSpec.from_dict(spec_dict)

        assert spec.decimals == 3
        assert spec.thousands is True  # default
        assert spec.prefix == ""  # default
        assert spec.suffix == ""  # default
        assert spec.multiplier == 1.0  # default
        assert spec.scale is None  # default


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
        """Test Format.MILLIONS constant (no suffix)."""
        assert format_value(3456789, Format.MILLIONS) == "3.5"
        assert format_value(1500000, Format.MILLIONS) == "1.5"

    def test_format_millions_m(self):
        """Test Format.MILLIONS_M constant (with suffix)."""
        assert format_value(3100000, Format.MILLIONS_M) == "3.1M"
        assert format_value(1500000, Format.MILLIONS_M) == "1.5M"

    def test_format_thousands(self):
        """Test Format.THOUSANDS constant (no suffix)."""
        assert format_value(3456789, Format.THOUSANDS) == "3,456.8"
        assert format_value(1234, Format.THOUSANDS) == "1.2"

    def test_format_thousands_k(self):
        """Test Format.THOUSANDS_K constant (with suffix)."""
        assert format_value(3100, Format.THOUSANDS_K) == "3.1K"
        assert format_value(1500, Format.THOUSANDS_K) == "1.5K"
