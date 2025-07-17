from typing import List, Dict, Optional, Any

from pyproforma.models.multi_line.multi_line_abc import MultiLineItemABC


class Debt(MultiLineItemABC):
    """
    Debt class for modeling debt related line items.
    Inherits from MultiLineItemABC.
    
    This class will handle debt related calculations including principal, interest payments, 
    and debt service schedule. Currently a placeholder implementation.
    """
    
    def __init__(self, 
                name: str,
                par_amounts: dict, 
                interest_rate: float, 
                term: int,
                existing_debt_service: list[dict] = None):
        """
        Initialize a Debt object with specified parameters.
        
        Args:
            name (str): The name of this debt component.
            par_amounts (dict): The principal amounts for each debt issue.
            interest_rate (float): The interest rate applied to the debt.
            term (int): The term of the debt in years.
            existing_debt_service (list[dict], optional): Pre-existing debt service schedule.
        """
        self.name = name
        self.par_amounts = par_amounts
        self.interest_rate = interest_rate
        self.term = term
        
        self.ds_schedules = {}
        
        # TODO: implement this later
        self.existing_debt_service = existing_debt_service or []
    
    
    
    @classmethod
    def _generate_debt_service_schedule(cls, par, interest_rate: float, start_year: int, term: int):
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
            equal_payment = par / term
            for i in range(term):
                year = start_year + i
                schedule.append({
                    'year': year,
                    'principal': equal_payment,
                    'interest': 0.0
                })
        else:
            # Standard amortization calculation for non-zero interest
            annual_payment = (par * interest_rate) / (1 - (1 + interest_rate) ** -term)
            remaining_principal = par
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
    
    @property
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.
        
        Returns:
            List[str]: The names of all line items this component can generate values for.
        """
        return [f'{self.name}.principal', f'{self.name}.interest', f'{self.name}.bond_proceeds']
    
    def get_values(self, interim_values_by_year: Dict[int, Dict[str, Any]],
                  year: int) -> Dict[str, Optional[float]]:
        """
        Get all values for this debt component for a specific year.
        
        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values
                by year, used to prevent circular references and for formula calculations.
            year (int): The year for which to get the values.
            
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this
                                        component for the specified year, with line item names as keys.
                             
        Raises:
            ValueError: If value already exists in interim_values_by_year to prevent circular references.
        """
        # Placeholder implementation
        result = {}
        
        # Check for circular references
        for name in self.defined_names:
            if (year in interim_values_by_year and 
                name in interim_values_by_year[year]):
                raise ValueError(f"Circular reference detected for '{name}' in year {year}.")
            
            # Will be implemented in future
            result[name] = None
            
        return result
    
    def _add_bond_issue(self, par, interest_rate: float, start_year: int, term: int):
        """
        Add a bond issue to the debt service schedules.
        
        Args:
            par: The principal amount of the debt.
            interest_rate (float): Annual interest rate (as a decimal, e.g., 0.05 for 5%).
            start_year (int): The starting year for the debt service.
            term (int): The term of the debt in years.
            
        Raises:
            ValueError: If a debt service schedule already exists with the same start_year.
        """
        # Check if a schedule with this start_year already exists
        if start_year in self.ds_schedules:
            raise ValueError(f"A debt service schedule already exists for year {start_year}")
            
        # Generate debt service schedule using class method
        schedule = self._generate_debt_service_schedule(par, interest_rate, start_year, term)
        
        # Add to ds_schedules with start_year as key
        self.ds_schedules[start_year] = schedule