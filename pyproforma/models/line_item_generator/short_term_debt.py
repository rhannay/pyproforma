from typing import List, Dict, Optional, Any

from pyproforma.models.line_item_generator.abc_class import LineItemGenerator
from pyproforma.models._utils import check_name, check_interim_values_by_year


@LineItemGenerator.register("short_term_debt")
class ShortTermDebt(LineItemGenerator):
    """
    ShortTermDebt class for modeling short-term debt line items.
    Inherits from LineItemGenerator ABC.
    
    A generator for modeling short-term debt instruments such as credit lines, revolving credit, 
    or other variable debt facilities.
    
    This class calculates debt outstanding balances, draws, principal payments, and interest 
    expenses over time based on specified draw and paydown schedules. It supports flexible 
    modeling of debt facilities where the outstanding balance can vary based on business needs.
    
    The start year is automatically determined from the minimum year in interim_values_by_year
    when get_values() is called.
    
    Args:
        name (str): Unique identifier for the debt instrument. Must contain only letters, 
            numbers, underscores, or hyphens (no spaces or special characters).
        draws (dict | str): Dictionary mapping years (int) to draw amounts (float), or string 
            representing a line item name to look up in interim_values_by_year. Represents 
            additional borrowings in each year. Empty dict if no draws.
        paydown (dict | str): Dictionary mapping years (int) to paydown amounts (float), or string 
            representing a line item name to look up in interim_values_by_year. Represents 
            principal payments in each year. Empty dict if no paydowns.
        begin_balance (float): Initial outstanding debt balance at the start of the model.
        interest_rate (float | dict | str): Annual interest rate. Can be:
            - float: Fixed rate for all years (e.g., 0.05 for 5%)
            - dict: Dictionary mapping years (int) to rates (float) for year-specific rates
            - str: String representing a line item name to look up in interim_values_by_year
    
    Examples:
        >>> # Credit line with fixed parameters
        >>> credit_line = ShortTermDebt(
        ...     name='working_capital_line',
        ...     draws={2024: 500000, 2025: 300000},
        ...     paydown={2025: 200000, 2026: 600000},
        ...     begin_balance=1000000,
        ...     interest_rate=0.06
        ... )
        >>> 
        >>> # Credit line with year-specific interest rates
        >>> credit_line = ShortTermDebt(
        ...     name='variable_line',
        ...     draws={2024: 500000},
        ...     paydown={2025: 200000},
        ...     begin_balance=1000000,
        ...     interest_rate={2024: 0.05, 2025: 0.06, 2026: 0.065}
        ... )
        >>> 
        >>> # Credit line with dynamic interest rate lookup
        >>> credit_line = ShortTermDebt(
        ...     name='dynamic_line',
        ...     draws={2024: 500000},
        ...     paydown={2025: 200000},
        ...     begin_balance=1000000,
        ...     interest_rate='prime_rate'  # Look up from interim_values_by_year
        ... )
    """
    
    def __init__(
            self, 
            name: str,
            draws: dict | str = None, 
            paydown: dict | str = None, 
            begin_balance: float = 0.0,
            interest_rate: float | dict | str = 0.0):
        
        if not check_name(name):
            raise ValueError("Short term debt name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        
        self.name = name
        self._draws = draws if draws is not None else {}
        self._paydown = paydown if paydown is not None else {}
        self._begin_balance = begin_balance
        self._interest_rate = interest_rate
        
        # Validate interest rate is not negative if it's a number
        if isinstance(interest_rate, (float, int)) and interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        
        # Validate interest rate dict values are not negative if it's a dict
        if isinstance(interest_rate, dict):
            for year, rate in interest_rate.items():
                if rate < 0:
                    raise ValueError(f"Interest rate for year {year} cannot be negative")
        
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

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ShortTermDebt':
        """Create a ShortTermDebt instance from a configuration dictionary."""
        # Convert draws and paydown keys from strings to integers if they're dicts (for JSON compatibility)
        draws = config.get('draws')
        if isinstance(draws, dict):
            draws = {int(k): v for k, v in draws.items()}
        
        paydown = config.get('paydown')
        if isinstance(paydown, dict):
            paydown = {int(k): v for k, v in paydown.items()}
        
        # Convert interest_rate keys from strings to integers if it's a dict (for JSON compatibility)
        interest_rate = config['interest_rate']
        if isinstance(interest_rate, dict):
            interest_rate = {int(k): v for k, v in interest_rate.items()}
        
        return cls(
            name=config['name'],
            draws=draws,
            paydown=paydown,
            begin_balance=config.get('begin_balance', 0.0),
            interest_rate=interest_rate
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ShortTermDebt instance to a dictionary representation."""
        return {
            'type': 'short_term_debt',
            'name': self.name,
            'draws': self._draws,
            'paydown': self._paydown,
            'begin_balance': self._begin_balance,
            'interest_rate': self._interest_rate
        }

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
            ValueError: If draws or paydowns are prior to the start year.
        """
        # Validate interim values by year
        is_valid, error_msg = check_interim_values_by_year(interim_values_by_year)
        if not is_valid:
            raise ValueError(f"Invalid interim values by year: {error_msg}")

        result = {}
        
        # Get start year and validate draws/paydowns are not before it
        start_year = self._get_start_year(interim_values_by_year, year)
        self._validate_years_not_before_start(start_year)
        
        result[self._debt_outstanding_name] = self._get_debt_outstanding(interim_values_by_year, year)
        result[self._draw_name] = self._get_draw(interim_values_by_year, year)
        result[self._principal_name] = self._get_paydown(interim_values_by_year, year)
        result[self._interest_name] = self._get_interest(interim_values_by_year, year)
        
        return result
    
    # ----------------------------------
    # PARAMETER LOOKUP METHODS
    # ----------------------------------
    
    def _get_start_year(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> int:
        """Get the start year - just the first year in interim_values_by_year."""
        if not interim_values_by_year:
            raise ValueError("No years available in interim_values_by_year to determine start year")
        
        # Simply return the first year in the dictionary (assume years are in order, don't sort)
        return list(interim_values_by_year.keys())[0]
    
    def _validate_years_not_before_start(self, start_year: int) -> None:
        """
        Validate that draws and paydowns are not prior to the start year.
        
        Args:
            start_year (int): The start year for the model.
            
        Raises:
            ValueError: If any draws or paydowns are prior to the start year.
        """
        # Check draws if they are specified as a dict
        if isinstance(self._draws, dict):
            for year in self._draws.keys():
                if year < start_year:
                    raise ValueError(f"Draw year {year} is prior to start year {start_year}")
        
        # Check paydowns if they are specified as a dict
        if isinstance(self._paydown, dict):
            for year in self._paydown.keys():
                if year < start_year:
                    raise ValueError(f"Paydown year {year} is prior to start year {start_year}")
    
    def _get_begin_balance(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int = None) -> float:
        """Get the begin balance from the fixed value."""
        if isinstance(self._begin_balance, (float, int)):
            return float(self._begin_balance)
        else:
            raise TypeError(f"Begin balance must be a float, not {type(self._begin_balance)}")
    
    def _get_interest_rate(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """Get the interest rate, from a fixed value, dict lookup by year, or interim_values_by_year lookup."""
        if isinstance(self._interest_rate, (float, int)):
            return float(self._interest_rate)
        elif isinstance(self._interest_rate, dict):
            # Look up interest rate by year in the provided dict
            if year in self._interest_rate:
                return float(self._interest_rate[year])
            else:
                raise ValueError(f"Interest rate for year {year} not found in interest rate dictionary")
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
            raise TypeError(f"Interest rate must be a float, dict, or string, not {type(self._interest_rate)}")
    
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
        
        # For dynamic parameters (strings), find the first year with available data
        if isinstance(self._draws, str) or isinstance(self._paydown, str):
            available_years = sorted(interim_values_by_year.keys())
            min_year = None
            for check_year in available_years:
                year_data = interim_values_by_year[check_year]
                
                # Check if the required dynamic parameters exist in this year
                draws_available = (not isinstance(self._draws, str) or 
                                 self._draws in year_data)
                paydown_available = (not isinstance(self._paydown, str) or 
                                   self._paydown in year_data)
                
                if draws_available and paydown_available:
                    min_year = check_year
                    break
            
            if min_year is None:
                # If we can't find a year with all required data, use start_year
                # The actual lookup will fail later with a proper error message
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