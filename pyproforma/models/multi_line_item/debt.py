from typing import Any, Dict, List, Optional

from pyproforma.models._utils import validate_name
from pyproforma.models.model.value_matrix import validate_value_matrix
from pyproforma.models.multi_line_item.abc_class import MultiLineItem


@MultiLineItem.register("debt")
class Debt(MultiLineItem):
    """
    Debt class for modeling debt related line items.
    Inherits from MultiLineItem.

    This class will handle debt related calculations including principal, interest payments,  # noqa: E501
    and debt service schedule. Currently a placeholder implementation.
    """  # noqa: E501

    def __init__(
        self,
        name: str,
        par_amount: dict | str,
        interest_rate: float | str,
        term: int | str,
        existing_debt_service: list[dict] = None,
    ):
        """
        Initialize a Debt object with specified parameters.

        Args:
            name (str): The name of this debt component.
            par_amount (dict | str): The principal amounts for each debt issue. Can be a dict with years as keys  # noqa: E501
                                   or a string representing a line item name to look up in the value matrix.  # noqa: E501
            interest_rate (float | str): The interest rate applied to the debt. Can be a float (e.g., 0.05 for 5%)  # noqa: E501
                                      or a string representing a line item name to look up in the value matrix.  # noqa: E501
            term (int | str): The term of the debt in years. Can be an integer or a string representing  # noqa: E501
                           a line item name to look up in the value matrix.  # noqa: E501
            existing_debt_service (list[dict], optional): Pre-existing debt service schedule for debts that  # noqa: E501
                                                        were issued before the model period. Each dictionary  # noqa: E501
                                                        in the list should contain the following keys:  # noqa: E501
                                                        - 'year' (int): The year of the payment  # noqa: E501
                                                        - 'principal' (float): The principal payment amount  # noqa: E501
                                                        - 'interest' (float): The interest payment amount  # noqa: E501
                                                        Example: [{'year': 2024, 'principal': 1000.0, 'interest': 50.0},  # noqa: E501
                                                                 {'year': 2025, 'principal': 1000.0, 'interest': 40.0}]  # noqa: E501
                                                        Defaults to None (empty list).
        """  # noqa: E501
        validate_name(name)
        self.name = name
        self._par_amount = par_amount
        self._interest_rate = interest_rate
        self._term = term

        # Gather the defined names
        self._principal_name = f"{self.name}_principal"
        self._interest_name = f"{self.name}_interest"
        self._bond_proceeds_name = f"{self.name}_bond_proceeds"
        self._debt_outstanding_name = f"{self.name}_debt_outstanding"

        self.ds_schedules = {}

        self.existing_debt_service = existing_debt_service or []
        # Validate the existing debt service structure
        self._validate_existing_debt_service(self.existing_debt_service)

    @classmethod
    def _validate_existing_debt_service(cls, existing_debt_service: list[dict]):
        """
        Validate the existing_debt_service structure to ensure it's correctly formatted.

        Args:
            existing_debt_service (list[dict]): The existing debt service schedule to validate.  # noqa: E501

        Raises:
            ValueError: If the existing_debt_service is not properly structured or has gaps in years.  # noqa: E501
        """  # noqa: E501
        if not existing_debt_service:
            return  # Empty list or None is valid

        # Check that it's a list
        if not isinstance(existing_debt_service, list):
            raise ValueError("existing_debt_service must be a list of dictionaries")

        # Check each entry is a dictionary with required keys
        required_keys = {"year", "principal", "interest"}
        for i, entry in enumerate(existing_debt_service):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"existing_debt_service entry {i} must be a dictionary"
                )

            # Check required keys
            if not required_keys.issubset(entry.keys()):
                missing_keys = required_keys - entry.keys()
                raise ValueError(
                    f"existing_debt_service entry {i} is missing required keys: {missing_keys}"  # noqa: E501
                )

            # Validate data types
            if not isinstance(entry["year"], int):
                raise ValueError(
                    f"existing_debt_service entry {i}: 'year' must be an integer"
                )

            if not isinstance(entry["principal"], (int, float)):
                raise ValueError(
                    f"existing_debt_service entry {i}: 'principal' must be a number"
                )

            if not isinstance(entry["interest"], (int, float)):
                raise ValueError(
                    f"existing_debt_service entry {i}: 'interest' must be a number"
                )

            # Validate non-negative values
            if entry["principal"] < 0:
                raise ValueError(
                    f"existing_debt_service entry {i}: 'principal' must be non-negative"
                )

            if entry["interest"] < 0:
                raise ValueError(
                    f"existing_debt_service entry {i}: 'interest' must be non-negative"
                )

        # Check for sequential years with no gaps
        years = [entry["year"] for entry in existing_debt_service]

        # Check that years are provided in ascending order
        if len(years) > 1:
            for i in range(1, len(years)):
                if years[i] <= years[i - 1]:
                    raise ValueError(
                        "existing_debt_service years must be provided in ascending order"  # noqa: E501
                    )

        # Check for sequential years with no gaps (years are already in order and no duplicates)  # noqa: E501
        if len(years) > 1:
            for i in range(1, len(years)):
                if years[i] != years[i - 1] + 1:
                    raise ValueError(
                        f"existing_debt_service years must be sequential with no gaps. "
                        f"Gap found between {years[i - 1]} and {years[i]}"
                    )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Debt":
        """Create a Debt instance from a configuration dictionary."""
        # Convert par_amount keys from strings to integers if it's a dict (for JSON compatibility)  # noqa: E501
        par_amount = config["par_amount"]
        if isinstance(par_amount, dict):
            par_amount = {int(k): v for k, v in par_amount.items()}

        return cls(
            name=config["name"],
            par_amount=par_amount,
            interest_rate=config["interest_rate"],
            term=config["term"],
            existing_debt_service=config.get("existing_debt_service"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Debt instance to a dictionary representation."""
        return {
            "type": "debt",
            "name": self.name,
            "par_amount": self._par_amount,
            "interest_rate": self._interest_rate,
            "term": self._term,
            "existing_debt_service": self.existing_debt_service
            if self.existing_debt_service
            else None,
        }

    # ----------------------------------
    # MAIN PUBLIC API METHODS
    # ----------------------------------

    @property
    def defined_names(self) -> List[str]:
        """
        Returns a list of all line item names defined by this component.

        Returns:
            List[str]: The names of all line items this component can generate values for.  # noqa: E501
        """  # noqa: E501
        return [
            self._principal_name,
            self._interest_name,
            self._bond_proceeds_name,
            self._debt_outstanding_name,
        ]

    def get_values(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> Dict[str, Optional[float]]:
        """
        Get all values for this debt component for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used to prevent circular references and for formula calculations.  # noqa: E501
                The keys of this dictionary represent all years in the model.
            year (int): The year for which to get the values.

        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated values for all defined line items in this  # noqa: E501
                                        component for the specified year, with line item names as keys.  # noqa: E501
        """  # noqa: E501
        # Validate interim values by year
        validate_value_matrix(interim_values_by_year)

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
        result[self._bond_proceeds_name] = self._get_par_amount(
            interim_values_by_year, year
        )

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
            if entry["year"] == year:
                total_principal += entry["principal"]

        # Check scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            for entry in schedule:
                if entry["year"] == year:
                    total_principal += entry["principal"]

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
            if entry["year"] == year:
                total_interest += entry["interest"]

        # Check scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            for entry in schedule:
                if entry["year"] == year:
                    total_interest += entry["interest"]

        return total_interest

    def get_debt_outstanding(self, year: int) -> float:
        """
        Get the total outstanding principal at the end of a specific year across all debt issues.  # noqa: E501

        Args:
            year (int): The year for which to calculate the outstanding principal.

        Returns:
            float: The total outstanding principal at the end of the specified year.
        """  # noqa: E501
        total_outstanding = 0.0

        # Calculate outstanding balance from existing debt service
        existing_outstanding = self._calculate_debt_outstanding_for_issue(
            self.existing_debt_service, year
        )
        total_outstanding += existing_outstanding

        # Calculate outstanding balance from scheduled debt issues
        for start_year, schedule in self.ds_schedules.items():
            if start_year <= year:  # Only consider debt issued by the end of this year
                outstanding = self._calculate_debt_outstanding_for_issue(schedule, year)
                total_outstanding += outstanding

        return total_outstanding

    @classmethod
    def _calculate_debt_outstanding_for_issue(
        cls, debt_service_schedule: list[dict], year: int
    ) -> float:
        """
        Calculate the outstanding principal for a debt service schedule at the end of a specific year.  # noqa: E501

        Args:
            debt_service_schedule (list[dict]): The debt service schedule containing payment entries.  # noqa: E501
            year (int): The year for which to calculate the outstanding principal.

        Returns:
            float: The outstanding principal from the debt service schedule.
        """  # noqa: E501
        if not debt_service_schedule:
            return 0.0

        # Outstanding principal is just the sum of all principal payments due after this year  # noqa: E501
        return sum(
            entry["principal"]
            for entry in debt_service_schedule
            if entry["year"] > year
        )

    # ----------------------------------
    # DEBT SCHEDULE MANAGEMENT
    # ----------------------------------

    def _add_bond_issue(
        self, par: float, interest_rate: float, start_year: int, term: int
    ):
        """
        Add a bond issue to the debt service schedules.

        Args:
            par (float): The principal amount of the debt.
            interest_rate (float): Annual interest rate as a decimal (e.g., 0.05 for 5%).  # noqa: E501
            start_year (int): The starting year for the debt service.
            term (int): The term of the debt in years.

        Raises:
            ValueError: If a debt service schedule already exists with the same start_year.  # noqa: E501
        """  # noqa: E501
        # Check if a schedule with this start_year already exists
        if start_year in self.ds_schedules:
            raise ValueError(
                f"A debt service schedule already exists for year {start_year}"
            )

        # Generate debt service schedule using static method
        schedule = self.generate_debt_service_schedule(
            par, interest_rate, start_year, term
        )

        # Add to ds_schedules with start_year as key
        self.ds_schedules[start_year] = schedule

    @classmethod
    def generate_debt_service_schedule(
        cls, par_amount, interest_rate: float, start_year: int, term: int
    ):
        """
        Generate an amortization schedule for a debt instrument.

        Args:
            par: The principal amount of the debt.
            interest_rate (float): Annual interest rate (as a decimal, e.g., 0.05 for 5%).  # noqa: E501
            start_year (int): The starting year for the debt service.
            term (int): The term of the debt in years.

        Returns:
            list: A list of dictionaries representing the debt service schedule,
                 with each dictionary containing 'year', 'principal', and 'interest'.
        """  # noqa: E501
        schedule = []

        if interest_rate == 0:
            # For zero interest loans, simply divide principal evenly across the term
            equal_payment = par_amount / term
            for i in range(term):
                year = start_year + i
                schedule.append(
                    {"year": year, "principal": equal_payment, "interest": 0.0}
                )
        else:
            # Standard amortization calculation for non-zero interest
            annual_payment = (par_amount * interest_rate) / (
                1 - (1 + interest_rate) ** -term
            )
            remaining_principal = par_amount
            for i in range(term):
                year = start_year + i
                interest = remaining_principal * interest_rate
                principal_payment = annual_payment - interest
                schedule.append(
                    {"year": year, "principal": principal_payment, "interest": interest}
                )
                remaining_principal -= principal_payment

        return schedule

    # ----------------------------------
    # DEBT ISSUE PARAMETER METHODS
    # ----------------------------------

    def _get_interest_rate(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> float:
        """
        Get the interest rate for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used for looking up the interest rate if it's specified as a string.  # noqa: E501
            year (int): The year for which to get the interest rate.

        Returns:
            float: The interest rate as a float value.

        Raises:
            ValueError: If the interest_rate is a string but the value cannot be found in interim_values_by_year.  # noqa: E501
            TypeError: If the interest_rate is not a float or string.
        """  # noqa: E501
        if isinstance(self._interest_rate, (float, int)):
            return float(self._interest_rate)
        elif isinstance(self._interest_rate, str):
            interest_rate_name = self._interest_rate
            # Look up the value in interim_values_by_year
            if (
                year in interim_values_by_year
                and interest_rate_name in interim_values_by_year[year]
            ):
                value = interim_values_by_year[year][interest_rate_name]
                if value is None:
                    raise ValueError(
                        f"Interest rate '{interest_rate_name}' for year {year} is None"
                    )
                return float(value)
            else:
                raise ValueError(
                    f"Could not find interest rate '{interest_rate_name}' for year {year} in interim values"  # noqa: E501
                )
        else:
            raise TypeError(
                f"Interest rate must be a float or string, not {type(self._interest_rate)}"  # noqa: E501
            )

    def _get_par_amount(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> float:
        """
        Get the par amount for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used for looking up the par amount if it's specified as a string.  # noqa: E501
            year (int): The year for which to get the par amount.

        Returns:
            float: The par amount as a float value, or 0.0 if no par amount for this year.  # noqa: E501

        Raises:
            ValueError: If the par_amount is a string but the value cannot be found in interim_values_by_year.  # noqa: E501
            TypeError: If the par_amount is not a dict or string.
        """  # noqa: E501
        if isinstance(self._par_amount, dict):
            # Direct lookup from the dictionary
            return float(self._par_amount.get(year, 0.0))
        elif isinstance(self._par_amount, str):
            par_amount_name = self._par_amount
            # Look up the value in interim_values_by_year
            if (
                year in interim_values_by_year
                and par_amount_name in interim_values_by_year[year]
            ):
                value = interim_values_by_year[year][par_amount_name]
                if value is None:
                    return 0.0
                return float(value)
            else:
                raise ValueError(
                    f"Could not find par amount '{par_amount_name}' for year {year} in interim values"  # noqa: E501
                )
        else:
            raise TypeError(
                f"Par amount must be a dict or string, not {type(self._par_amount)}"
            )

    def _get_term(
        self, interim_values_by_year: Dict[int, Dict[str, Any]], year: int
    ) -> int:
        """
        Get the term for a specific year.

        Args:
            interim_values_by_year (Dict[int, Dict[str, Any]]): Dictionary containing calculated values  # noqa: E501
                by year, used for looking up the term if it's specified as a string.
            year (int): The year for which to get the term.

        Returns:
            int: The term as an integer value.

        Raises:
            ValueError: If the term is a string but the value cannot be found in interim_values_by_year,  # noqa: E501
                        or if the term is zero, negative, or not a whole number.
            TypeError: If the term is not an int or string.
        """  # noqa: E501
        term_value = None

        if isinstance(self._term, int):
            term_value = self._term
        elif isinstance(self._term, str):
            term_name = self._term
            # Look up the value in interim_values_by_year
            if (
                year in interim_values_by_year
                and term_name in interim_values_by_year[year]
            ):
                value = interim_values_by_year[year][term_name]
                if value is None:
                    raise ValueError(f"Term '{term_name}' for year {year} is None")
                term_value = int(value)
            else:
                raise ValueError(
                    f"Could not find term '{term_name}' for year {year} in interim values"  # noqa: E501
                )
        else:
            raise TypeError(f"Term must be an int or string, not {type(self._term)}")

        # Validate that the term is a positive whole number greater than zero
        if term_value <= 0:
            raise ValueError(f"Term must be positive, got {term_value}")
        if not isinstance(term_value, int) or term_value != float(term_value):
            raise ValueError(f"Term must be a whole number, got {term_value}")

        return term_value
