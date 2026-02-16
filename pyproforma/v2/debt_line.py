"""
DebtLine generator for modeling debt financing.

This module provides a GeneratorLine subclass for modeling debt with principal
payments, interest payments, outstanding balances, and bond proceeds.
"""

from typing import TYPE_CHECKING

from pyproforma.v2.generator_line import GeneratorLine

if TYPE_CHECKING:
    from pyproforma.v2.assumption_values import AssumptionValues
    from pyproforma.v2.line_item_values import LineItemValues


class DebtLine(GeneratorLine):
    """
    A generator for debt financing that produces multiple related fields.

    DebtLine generates four fields for debt modeling:
    - principal: Principal payment for the period
    - interest: Interest payment for the period
    - debt_outstanding: Outstanding debt balance at end of period
    - proceeds: Bond proceeds (new debt issued) in the period

    The debt uses straight-line amortization with constant annual payments
    consisting of principal and interest.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     # Define par amounts and terms
        ...     par_2024 = FixedLine(values={2024: 1000000, 2025: 0, 2026: 500000})
        ...     debt_term = Assumption(value=10)
        ...     interest_rate = Assumption(value=0.05)
        ...
        ...     # Create debt generator
        ...     debt = DebtLine(
        ...         par_amount_name="par_2024",
        ...         interest_rate_name="interest_rate",
        ...         term_name="debt_term"
        ...     )
        ...
        ...     # Access generated fields in formulas
        ...     total_debt_service = FormulaLine(
        ...         formula=lambda a, li, t: li.debt_principal[t] + li.debt_interest[t]
        ...     )

    Attributes:
        par_amount_name (str): Name of line item or assumption containing par amounts
        interest_rate_name (str): Name of assumption containing interest rate
        term_name (str): Name of assumption containing term in years
        label (str, optional): Human-readable label for display purposes
    """

    def __init__(
        self,
        par_amount_name: str,
        interest_rate_name: str,
        term_name: str,
        label: str | None = None,
    ):
        """
        Initialize a DebtLine generator.

        Args:
            par_amount_name (str): Name of line item or assumption with par amounts
                (new debt issued each period)
            interest_rate_name (str): Name of assumption with interest rate
                (as decimal, e.g., 0.05 for 5%)
            term_name (str): Name of assumption with term in years
            label (str, optional): Human-readable label. Defaults to None.
        """
        super().__init__(label=label)
        self.par_amount_name = par_amount_name
        self.interest_rate_name = interest_rate_name
        self.term_name = term_name

        # Track debt service schedules by issue year
        # Format: {issue_year: [{'year': int, 'principal': float,
        #                        'interest': float}, ...]}
        self._debt_schedules = {}

    @property
    def field_names(self) -> list[str]:
        """
        Return the list of field names this generator produces.

        Returns:
            list[str]: ['principal', 'interest', 'debt_outstanding', 'proceeds']
        """
        return ["principal", "interest", "debt_outstanding", "proceeds"]

    def generate_fields(
        self,
        a: "AssumptionValues",
        li: "LineItemValues",
        t: int,
    ) -> dict[str, float]:
        """
        Generate all debt-related field values for a specific period.

        Args:
            a (AssumptionValues): Container for accessing assumption values
            li (LineItemValues): Container for accessing other line item values
            t (int): Current period being calculated

        Returns:
            dict[str, float]: Dictionary with keys 'principal', 'interest',
                'debt_outstanding', and 'proceeds', all as float values.
        """
        # Get parameters (interest rate and term are assumptions,
        # constant across periods)
        interest_rate = getattr(a, self.interest_rate_name)
        term = int(getattr(a, self.term_name))

        # Get par amount for this period (could be from line item or assumption)
        try:
            # Try as line item first
            par_amount_li = getattr(li, self.par_amount_name)
            par_amount = par_amount_li[t] if par_amount_li[t] is not None else 0.0
        except (AttributeError, KeyError):
            # Try as assumption
            par_amount = getattr(a, self.par_amount_name, 0.0)

        par_amount = float(par_amount) if par_amount else 0.0

        # Add new debt issue if par_amount > 0
        if par_amount > 0 and t not in self._debt_schedules:
            schedule = self._generate_debt_schedule(par_amount, interest_rate, t, term)
            self._debt_schedules[t] = schedule

        # Calculate totals for this period across all debt issues
        principal = 0.0
        interest = 0.0

        for issue_year, schedule in self._debt_schedules.items():
            if issue_year <= t:  # Only consider debt issued by this period
                for entry in schedule:
                    if entry["year"] == t:
                        principal += entry["principal"]
                        interest += entry["interest"]

        # Calculate outstanding balance at end of period
        debt_outstanding = 0.0
        for issue_year, schedule in self._debt_schedules.items():
            if issue_year <= t:
                # Outstanding = sum of future principal payments
                for entry in schedule:
                    if entry["year"] > t:
                        debt_outstanding += entry["principal"]

        return {
            "principal": principal,
            "interest": interest,
            "debt_outstanding": debt_outstanding,
            "proceeds": par_amount,
        }

    @staticmethod
    def _generate_debt_schedule(
        par_amount: float, interest_rate: float, start_year: int, term: int
    ) -> list[dict]:
        """
        Generate an amortization schedule for a debt issue.

        Uses standard amortization with constant annual payments. For zero
        interest rate, divides principal evenly across the term.

        Args:
            par_amount (float): Principal amount of the debt
            interest_rate (float): Annual interest rate (as decimal, e.g., 0.05)
            start_year (int): Year of debt issuance
            term (int): Term of the debt in years

        Returns:
            list[dict]: Schedule with entries {'year': int, 'principal': float,
                'interest': float} for each payment year
        """
        schedule = []

        if interest_rate == 0:
            # Zero interest: equal principal payments
            equal_payment = par_amount / term
            for i in range(term):
                year = start_year + i
                schedule.append(
                    {"year": year, "principal": equal_payment, "interest": 0.0}
                )
        else:
            # Standard amortization
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

    def __repr__(self):
        """Return a string representation of the DebtLine."""
        parts = [
            f"par_amount_name={self.par_amount_name!r}",
            f"interest_rate_name={self.interest_rate_name!r}",
            f"term_name={self.term_name!r}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtLine({', '.join(parts)})"
