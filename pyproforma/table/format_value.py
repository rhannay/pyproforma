"""Value formatting utilities for table cells."""

from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

# Type alias for valid value formats
ValueFormat = Literal[
    None,
    "str",
    "no_decimals",
    "two_decimals",
    "percent",
    "percent_one_decimal",
    "percent_two_decimals",
    "year",
]


@dataclass(frozen=True)
class NumberFormatSpec:
    """Specification for number formatting with flexible display options.

    Defines how numbers should be formatted for display, including decimal precision,
    thousands separators, prefixes/suffixes, multipliers, and scale indicators.

    Args:
        decimals: Number of decimal places to display (0, 1, 2, etc.)
        thousands: Whether to include thousands separator (commas)
        prefix: String to prepend to the formatted value (e.g., "$" for currency)
        suffix: String to append to the formatted value (e.g., "%" for percentages,
            "M" for millions, "K" for thousands)
        multiplier: Multiplier to apply before formatting (e.g., 100 for
            percentages). Applied before scale.
        scale: Scale to apply (e.g., "thousands", "millions").
            Divides the value before formatting. Use with or without suffix.

    Examples:
        >>> # Currency format
        >>> spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
        >>> format_value(1234.56, spec)
        '$1,234.56'

        >>> # Percentage format
        >>> spec = NumberFormatSpec(
        ...     decimals=0, thousands=False, suffix="%", multiplier=100
        ... )
        >>> format_value(0.1234, spec)
        '12%'

        >>> # Millions with suffix
        >>> spec = NumberFormatSpec(decimals=1, thousands=False, scale="millions", suffix="M")
        >>> format_value(3100000, spec)
        '3.1M'

        >>> # Millions without suffix (for tables labeled "in millions")
        >>> spec = NumberFormatSpec(decimals=1, thousands=True, scale="millions")
        >>> format_value(3100000, spec)
        '3.1'
    """

    decimals: int = 0
    thousands: bool = True
    prefix: str = ""
    suffix: str = ""
    multiplier: float = 1.0
    scale: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize NumberFormatSpec to dictionary."""
        return {
            "decimals": self.decimals,
            "thousands": self.thousands,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "multiplier": self.multiplier,
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NumberFormatSpec":
        """Deserialize NumberFormatSpec from dictionary."""
        return cls(
            decimals=data.get("decimals", 0),
            thousands=data.get("thousands", True),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", ""),
            multiplier=data.get("multiplier", 1.0),
            scale=data.get("scale", None),
        )


class Format:
    """Namespace for common number format specifications.

    Provides pre-defined format constants for common formatting needs.
    All constants are NumberFormatSpec instances that can be used directly
    or modified for custom formatting.

    Examples:
        >>> from pyproforma.table import Format, format_value
        >>> format_value(1234.56, Format.NO_DECIMALS)
        '1,235'
        >>> format_value(1234.56, Format.CURRENCY)
        '$1,234.56'
        >>> format_value(0.1234, Format.PERCENT)
        '12%'
        >>> format_value(3100000, Format.MILLIONS)
        '3.1M'
    """

    # Integer with thousands separator
    NO_DECIMALS = NumberFormatSpec(decimals=0, thousands=True)

    # Float with 2 decimals and thousands separator
    TWO_DECIMALS = NumberFormatSpec(decimals=2, thousands=True)

    # Percentage formats (multiply by 100 and add % suffix)
    PERCENT = NumberFormatSpec(decimals=0, thousands=False, suffix="%", multiplier=100)
    PERCENT_ONE_DECIMAL = NumberFormatSpec(
        decimals=1, thousands=False, suffix="%", multiplier=100
    )
    PERCENT_TWO_DECIMALS = NumberFormatSpec(
        decimals=2, thousands=False, suffix="%", multiplier=100
    )

    # Currency formats ($ prefix)
    CURRENCY = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
    CURRENCY_NO_DECIMALS = NumberFormatSpec(decimals=0, thousands=True, prefix="$")

    # Large number scale formats (for tables labeled "in thousands/millions")
    THOUSANDS = NumberFormatSpec(decimals=1, thousands=True, scale="thousands")
    MILLIONS = NumberFormatSpec(decimals=1, thousands=True, scale="millions")
    
    # Large number scale formats with suffix
    THOUSANDS_K = NumberFormatSpec(decimals=1, thousands=False, scale="thousands", suffix="K")
    MILLIONS_M = NumberFormatSpec(decimals=1, thousands=False, scale="millions", suffix="M")


def format_value(
    value: Any,
    value_format: Optional[Union[ValueFormat, NumberFormatSpec]],
    none_returns="",
) -> Any:
    """Format a value according to the specified format.

    Args:
        value: The value to format
        value_format: The format to apply. Can be a string format (legacy), a
            NumberFormatSpec instance, or None. String options: 'str',
            'no_decimals', 'two_decimals', 'percent', 'percent_one_decimal',
            'percent_two_decimals', 'year'
        none_returns: Value to return if value is None. Defaults to empty string.

    Returns:
        The formatted value

    Raises:
        ValueError: If an invalid value_format is provided

    Examples:
        >>> format_value(123.45, None)
        123.45
        >>> format_value(123.45, "str")
        '123.45'
        >>> format_value(123.456, "two_decimals")
        '123.46'
        >>> format_value(0.1234, "percent")
        '12%'
        >>> format_value(1234.56, Format.CURRENCY)
        '$1,234.56'
        >>> format_value(3100000, Format.MILLIONS)
        '3.1M'
    """
    if value is None:
        return none_returns

    # Handle NumberFormatSpec instances
    if isinstance(value_format, NumberFormatSpec):
        return _format_with_spec(value, value_format)

    # Handle legacy string formats and None
    if value_format is None:
        return value
    if value_format == "str":
        return str(value)
    elif value_format == "no_decimals":
        return f"{int(round(value)):,}"
    elif value_format == "two_decimals":
        return f"{value:,.2f}"
    elif value_format == "percent":
        return f"{int(round(value * 100))}%"
    elif value_format == "percent_one_decimal":
        return f"{value * 100:.1f}%"
    elif value_format == "percent_two_decimals":
        return f"{value * 100:.2f}%"
    elif value_format == "year":
        return str(int(round(value)))
    else:
        raise ValueError(f"Invalid value_format: {value_format}")


def _format_with_spec(value: Any, spec: NumberFormatSpec) -> str:
    """Format a value using a NumberFormatSpec.

    Args:
        value: The numeric value to format
        spec: The NumberFormatSpec defining the format

    Returns:
        The formatted string

    Examples:
        >>> spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
        >>> _format_with_spec(1234.56, spec)
        '$1,234.56'
    """
    # Apply multiplier first
    formatted_value = value * spec.multiplier

    # Apply scale if specified
    if spec.scale:
        scale_map = {
            "thousands": 1_000,
            "millions": 1_000_000,
            "billions": 1_000_000_000,
            "trillions": 1_000_000_000_000,
        }
        scale_factor = scale_map.get(spec.scale.lower())
        if scale_factor:
            formatted_value = formatted_value / scale_factor
        else:
            raise ValueError(
                f"Invalid scale: {spec.scale}. "
                f"Valid options: {', '.join(scale_map.keys())}"
            )

    # Format the number with appropriate decimals and thousands separator
    if spec.thousands:
        if spec.decimals == 0:
            formatted_str = f"{int(round(formatted_value)):,}"
        else:
            formatted_str = f"{formatted_value:,.{spec.decimals}f}"
    else:
        if spec.decimals == 0:
            formatted_str = str(int(round(formatted_value)))
        else:
            formatted_str = f"{formatted_value:.{spec.decimals}f}"

    # Add prefix and suffix
    return spec.prefix + formatted_str + spec.suffix
