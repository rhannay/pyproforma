from .generator_class import Generator
from ..models._utils import check_name
from typing import Dict, Any


@Generator.register("short_term_debt")
class ShortTermDebt(Generator):
    """
    A generator for modeling short-term debt instruments such as credit lines, revolving credit, 
    or other variable debt facilities.
    
    This class calculates debt outstanding balances, draws, principal payments, and interest 
    expenses over time based on specified draw and paydown schedules. It supports flexible 
    modeling of debt facilities where the outstanding balance can vary based on business needs.
    
    Args:
        name (str): Unique identifier for the debt instrument. Must contain only letters, 
            numbers, underscores, or hyphens (no spaces or special characters).
        draws (dict): Dictionary mapping years (int) to draw amounts (float). Represents 
            additional borrowings in each year. Empty dict if no draws.
        paydown (dict): Dictionary mapping years (int) to paydown amounts (float). Represents 
            principal payments in each year. Empty dict if no paydowns.
        begin_balance (float): Initial outstanding debt balance at the start of the model.
        interest_rate (float): Annual interest rate as a decimal (e.g., 0.05 for 5%).
        start_year (int): First year for which calculations are valid. Queries before this 
            year will raise ValueError.
    
    Raises:
        ValueError: If name contains invalid characters, if interest_rate is negative, 
            or if any draw/paydown amounts are negative.
    
    Examples:
        >>> # Credit line with initial balance and variable draws/paydowns
        >>> credit_line = ShortTermDebt(
        ...     name='working_capital_line',
        ...     draws={2024: 500000, 2025: 300000},
        ...     paydown={2025: 200000, 2026: 600000},
        ...     begin_balance=1000000,
        ...     interest_rate=0.06,
        ...     start_year=2024
        ... )
        >>> 
        >>> # Get debt outstanding in 2025
        >>> credit_line.get_debt_outstanding(2025)  # 1600000.0
        >>> 
        >>> # Get all values for 2025
        >>> credit_line.get_values(2025)
        {
            'working_capital_line.debt_outstanding': 1600000.0,
            'working_capital_line.draw': 300000.0,
            'working_capital_line.principal': 200000.0,
            'working_capital_line.interest': 90000.0
        }
    
    Note:
        Interest is calculated on the debt balance at the beginning of each year.
        For the start_year, this equals the begin_balance. For subsequent years,
        it equals the previous year's ending balance.
    """
    def __init__(
            self, 
            name: str,
            draws: dict, 
            paydown: dict, 
            begin_balance: float,
            interest_rate: float,
            start_year: int):
        
        if not check_name(name):
            raise ValueError("Short term debt name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        
        self.name = name
        self.draws = draws if draws is not None else {}
        self.paydown = paydown if paydown is not None else {}
        self.begin_balance = begin_balance
        self.interest_rate = interest_rate
        self.start_year = start_year
        
        # Validate interest rate is not negative
        if interest_rate < 0:
            raise ValueError("Interest rate cannot be negative")
        
        # Validate draws and paydown values are not negative
        for year, amount in self.draws.items():
            if amount < 0:
                raise ValueError(f"Draw amount for year {year} cannot be negative")
        
        for year, amount in self.paydown.items():
            if amount < 0:
                raise ValueError(f"Paydown amount for year {year} cannot be negative")
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ShortTermDebt':
        """Create a ShortTermDebt instance from a configuration dictionary."""
        # Convert draws and paydown keys from strings to integers (for JSON compatibility)
        draws = {int(k): v for k, v in config.get('draws', {}).items()}
        paydown = {int(k): v for k, v in config.get('paydown', {}).items()}
        
        return cls(
            name=config['name'],
            draws=draws,
            paydown=paydown,
            begin_balance=config['begin_balance'],
            interest_rate=config['interest_rate'],
            start_year=config['start_year']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ShortTermDebt instance to a dictionary representation."""
        return {
            'type': 'short_term_debt',
            'name': self.name,
            'draws': self.draws,
            'paydown': self.paydown,
            'begin_balance': self.begin_balance,
            'interest_rate': self.interest_rate,
            'start_year': self.start_year
        }
    
    @property
    def defined_names(self) -> list[str]:
        return [f'{self.name}.debt_outstanding', f'{self.name}.draw', f'{self.name}.principal', f'{self.name}.interest']
    
    def get_values(self, year: int) -> dict:
        return {
            f'{self.name}.debt_outstanding': self.get_debt_outstanding(year),
            f'{self.name}.draw': self.get_draw(year),
            f'{self.name}.principal': self.get_paydown(year),
            f'{self.name}.interest': self.get_interest(year)
        }

    def get_debt_outstanding(self, year: int) -> float:
        """
        Calculate the outstanding debt balance for a given year.
        Outstanding balance = previous year balance + draws - paydowns
        """
        # Check if year is before start_year (allow start_year - 1 as it returns begin_balance)
        if year < self.start_year - 1:
            raise ValueError(f"Cannot calculate debt outstanding for year {year} as it is before the start year {self.start_year}")
        
        # If asking for the year before start_year, return begin_balance
        if year == self.start_year - 1:
            return self.begin_balance
        
        # Get all years from draws and paydowns to determine the range
        all_years = set(self.draws.keys()) | set(self.paydown.keys())
        if not all_years:
            return self.begin_balance
        
        min_year = min(all_years)
        
        # If year is before any activity, return begin balance
        if year < min_year:
            return self.begin_balance
        
        # Calculate cumulative balance up to the given year
        balance = self.begin_balance
        for y in range(min_year, year + 1):
            balance += self.draws.get(y, 0.0)
            balance -= self.paydown.get(y, 0.0)
        
        return balance
    
    def get_draw(self, year: int) -> float:
        """Get the draw amount for a given year."""
        return self.draws.get(year, 0.0)
    
    def get_paydown(self, year: int) -> float:
        """Get the paydown amount for a given year."""
        return self.paydown.get(year, 0.0)
    
    def get_interest(self, year: int) -> float:
        """
        Calculate the interest expense for a given year.
        Interest is calculated based on the debt outstanding at the beginning of the year.
        """
        # Check if year is before start_year
        if year < self.start_year:
            raise ValueError(f"Cannot calculate interest for year {year} as it is before the start year {self.start_year}")
        
        # Use previous year's ending balance (which equals begin_balance for start_year)
        previous_year_balance = self.get_debt_outstanding(year - 1)
        return previous_year_balance * self.interest_rate