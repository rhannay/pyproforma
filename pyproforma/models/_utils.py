import re
from typing import List, Union


def validate_name(name):
    """Validate that a name contains only letters, numbers, underscores, or hyphens.

    Args:
        name (str): The name to validate

    Raises:
        ValueError: If the name contains invalid characters
    """
    if not re.match(r"^[A-Za-z0-9_-]+$", name):
        raise ValueError(
            "Name must only contain letters, numbers, underscores, "
            "or hyphens (no spaces or special characters)."
        )


def validate_periods(
    periods: List[Union[int, str]], fill_in_periods: bool = False
) -> List[int]:
    """
    Validate and normalize a list of periods (years).

    Validates that all periods are valid years (integers or strings convertible to
    integers), converts strings to integers, checks for duplicates, and optionally
    fills in missing years between the minimum and maximum values.

    Args:
        periods (List[Union[int, str]]): List of years to validate. Can contain
            integers or strings that represent years (e.g., 2023 or '2023').
        fill_in_periods (bool, optional): If True, fills in missing years between
            the minimum and maximum year in the list. Default is False.

    Returns:
        List[int]: Validated and normalized list of years as integers, sorted in
            ascending order.

    Raises:
        ValueError: If any period cannot be converted to a valid integer year,
            if duplicate years are found, or if the input list is empty.
        TypeError: If periods is None.

    Examples:
        >>> validate_periods([2023, 2024, 2025])
        [2023, 2024, 2025]

        >>> validate_periods(['2023', 2024, '2025'])
        [2023, 2024, 2025]

        >>> validate_periods([2023, 2025], fill_in_periods=True)
        [2023, 2024, 2025]

        >>> validate_periods([2023, 2023])  # Raises ValueError for duplicates

        >>> validate_periods(['invalid'])  # Raises ValueError for invalid year
    """
    if periods is None:
        raise TypeError("Periods cannot be None")

    if not periods:
        raise ValueError("Periods list cannot be empty")

    # Convert all periods to integers and validate
    normalized_periods = []
    for period in periods:
        if isinstance(period, int):
            normalized_periods.append(period)
        elif isinstance(period, str):
            try:
                # Try to convert string to integer
                year = int(period)
                normalized_periods.append(year)
            except ValueError:
                raise ValueError(
                    f"Invalid year: '{period}' cannot be converted to an integer"
                )
        else:
            raise ValueError(
                f"Period must be an integer or string, got {type(period).__name__}: {period}"
            )

    # Check for duplicates
    if len(normalized_periods) != len(set(normalized_periods)):
        # Find the duplicates
        seen = set()
        duplicates = set()
        for year in normalized_periods:
            if year in seen:
                duplicates.add(year)
            seen.add(year)
        raise ValueError(
            f"Duplicate years not allowed: {sorted(duplicates)}"
        )

    # Sort the periods
    sorted_periods = sorted(normalized_periods)

    # Fill in missing periods if requested
    if fill_in_periods and len(sorted_periods) > 1:
        min_year = sorted_periods[0]
        max_year = sorted_periods[-1]
        filled_periods = list(range(min_year, max_year + 1))
        return filled_periods

    return sorted_periods
