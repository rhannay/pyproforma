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
            existing_debt_service (list[dict], optional): Pre-existing debt service schedule for debts that
                                                        were issued before the model period. Each dictionary
                                                        in the list should contain the following keys:
                                                        - 'year' (int): The year of the payment
                                                        - 'principal' (float): The principal payment amount
                                                        - 'interest' (float): The interest payment amount
                                                        Example: [{'year': 2024, 'principal': 1000.0, 'interest': 50.0},
                                                                 {'year': 2025, 'principal': 1000.0, 'interest': 40.0}]
                                                        Defaults to None (empty list).
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
        self._debt_outstanding_name = f'{self.name}.debt_outstanding'

        self.ds_schedules = {}
        
        self.existing_debt_service = existing_debt_service or []
        # Validate the existing debt service structure
        self._validate_existing_debt_service(self.existing_debt_service)
    
    @classmethod
    def _validate_existing_debt_service(cls, existing_debt_service: list[dict]):
        """
        Validate the existing_debt_service structure to ensure it's correctly formatted.
        
        Args:
            existing_debt_service (list[dict]): The existing debt service schedule to validate.
        
        Raises:
            ValueError: If the existing_debt_service is not properly structured or has gaps in years.
        """
        if not existing_debt_service:
            return  # Empty list or None is valid
        
        # Check that it's a list
        if not isinstance(existing_debt_service, list):
            raise ValueError("existing_debt_service must be a list of dictionaries")
        
        # Check each entry is a dictionary with required keys
        required_keys = {'year', 'principal', 'interest'}
        for i, entry in enumerate(existing_debt_service):
            if not isinstance(entry, dict):
                raise ValueError(f"existing_debt_service entry {i} must be a dictionary")
            
            # Check required keys
            if not required_keys.issubset(entry.keys()):
                missing_keys = required_keys - entry.keys()
                raise ValueError(f"existing_debt_service entry {i} is missing required keys: {missing_keys}")
            
            # Validate data types
            if not isinstance(entry['year'], int):
                raise ValueError(f"existing_debt_service entry {i}: 'year' must be an integer")
            
            if not isinstance(entry['principal'], (int, float)):
                raise ValueError(f"existing_debt_service entry {i}: 'principal' must be a number")
            
            if not isinstance(entry['interest'], (int, float)):
                raise ValueError(f"existing_debt_service entry {i}: 'interest' must be a number")
            
            # Validate non-negative values
            if entry['principal'] < 0:
                raise ValueError(f"existing_debt_service entry {i}: 'principal' must be non-negative")
            
            if entry['interest'] < 0:
                raise ValueError(f"existing_debt_service entry {i}: 'interest' must be non-negative")
        
        # Check for sequential years with no gaps
        years = sorted([entry['year'] for entry in existing_debt_service])
        
        # Remove duplicates and check for them
        unique_years = list(set(years))
        if len(unique_years) != len(years):
            duplicate_years = [year for year in years if years.count(year) > 1]
            raise ValueError(f"existing_debt_service contains duplicate years: {set(duplicate_years)}")
        
        # Check for sequential years with no gaps
        if len(unique_years) > 1:
            for i in range(1, len(unique_years)):
                if unique_years[i] != unique_years[i-1] + 1:
                    raise ValueError(f"existing_debt_service years must be sequential with no gaps. "
                                   f"Gap found between {unique_years[i-1]} and {unique_years[i]}")
    
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
        return [self._principal_name, self._interest_name, self._bond_proceeds_name, self._debt_outstanding_name]

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

            # Only add debt service schedule if par amount is greater than zero
            if par_amount > 0:
                self._add_bond_issue(par_amount, interest_rate, _year, term)

        # Principal and interest payments for this year
        result[self._principal_name] = self.get_principal(year)
        result[self._interest_name] = self.get_interest(year)

        # Bond proceeds (par amounts for new debt issues in this year)
        result[self._bond_proceeds_name] = self._get_par_amount(interim_values_by_year, year)
        
        # Outstanding debt at the end of this year
        result[self._debt_outstanding_name] = self.get_debt_outstanding(year)
            
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
        
    def get_debt_outstanding(self, year: int) -> float:
        """
        Get the total outstanding principal at the end of a specific year across all debt issues.
        
        Args:
            year (int): The year for which to calculate the outstanding principal.
            
        Returns:
            float: The total outstanding principal at the end of the specified year.
        """
        total_outstanding = 0.0
        
        # Calculate outstanding balance from existing debt service
        existing_outstanding = self._calculate_debt_outstanding_for_issue(self.existing_debt_service, year)
        total_outstanding += existing_outstanding
        
        # Calculate outstanding balance from scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            if start_year <= year:  # Only consider debt issued by the end of this year
                outstanding = self._calculate_debt_outstanding_for_issue(schedule, year)
                total_outstanding += outstanding
        
        return total_outstanding
    
    @classmethod
    def _calculate_debt_outstanding_for_issue(cls, debt_service_schedule: list[dict], year: int) -> float:
        """
        Calculate the outstanding principal for a debt service schedule at the end of a specific year.
        
        Args:
            debt_service_schedule (list[dict]): The debt service schedule containing payment entries.
            year (int): The year for which to calculate the outstanding principal.
            
        Returns:
            float: The outstanding principal from the debt service schedule.
        """
        if not debt_service_schedule:
            return 0.0
        
        # Outstanding principal is just the sum of all principal payments due after this year
        return sum(entry['principal'] for entry in debt_service_schedule if entry['year'] > year)
        
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