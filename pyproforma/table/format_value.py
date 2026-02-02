"""Value formatting utilities for table cells."""

from typing import Any, Optional

from ..constants import ValueFormat


def format_value(
    value: Any, value_format: Optional[ValueFormat], none_returns=""
) -> Any:
    """Format a value according to the specified format.

    Args:
        value: The value to format
        value_format: The format to apply. Options: 'str', 'no_decimals', 
            'two_decimals', 'percent', 'percent_one_decimal', 'percent_two_decimals', 'year'
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
    """
    if value is None:
        return none_returns
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
