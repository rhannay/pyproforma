from typing import List, Dict, Optional, Any

from pyproforma.models.line_item_generator.abc_class import LineItemGenerator
from pyproforma.models._utils import check_name, check_interim_values_by_year


@LineItemGenerator.register("debt")
class Debt(LineItemGenerator):
    """
    Debt class for modeling debt related line items.
    Inherits from LineItemGeneratorABC.
    
    This class will handle debt related calculations including principal, interest payments, 
    and debt service schedule. Currently a placeholder implementation.
    """
    
    def __init__(self, 
                name: str,
                par_amount: dict | str, 
                interest_rate: float | str, 
                term: int | str,
                existing_debt_service: list[dict] = None):
        """
        Initialize a Debt object with specified parameters.
        
        Args:
            name (str): The name of this debt component.
            par_amount (dict | str): The principal amounts for each debt issue. Can be a dict with years as keys
                                   or a string representing a line item name to look up in the value matrix.
            interest_rate (float | str): The interest rate applied to the debt. Can be a float (e.g., 0.05 for 5%)
                                      or a string representing a line item name to look up in the value matrix.
            term (int | str): The term of the debt in years. Can be an integer or a string representing
                           a line item name to look up in the value matrix.
            existing_debt_service (list[dict], optional): Pre-existing debt service schedule.
        """
        if not check_name(name):
            raise ValueError("Debt name must only contain letters, numbers, underscores, or hyphens (no spaces or special characters).")
        self.name = name
        self._par_amount = par_amount
        self._interest_rate = interest_rate
        self._term = term

        # Gather the defined names
        self._principal_name = f'{self.name}.principal'
        self._interest_name = f'{self.name}.interest'
        self._bond_proceeds_name = f'{self.name}.bond_proceeds'

        self.ds_schedules = {}
        
        self.existing_debt_service = existing_debt_service or []
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'Debt':
        """Create a Debt instance from a configuration dictionary."""
        # Convert par_amount keys from strings to integers if it's a dict (for JSON compatibility)
        par_amount = config['par_amount']
        if isinstance(par_amount, dict):
            par_amount = {int(k): v for k, v in par_amount.items()}
        
        return cls(
            name=config['name'],
            par_amount=par_amount,
            interest_rate=config['interest_rate'],
            term=config['term'],
            existing_debt_service=config.get('existing_debt_service')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Debt instance to a dictionary representation."""
        return {
            'type': 'debt',
            'name': self.name,
            'par_amount': self._par_amount,
            'interest_rate': self._interest_rate,
            'term': self._term,
            'existing_debt_service': self.existing_debt_service if self.existing_debt_service else None
        }
    
    # ----------------------------------
    # MAIN PUBLIC API METHODS
    # ----------------------------------
    
    @property
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.
        
        Returns:
            List[str]: The names of all line items this component can generate values for.
        """
        return [self._principal_name, self._interest_name, self._bond_proceeds_name]

    def get_values(self, interim_values_by_year: Dict[int, Dict[str, Any]],
                  year: int) -> Dict[str, Optional[float]]:
        """
        Get all values for this debt component for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.
            
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this
                                        component for the specified year, with line item names as keys.
        """
        # Validate interim values by year
        is_valid, error_msg = check_interim_values_by_year(interim_values_by_year)
        if not is_valid:
            raise ValueError(f"Invalid interim values by year: {error_msg}")

        result = {}
        
        # Build up bond issues
        # Start by clearing out self.debt_service_schedules
        self.ds_schedules = {}
        
        # Extract years from interim_values_by_year keys
        years = sorted([y for y in interim_values_by_year.keys()])

        for _year in [y for y in years if y <= year]:
            # Gather interest rate, par amount, and term for this year bond issue
            interest_rate = self._get_interest_rate(interim_values_by_year, _year)
            par_amount = self._get_par_amount(interim_values_by_year, _year)
            term = self._get_term(interim_values_by_year, _year)

            # Add it to the schedules
            self._add_bond_issue(par_amount, interest_rate, _year, term)

        # Principal and interest payments for this year
        result[self._principal_name] = self.get_principal(year)
        result[self._interest_name] = self.get_interest(year)

        # Bond proceeds (par amounts for new debt issues in this year)
        result[self._bond_proceeds_name] = self._get_par_amount(interim_values_by_year, year)
            
        return result
    
    # ----------------------------------
    # PRINCIPAL AND INTEREST BY YEAR
    # ----------------------------------
    
    def get_principal(self, year: int) -> float:
        """
        Get the total principal payment for a specific year across all debt issues.
        
        Args:
            year (int): The year for which to calculate the total principal payment.
            
        Returns:
            float: The total principal payment for the specified year.
        """
        total_principal = 0.0
        
        # Check existing debt service schedule
        for entry in self.existing_debt_service:
            if entry['year'] == year:
                total_principal += entry['principal']
        
        # Check scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            for entry in schedule:
                if entry['year'] == year:
                    total_principal += entry['principal']
        
        return total_principal
    
    def get_interest(self, year: int) -> float:
        """
        Get the total interest payment for a specific year across all debt issues.
        
        Args:
            year (int): The year for which to calculate the total interest payment.
            
        Returns:
            float: The total interest payment for the specified year.
        """
        total_interest = 0.0
        
        # Check existing debt service schedule
        for entry in self.existing_debt_service:
            if entry['year'] == year:
                total_interest += entry['interest']
        
        # Check scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            for entry in schedule:
                if entry['year'] == year:
                    total_interest += entry['interest']
        
        return total_interest
        
    # ----------------------------------
    # DEBT SCHEDULE MANAGEMENT
    # ----------------------------------
    
    def _add_bond_issue(self, par: float, interest_rate: float, start_year: int, term: int):
        """
        Add a bond issue to the debt service schedules.
        
        Args:
            par (float): The principal amount of the debt.
            interest_rate (float): Annual interest rate as a decimal (e.g., 0.05 for 5%).
            start_year (int): The starting year for the debt service.
            term (int): The term of the debt in years.
            
        Raises:
            ValueError: If a debt service schedule already exists with the same start_year.
        """
        # Check if a schedule with this start_year already exists
        if start_year in self.ds_schedules:
            raise ValueError(f"A debt service schedule already exists for year {start_year}")
            
        # Generate debt service schedule using static method
        schedule = self.generate_debt_service_schedule(par, interest_rate, start_year, term)
        
        # Add to ds_schedules with start_year as key
        self.ds_schedules[start_year] = schedule
    
    @classmethod
    def generate_debt_service_schedule(cls, par_amount, interest_rate: float, start_year: int, term: int):
        """
        Generate an amortization schedule for a debt instrument.
        
        Args:
            par: The principal amount of the debt.
            interest_rate (float): Annual interest rate (as a decimal, e.g., 0.05 for 5%).
            start_year (int): The starting year for the debt service.
            term (int): The term of the debt in years.
            
        Returns:
            list: A list of dictionaries representing the debt service schedule,
                 with each dictionary containing 'year', 'principal', and 'interest'.
        """
        schedule = []
        
        if interest_rate == 0:
            # For zero interest loans, simply divide principal evenly across the term
            equal_payment = par_amount / term
            for i in range(term):
                year = start_year + i
                schedule.append({
                    'year': year,
                    'principal': equal_payment,
                    'interest': 0.0
                })
        else:
            # Standard amortization calculation for non-zero interest
            annual_payment = (par_amount * interest_rate) / (1 - (1 + interest_rate) ** -term)
            remaining_principal = par_amount
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
    
    # ----------------------------------
    # DEBT ISSUE PARAMETER METHODS
    # ----------------------------------
    
    def _get_interest_rate(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """
        Get the interest rate for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used for looking up the interest rate if it's specified as a string.
            year (int): The year for which to get the interest rate.
            
        Returns:
            float: The interest rate as a float value.
            
        Raises:
            ValueError: If the interest_rate is a string but the value cannot be found in interim_values_by_year.
            TypeError: If the interest_rate is not a float or string.
        """
        if isinstance(self._interest_rate, (float, int)):
            return float(self._interest_rate)
        elif isinstance(self._interest_rate, str):
            interest_rate_name = self._interest_rate
            # Look up the value in interim_values_by_year
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
    
    def _get_par_amount(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> float:
        """
        Get the par amount for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used for looking up the par amount if it's specified as a string.
            year (int): The year for which to get the par amount.
            
        Returns:
            float: The par amount as a float value, or 0.0 if no par amount for this year.
            
        Raises:
            ValueError: If the par_amount is a string but the value cannot be found in interim_values_by_year.
            TypeError: If the par_amount is not a dict or string.
        """
        if isinstance(self._par_amount, dict):
            # Direct lookup from the dictionary
            return float(self._par_amount.get(year, 0.0))
        elif isinstance(self._par_amount, str):
            par_amount_name = self._par_amount
            # Look up the value in interim_values_by_year
            if (year in interim_values_by_year and 
                par_amount_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][par_amount_name]
                if value is None:
                    return 0.0
                return float(value)
            else:
                raise ValueError(f"Could not find par amount '{par_amount_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Par amount must be a dict or string, not {type(self._par_amount)}")
    
    def _get_term(self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int) -> int:
        """
        Get the term for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used for looking up the term if it's specified as a string.
            year (int): The year for which to get the term.
            
        Returns:
            int: The term as an integer value.
            
        Raises:
            ValueError: If the term is a string but the value cannot be found in interim_values_by_year,
                        or if the term is zero, negative, or not a whole number.
            TypeError: If the term is not an int or string.
        """
        term_value = None
        
        if isinstance(self._term, int):
            term_value = self._term
        elif isinstance(self._term, str):
            term_name = self._term
            # Look up the value in interim_values_by_year
            if (year in interim_values_by_year and 
                term_name in interim_values_by_year[year]):
                value = interim_values_by_year[year][term_name]
                if value is None:
                    raise ValueError(f"Term '{term_name}' for year {year} is None")
                term_value = int(value)
            else:
                raise ValueError(f"Could not find term '{term_name}' for year {year} in interim values")
        else:
            raise TypeError(f"Term must be an int or string, not {type(self._term)}")
            
        # Validate that the term is a positive whole number greater than zero
        if term_value <= 0:
            raise ValueError(f"Term must be positive, got {term_value}")
        if not isinstance(term_value, int) or term_value != float(term_value):
            raise ValueError(f"Term must be a whole number, got {term_value}")
            
        return term_value