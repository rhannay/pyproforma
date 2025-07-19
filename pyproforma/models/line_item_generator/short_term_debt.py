from typing import List, Dict, Optional, Any

from pyproforma.models.line_item_generator.abc_class import LineItemGenerator
from pyproforma.models._utils import check_name


class ShortTermDebt(LineItemGenerator):
    """
    ShortTermDebt class for modeling short-term debt line items.
    Inherits from LineItemGenerator ABC.
    
    A generator for modeling short-term debt instruments such as credit lines, revolving credit, 
    or other variable debt facilities.
    
    This class calculates debt outstanding balances, draws, principal payments, and interest 
    expenses over time based on specified draw and paydown schedules. It supports flexible 
    modeling of debt facilities where the outstanding balance can vary based on business needs.
    
    Args:
        name (str): Unique identifier for the debt instrument. Must contain only letters, 
            numbers, underscores, or hyphens (no spaces or special characters).
        draws (dict | str): Dictionary mapping years (int) to draw amounts (float), or string 
            representing a line item name to look up in interim_values_by_year. Represents 
            additional borrowings in each year. Empty dict if no draws.
        paydown (dict | str): Dictionary mapping years (int) to paydown amounts (float), or string 
            representing a line item name to look up in interim_values_by_year. Represents 
            principal payments in each year. Empty dict if no paydowns.
        begin_balance (float | str): Initial outstanding debt balance at the start of the model,
            or string representing a line item name to look up in interim_values_by_year.
        interest_rate (float | str): Annual interest rate as a decimal (e.g., 0.05 for 5%),
            or string representing a line item name to look up in interim_values_by_year.
        start_year (int | str): First year for which calculations are valid. Queries before this 
            year will raise ValueError. Can be string representing a line item name to look up.
    
    Examples:
        >>> # Credit line with fixed parameters
        >>> credit_line = ShortTermDebt(
        ...     name='working_capital_line',
        ...     draws={2024: 500000, 2025: 300000},
        ...     paydown={2025: 200000, 2026: 600000},
        ...     begin_balance=1000000,
        ...     interest_rate=0.06,
        ...     start_year=2024
        ... )
        >>> 
        >>> # Credit line with dynamic interest rate
        >>> credit_line = ShortTermDebt(
        ...     name='variable_line',
        ...     draws={2024: 500000},
        ...     paydown={2025: 200000},
        ...     begin_balance=1000000,
        ...     interest_rate='prime_rate',  # Look up from interim_values_by_year
        ...     start_year=2024
        ... )
    """
    
    def __init__(
            self, 
            name: str,
            draws: dict | str = None, 
            paydown: dict | str = None, 
            begin_balance: float | str = 0.0,
            interest_rate: float | str = 0.0,
            start_year: int | str = 2024):
        
        if not check_name(name):
            raise ValueError("Short term debt name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        
        self.name = name
        self._draws = draws if draws is not None else {}
        self._paydown = paydown if paydown is not None else {}
        self._begin_balance = begin_balance
        self._interest_rate = interest_rate
        self._start_year = start_year
        
        # Validate interest rate is not negative if it's a number
        if isinstance(interest_rate, (int, float)) and interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        
        # Validate draws and paydown values are not negative if they're dicts
        if isinstance(draws, dict):
            for year, amount in draws.items():
                if amount < 0:
                    raise ValueError(f"Draw amount for year {year} cannot be negative")
        
        if isinstance(paydown, dict):
            for year, amount in paydown.items():
                if amount < 0:
                    raise ValueError(f"Paydown amount for year {year} cannot be negative")
        
        # Define the line item names
        self._debt_outstanding_name = f'{self.name}.debt_outstanding'
        self._draw_name = f'{self.name}.draw'
        self._principal_name = f'{self.name}.principal'
        self._interest_name = f'{self.name}.interest'

    # ----------------------------------
    # MAIN PUBLIC API METHODS (LineItemGenerator ABC)
    # ----------------------------------
    
    @property
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.
        
        Returns:
            List[str]: The names of all line items this component can generate values for.
        """
        return [self._debt_outstanding_name, self._draw_name, self._principal_name, self._interest_name]

    def get_values(self, interim_values_by_year: Dict[int, Dict[str, Any]],
                  year: int) -> Dict[str, Optional[float]]:
        """
        Get all values for this short-term debt component for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.
            
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this
                                        component for the specified year, with line item names as keys.
                             
        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.
        """
        result = {}
        
        # Get dynamic parameters for this calculation
        start_year = self._get_start_year(interim_values_by_year, year)
        
        result[self._debt_outstanding_name] = self._get_debt_outstanding(interim_values_by_year, year)
        result[self._draw_name] = self._get_draw(interim_values_by_year, year)
        result[self._principal_name] = self._get_paydown(interim_values_by_year, year)
        result[self._interest_name] = self._get_interest(interim_values_by_year, year)
        
        return result
    
    # ----------------------------------
    # PARAMETER LOOKUP METHODS
    # ----------------------------------
    
    def _get_start_year(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> int:
        """Get the start year, either from a fixed value or interim_values_by_year lookup."""
        if isinstance(self._start_year, int):
            return self._start_year
        elif isinstance(self._start_year, str):
            start_year_name = self._start_year
            if (year in interim_values_by_year and 
                start_year_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][start_year_name]
                if value is None:
                    raise ValueError(f"Start year '{start_year_name}' for year {year} is None")
                return int(value)
            else:
                raise ValueError(f"Could not find start year '{start_year_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Start year must be an int or string, not {type(self._start_year)}")
    
    def _get_begin_balance(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int = None) -> float:
        """Get the begin balance, either from a fixed value or interim_values_by_year lookup."""
        if isinstance(self._begin_balance, (int, float)):
            return float(self._begin_balance)
        elif isinstance(self._begin_balance, str):
            begin_balance_name = self._begin_balance
            # For dynamic begin balance, find the first year that contains this key
            available_years = sorted(interim_values_by_year.keys())
            if not available_years:
                raise ValueError(f"No years available in interim_values_by_year to lookup begin balance '{begin_balance_name}'")
            
            # Find the first year that contains the begin balance key
            for lookup_year in available_years:
                if (lookup_year in interim_values_by_year and 
                    begin_balance_name in interim_values_by_year[lookup_year]):
                    value = interim_values_by_year[lookup_year][begin_balance_name]
                    if value is None:
                        return 0.0
                    return float(value)
            
            # If we get here, the key wasn't found in any year
            raise ValueError(f"Could not find begin balance '{begin_balance_name}' in any year in interim values")
        else:
            raise TypeError(f"Begin balance must be a float or string, not {type(self._begin_balance)}")
    
    def _get_interest_rate(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the interest rate, either from a fixed value or interim_values_by_year lookup."""
        if isinstance(self._interest_rate, (int, float)):
            return float(self._interest_rate)
        elif isinstance(self._interest_rate, str):
            interest_rate_name = self._interest_rate
            if (year in interim_values_by_year and 
                interest_rate_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][interest_rate_name]
                if value is None:
                    raise ValueError(f"Interest rate '{interest_rate_name}' for year {year} is None")
                return float(value)
            else:
                raise ValueError(f"Could not find interest rate '{interest_rate_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Interest rate must be a float or string, not {type(self._interest_rate)}")
    
    def _get_draws_for_year(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the draws for a specific year, either from dict or interim_values_by_year lookup."""
        if isinstance(self._draws, dict):
            return float(self._draws.get(year, 0.0))
        elif isinstance(self._draws, str):
            draws_name = self._draws
            if (year in interim_values_by_year and 
                draws_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][draws_name]
                if value is None:
                    return 0.0
                return float(value)
            else:
                raise ValueError(f"Could not find draws '{draws_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Draws must be a dict or string, not {type(self._draws)}")
    
    def _get_paydown_for_year(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the paydown for a specific year, either from dict or interim_values_by_year lookup."""
        if isinstance(self._paydown, dict):
            return float(self._paydown.get(year, 0.0))
        elif isinstance(self._paydown, str):
            paydown_name = self._paydown
            if (year in interim_values_by_year and 
                paydown_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][paydown_name]
                if value is None:
                    return 0.0
                return float(value)
            else:
                raise ValueError(f"Could not find paydown '{paydown_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Paydown must be a dict or string, not {type(self._paydown)}")

    # ----------------------------------
    # BUSINESS LOGIC METHODS (Adapted from generators/short_term_debt.py)
    # ----------------------------------

    def _get_debt_outstanding(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """
        Calculate the outstanding debt balance for a given year.
        Outstanding balance = previous year balance + draws - paydowns
        """
        start_year = self._get_start_year(interim_values_by_year, year)
        begin_balance = self._get_begin_balance(interim_values_by_year)
        
        # Check if year is before start_year (allow start_year - 1 as it returns begin_balance)
        if year < start_year - 1:
            raise ValueError(f"Cannot calculate debt outstanding for year {year} as it is before the start year {start_year}")
        
        # If asking for the year before start_year, return begin_balance
        if year == start_year - 1:
            return begin_balance
        
        # Get all years from draws and paydowns to determine the range
        draws_years = set()
        paydown_years = set()
        
        if isinstance(self._draws, dict):
            draws_years = set(self._draws.keys())
        if isinstance(self._paydown, dict):
            paydown_years = set(self._paydown.keys())
        
        all_years = draws_years | paydown_years
        
        # For dynamic parameters (strings), we don't know the years in advance
        # so we use start_year as the minimum year
        if isinstance(self._draws, str) or isinstance(self._paydown, str):
            min_year = start_year
        elif not all_years:
            return begin_balance
        else:
            min_year = min(all_years)
        
        # If year is before any activity, return begin balance
        if year < min_year:
            return begin_balance
        
        # Calculate cumulative balance up to the given year
        balance = begin_balance
        for y in range(min_year, year + 1):
            balance += self._get_draws_for_year(interim_values_by_year, y)
            balance -= self._get_paydown_for_year(interim_values_by_year, y)
        
        return balance

    def _get_draw(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the draw amount for a given year."""
        return self._get_draws_for_year(interim_values_by_year, year)

    def _get_paydown(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the paydown amount for a given year."""
        return self._get_paydown_for_year(interim_values_by_year, year)

    def _get_interest(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """
        Calculate the interest expense for a given year.
        Interest is calculated based on the debt outstanding at the beginning of the year.
        """
        start_year = self._get_start_year(interim_values_by_year, year)
        
        # Check if year is before start_year
        if year < start_year:
            raise ValueError(f"Cannot calculate interest for year {year} as it is before the start year {start_year}")
        
        # Use previous year's ending balance (which equals begin_balance for start_year)
        previous_year_balance = self._get_debt_outstanding(interim_values_by_year, year - 1)
        interest_rate = self._get_interest_rate(interim_values_by_year, year)
        
        return previous_year_balance * interest_rate