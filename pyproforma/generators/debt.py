from .generator_class import Generator
from ..models._utils import check_name
from typing import Dict, Any


@Generator.register("debt")
class Debt(Generator):
    def __init__(
            self, 
            name: str,
            par_amounts: dict, 
            interest_rate: float, 
            term: int,
            existing_debt_service: list[dict] = None):
        
        if not check_name(name):
            raise ValueError("Debt name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        
        # Validate existing_debt_service if provided
        if existing_debt_service is not None:
            self._validate_existing_debt_service(existing_debt_service)
        
        self.name = name
        self.existing_debt_service = existing_debt_service if existing_debt_service is not None else []
        self.interest_rate = interest_rate
        self.term = term
        years = list(par_amounts.keys())
        schedules = {}
        for year in years:
            par = par_amounts[year]
            if par < 0:
                raise ValueError("Principal amount cannot be negative.")
            if par > 0:  # Only generate schedule for positive amounts
                schedules[year] = generate_debt_service_schedule(par, interest_rate, year, term)
        self.schedules = schedules
        self.par_amounts = par_amounts
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Debt':
        """Create a Debt instance from a configuration dictionary."""
        # Convert par_amounts keys from strings to integers (for JSON compatibility)
        par_amounts = {int(k): v for k, v in config['par_amounts'].items()}
        
        return cls(
            name=config['name'],
            par_amounts=par_amounts,
            interest_rate=config['interest_rate'],
            term=config['term'],
            existing_debt_service=config.get('existing_debt_service')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Debt instance to a dictionary representation."""
        return {
            'type': 'debt',
            'name': self.name,
            'par_amounts': self.par_amounts,
            'interest_rate': self.interest_rate,
            'term': self.term,
            'existing_debt_service': self.existing_debt_service if self.existing_debt_service else None
        }
    
    @property
    def defined_names(self) -> list[str]:
        return [f'{self.name}.principal', f'{self.name}.interest', f'{self.name}.bond_proceeds']
    
    def get_values(self, year: int) -> dict:
        return {
            f'{self.name}.principal': self.get_total_principal(year),
            f'{self.name}.interest': self.get_total_interest(year),
            f'{self.name}.bond_proceeds': self.par_amounts.get(year, 0.0)
        }

    def get_total_principal(self, year: int) -> float:
        total_principal = 0.0
        
        # Add principal from new debt schedules
        for issue_year, schedule in self.schedules.items():
            total_principal += sum(entry['principal'] for entry in schedule if entry['year'] == year)
        
        # Add principal from existing debt service
        for entry in self.existing_debt_service:
            if entry['year'] == year:
                total_principal += entry['principal']
        
        return total_principal
    
    def get_total_interest(self, year: int) -> float:
        total_interest = 0.0
        
        # Add interest from new debt schedules
        for issue_year, schedule in self.schedules.items():
            total_interest += sum(entry['interest'] for entry in schedule if entry['year'] == year)
        
        # Add interest from existing debt service
        for entry in self.existing_debt_service:
            if entry['year'] == year:
                total_interest += entry['interest']
        
        return total_interest

    def _validate_existing_debt_service(self, existing_debt_service: list[dict]) -> None:
        """
        Validate existing_debt_service list of dicts.
        
        Checks:
        - Each dict has required keys: year, principal, interest
        - Years are sequential with no gaps or overlaps
        - Principal and interest are not negative
        """
        if not existing_debt_service:
            return
        
        # Check that each dict has required keys and valid values
        for i, entry in enumerate(existing_debt_service):
            if not isinstance(entry, dict):
                raise ValueError(f"existing_debt_service[{i}] must be a dict")
            
            required_keys = {'year', 'principal', 'interest'}
            if not required_keys.issubset(entry.keys()):
                missing_keys = required_keys - entry.keys()
                raise ValueError(f"existing_debt_service[{i}] missing required keys: {missing_keys}")
            
            # Validate year is an integer
            if not isinstance(entry['year'], int):
                raise ValueError(f"existing_debt_service[{i}]['year'] must be an integer")
            
            # Validate principal and interest are not negative
            if entry['principal'] < 0:
                raise ValueError(f"existing_debt_service[{i}]['principal'] cannot be negative")
            
            if entry['interest'] < 0:
                raise ValueError(f"existing_debt_service[{i}]['interest'] cannot be negative")
        
        # Check that years are sequential with no gaps or overlaps
        years = [entry['year'] for entry in existing_debt_service]
        
        # Check for duplicates
        if len(years) != len(set(years)):
            duplicates = [year for year in set(years) if years.count(year) > 1]
            raise ValueError(f"existing_debt_service has duplicate years: {duplicates}")
        
        # Check for sequential years (no gaps)
        sorted_years = sorted(years)
        if len(sorted_years) > 1:
            for i in range(1, len(sorted_years)):
                if sorted_years[i] != sorted_years[i-1] + 1:
                    raise ValueError(f"existing_debt_service years must be sequential with no gaps. Gap found between {sorted_years[i-1]} and {sorted_years[i]}")


def generate_debt_service_schedule(par, interest_rate: float, start_year: int, term: int):
    annual_payment = (par * interest_rate) / (1 - (1 + interest_rate) ** -term)
    remaining_principal = par
    schedule = []
    for i in range(term):
        year = start_year + i
        interest = remaining_principal * interest_rate
        principal_payment = annual_payment - interest
        schedule.append({
            'year': year,
            'principal': principal_payment,
            'interest': interest
        })
        remaining_principal -= principal_payment
    
    return schedule
