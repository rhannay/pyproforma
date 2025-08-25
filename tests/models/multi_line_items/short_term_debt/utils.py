

def _is_close(a, b, tolerance=1e-6):
    """Helper function to compare floating point numbers with tolerance."""
    return abs(a - b) < tolerance


def _calculate_interest(balance, rate):
    """Helper function to calculate interest expense."""
    return balance * rate


def _calculate_debt_outstanding(begin_balance, draws_dict, paydown_dict, target_year):
    """
    Helper function to calculate debt outstanding for a given year.
    Follows the same logic as the ShortTermDebt class for testing purposes.
    """
    # Get all years from draws and paydowns to determine the range
    all_years = set(draws_dict.keys()) | set(paydown_dict.keys())
    if not all_years:
        return begin_balance

    min_year = min(all_years)

    # If target year is before any activity, return begin balance
    if target_year < min_year:
        return begin_balance

    # Calculate cumulative balance up to the target year
    balance = begin_balance
    for y in range(min_year, target_year + 1):
        balance += draws_dict.get(y, 0.0)
        balance -= paydown_dict.get(y, 0.0)

    return balance
