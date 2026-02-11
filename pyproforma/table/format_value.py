"""Value formatting utilities for table cells."""

from dataclasses import dataclass
from typing import Any, Optional, Union


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

    def format(self, value: Any) -> str:
        """Format a value using this specification.

        Args:
            value: The numeric value to format

        Returns:
            The formatted string

        Examples:
            >>> spec = NumberFormatSpec(decimals=2, thousands=True, prefix="$")
            >>> spec.format(1234.56)
            '$1,234.56'
        """
        # Apply multiplier first
        formatted_value = value * self.multiplier

        # Apply scale if specified
        if self.scale:
            scale_map = {
                "thousands": 1_000,
                "millions": 1_000_000,
                "billions": 1_000_000_000,
                "trillions": 1_000_000_000_000,
            }
            scale_factor = scale_map.get(self.scale.lower())
            if scale_factor:
                formatted_value = formatted_value / scale_factor
            else:
                raise ValueError(
                    f"Invalid scale: {self.scale}. "
                    f"Valid options: {', '.join(scale_map.keys())}"
                )

        # Format the number with appropriate decimals and thousands separator
        if self.thousands:
            if self.decimals == 0:
                formatted_str = f"{int(round(formatted_value)):,}"
            else:
                formatted_str = f"{formatted_value:,.{self.decimals}f}"
        else:
            if self.decimals == 0:
                formatted_str = str(int(round(formatted_value)))
            else:
                formatted_str = f"{formatted_value:.{self.decimals}f}"

        # Add prefix and suffix
        return self.prefix + formatted_str + self.suffix


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

    # Mapping of string names to format constants
    _STRING_MAP = {
        "no_decimals": NO_DECIMALS,
        "two_decimals": TWO_DECIMALS,
        "percent": PERCENT,
        "percent_one_decimal": PERCENT_ONE_DECIMAL,
        "percent_two_decimals": PERCENT_TWO_DECIMALS,
        "currency": CURRENCY,
        "currency_no_decimals": CURRENCY_NO_DECIMALS,
        "thousands": THOUSANDS,
        "millions": MILLIONS,
        "thousands_k": THOUSANDS_K,
        "millions_m": MILLIONS_M,
    }

    @classmethod
    def from_string(cls, format_str: str) -> NumberFormatSpec:
        """Convert a string format name to NumberFormatSpec.

        Args:
            format_str: String name of the format (case-insensitive).
                Valid values: 'no_decimals', 'two_decimals', 'percent',
                'percent_one_decimal', 'percent_two_decimals', 'currency',
                'currency_no_decimals', 'thousands', 'millions',
                'thousands_k', 'millions_m'

        Returns:
            The corresponding NumberFormatSpec instance

        Raises:
            ValueError: If the format string is not recognized

        Examples:
            >>> Format.from_string('percent')
            NumberFormatSpec(decimals=0, thousands=False, suffix='%', multiplier=100)
            >>> Format.from_string('currency')
            NumberFormatSpec(decimals=2, thousands=True, prefix='$')
        """
        normalized = format_str.lower().strip()
        if normalized in cls._STRING_MAP:
            return cls._STRING_MAP[normalized]
        
        valid_formats = ', '.join(f"'{k}'" for k in sorted(cls._STRING_MAP.keys()))
        raise ValueError(
            f"Unknown format string: '{format_str}'. "
            f"Valid formats are: {valid_formats}"
        )


def normalize_format(
    value_format: Optional[Union[str, NumberFormatSpec, dict]]
) -> Optional[NumberFormatSpec]:
    """Normalize a value_format parameter to a NumberFormatSpec instance.

    Args:
        value_format: The format to normalize. Can be:
            - str: A format name like 'percent', 'currency', etc.
            - NumberFormatSpec: Returned as-is
            - dict: Converted to NumberFormatSpec via from_dict()
            - None: Returns None

    Returns:
        A NumberFormatSpec instance or None

    Raises:
        ValueError: If an invalid value_format type is provided

    Examples:
        >>> normalize_format('percent')
        NumberFormatSpec(decimals=0, thousands=False, suffix='%', multiplier=100)
        >>> normalize_format(Format.CURRENCY)
        NumberFormatSpec(decimals=2, thousands=True, prefix='$')
        >>> normalize_format({'decimals': 3, 'prefix': '$'})
        NumberFormatSpec(decimals=3, prefix='$')
        >>> normalize_format(None) is None
        True
    """
    if value_format is None:
        return None

    if isinstance(value_format, str):
        return Format.from_string(value_format)

    if isinstance(value_format, dict):
        return NumberFormatSpec.from_dict(value_format)

    if isinstance(value_format, NumberFormatSpec):
        return value_format

    raise ValueError(
        f"Invalid value_format type: {type(value_format).__name__}. "
        f"Expected str, NumberFormatSpec, dict, or None."
    )


def format_value(
    value: Any,
    value_format: Optional[Union[str, NumberFormatSpec, dict]] = None,
    none_returns="",
) -> Any:
    """Format a value according to the specified format.

    Args:
        value: The value to format
        value_format: The format to apply. Can be a string format name
            (e.g., 'percent', 'currency'), a NumberFormatSpec instance,
            a dict (which will be converted to NumberFormatSpec), or None.
        none_returns: Value to return if value is None (default: empty string)

    Returns:
        The formatted value, or the original value if value_format is None

    Raises:
        ValueError: If an invalid value_format type is provided

    Examples:
        >>> format_value(1234.56, Format.CURRENCY)
        '$1,234.56'
        >>> format_value(1234.56, 'currency')
        '$1,234.56'
        >>> format_value(0.1234, 'percent')
        '12%'
        >>> format_value(1234.56, None)
        1234.56
        >>> format_value(3100000, Format.MILLIONS)
        '3.1'
    """
    if value is None:
        return none_returns

    if value_format is None:
        return value

    normalized = normalize_format(value_format)
    if normalized is not None:
        return normalized.format(value)

    return value
