"""
Debt line items for bond principal and interest payments.

This module provides specialized line items for tracking bond debt service
across multiple issuances. It handles level annual debt service amortization
where each bond issue has constant annual payments of principal plus interest.

Classes:
    DebtCalculator: Manages debt schedules and calculations across periods.
    DebtBase: Abstract base class for debt-related line items.
    DebtPrincipalLine: Line item that returns principal payments.
    DebtInterestLine: Line item that returns interest payments.

Functions:
    create_debt_lines: Factory function to create matched principal and interest lines.

Example:
    >>> # Create bond proceeds line item
    >>> bond_proceeds = FixedLine(values={2024: 1_000_000, 2026: 500_000})
    >>>
    >>> # Create debt lines using factory
    >>> principal, interest = create_debt_lines(
    ...     par_amounts_line_item='bond_proceeds',
    ...     interest_rate=0.05,
    ...     term=10
    ... )
    >>>
    >>> # Add to model
    >>> class MyModel(ProformaModel):
    ...     bond_proceeds = FixedLine(values={2024: 1_000_000, 2026: 500_000})
    ...     principal_payment = principal
    ...     interest_expense = interest
"""

from abc import abstractmethod
from typing import TYPE_CHECKING

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.v2.assumption_values import AssumptionValues
    from .line_item_values import LineItemValues


class DebtCalculator:
    """
    Stateful calculator for debt schedules across multiple bond issues.

    DebtCalculator tracks all bond issuances and their amortization schedules,
    providing principal and interest amounts for each period. It uses level
    annual debt service amortization where each bond has constant total payments.

    The calculator is called period-by-period through the eval() method, which
    checks for new bond issuances and updates internal schedules accordingly.

    Attributes:
        par_amounts_line_item (str): Name of the line item containing par amounts.
        interest_rate (float): Annual interest rate for all bonds.
        term (int): Term in years for all bonds.

    Example:
        >>> calculator = DebtCalculator(
        ...     par_amounts_line_item='bond_proceeds',
        ...     interest_rate=0.05,
        ...     term=10
        ... )
        >>> # Calculator is used internally by DebtPrincipalLine and DebtInterestLine
    """

    def __init__(
        self,
        par_amounts_line_item: str,
        interest_rate: float,
        term: int,
    ):
        """
        Initialize a DebtCalculator.

        Args:
            par_amounts_line_item (str): Name of the line item to check for new
                bond issuances. When this line item has a non-zero value for a
                period, a new bond issue is layered on.
            interest_rate (float): Annual interest rate (e.g., 0.05 for 5%).
            term (int): Term in years for bond amortization.
        """
        self.par_amounts_line_item = par_amounts_line_item
        self.interest_rate = interest_rate
        self.term = term

        # Internal state: schedules for each bond issue
        # Structure: {issue_year: {period: {'principal': float, 'interest': float, 'balance': float}}}
        self._schedules: dict[int, dict[int, dict[str, float]]] = {}

        # Track the last period evaluated to detect non-sequential calls
        self._last_period: int | None = None

    def eval(
        self,
        a: "AssumptionValues",
        li: "LineItemValues",
        t: int,
    ) -> None:
        """
        Process a period by checking for new bond issuances.

        This method is called each period to check if there's a new bond issue
        to layer on. If the par_amounts_line_item has a non-zero value for this
        period, a new amortization schedule is created and added to the tracker.

        Args:
            a (AssumptionValues): Access to assumption values (not currently used).
            li (LineItemValues): Access to line item values for checking par amounts.
            t (int): Current period being processed.
        """
        # Check if we're being called out of order (shouldn't happen in normal flow)
        if self._last_period is not None and t < self._last_period:
            # If going backwards, clear state and rebuild
            self._schedules = {}

        self._last_period = t

        # Look up par amount for this period
        try:
            par_amount = getattr(li, self.par_amounts_line_item)[t]
        except (KeyError, AttributeError):
            # Line item doesn't exist or period not calculated yet
            # This can happen during dependency resolution - just skip
            return

        # If there's a non-zero par amount, add a new bond issue
        if par_amount and par_amount > 0:
            self._add_bond_issue(par_amount, t)

    def _calculate_annual_payment(self, par: float, rate: float, term: int) -> float:
        """
        Calculate the level annual payment for a bond.

        Uses the standard annuity formula for constant payments:
        Payment = P * (r * (1 + r)^n) / ((1 + r)^n - 1)

        Args:
            par (float): Principal amount (par value of the bond).
            rate (float): Annual interest rate.
            term (int): Term in years.

        Returns:
            float: Annual payment amount (principal + interest).
        """
        if rate == 0:
            # If interest rate is zero, just amortize evenly
            return par / term

        # Standard annuity formula
        numerator = rate * ((1 + rate) ** term)
        denominator = ((1 + rate) ** term) - 1
        return par * (numerator / denominator)

    def _add_bond_issue(self, par: float, issue_year: int) -> None:
        """
        Create amortization schedule for a new bond issue.

        Generates a complete amortization schedule with principal, interest,
        and outstanding balance for each year of the bond's life.

        Args:
            par (float): Par amount of the bond.
            issue_year (int): Year the bond is issued.
        """
        # Calculate level annual payment
        annual_payment = self._calculate_annual_payment(par, self.interest_rate, self.term)

        # Build amortization schedule
        schedule = {}
        balance = par

        for year_offset in range(self.term):
            period = issue_year + year_offset
            interest = balance * self.interest_rate
            principal = annual_payment - interest

            # Handle final payment rounding
            if year_offset == self.term - 1:
                principal = balance

            schedule[period] = {
                "principal": principal,
                "interest": interest,
                "balance": balance,
            }

            balance -= principal

        # Store the schedule
        self._schedules[issue_year] = schedule

    def get_principal(self, period: int) -> float:
        """
        Get total principal payment for a specific period.

        Sums principal payments from all active bonds in the given period.

        Args:
            period (int): The period to get principal for.

        Returns:
            float: Total principal payment across all active bonds.
        """
        total = 0.0
        for schedule in self._schedules.values():
            if period in schedule:
                total += schedule[period]["principal"]
        return total

    def get_interest(self, period: int) -> float:
        """
        Get total interest payment for a specific period.

        Sums interest payments from all active bonds in the given period.

        Args:
            period (int): The period to get interest for.

        Returns:
            float: Total interest payment across all active bonds.
        """
        total = 0.0
        for schedule in self._schedules.values():
            if period in schedule:
                total += schedule[period]["interest"]
        return total

    def get_outstanding_balance(self, period: int) -> float:
        """
        Get total outstanding balance for a specific period.

        Sums outstanding balances from all active bonds at the end of the period.

        Args:
            period (int): The period to get balance for.

        Returns:
            float: Total outstanding balance across all active bonds.
        """
        total = 0.0
        for issue_year, schedule in self._schedules.items():
            if period in schedule:
                # Balance at end of period after principal payment
                total += schedule[period]["balance"] - schedule[period]["principal"]
        return total


class DebtBase(LineItem):
    """
    Abstract base class for debt line items.

    DebtBase provides shared functionality for DebtPrincipalLine and
    DebtInterestLine. It handles the eval() pattern similar to FormulaLine,
    calling the shared DebtCalculator to process periods.

    This class should not be instantiated directly. Use DebtPrincipalLine
    or DebtInterestLine instead, or use the create_debt_lines() factory.

    Attributes:
        calculator (DebtCalculator): Shared calculator for debt schedules.
        label (str, optional): Human-readable label for display.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def __init__(
        self,
        calculator: DebtCalculator,
        label: str | None = None,
        tags: list[str] | None = None,
    ):
        """
        Initialize a DebtBase line item.

        Args:
            calculator (DebtCalculator): Shared calculator managing debt schedules.
            label (str, optional): Human-readable label. Defaults to None.
            tags (list[str], optional): List of tags for categorizing the line item.
                Defaults to None (empty list).
        """
        super().__init__(label=label, tags=tags)
        self.calculator = calculator

    def eval(
        self,
        a: "AssumptionValues",
        li: "LineItemValues",
        t: int,
    ) -> float:
        """
        Evaluate the debt line for a specific period.

        This method calls the calculator's eval() to process the period and
        potentially layer on new bond issues, then returns the appropriate
        value (principal or interest) by calling the abstract _get_value() method.

        Args:
            a (AssumptionValues): Access to assumption values.
            li (LineItemValues): Access to line item values.
            t (int): Current period being calculated.

        Returns:
            float: Principal or interest value for the period.
        """
        # Let calculator process this period
        self.calculator.eval(a, li, t)

        # Return the appropriate value (principal or interest)
        return self._get_value(t)

    @abstractmethod
    def _get_value(self, period: int) -> float:
        """
        Get the specific value (principal or interest) for a period.

        This abstract method must be implemented by subclasses to return
        either principal or interest as appropriate.

        Args:
            period (int): The period to get the value for.

        Returns:
            float: The value for this line item type.
        """
        pass

    def get_value(self, period: int) -> float | None:
        """
        Get the value for a specific period.

        This method is called by the calculation engine. It returns None
        to indicate that the value should be calculated via eval().

        Args:
            period (int): The period to get the value for.

        Returns:
            float | None: Always returns None to trigger formula evaluation.
        """
        # Return None so calculation engine calls eval()
        return None


class DebtPrincipalLine(DebtBase):
    """
    Line item for principal payments from bond debt service.

    DebtPrincipalLine returns the total principal payment across all active
    bonds for each period. It shares a DebtCalculator with its corresponding
    DebtInterestLine to ensure consistent debt schedules.

    Example:
        >>> principal, interest = create_debt_lines(
        ...     par_amounts_line_item='bond_proceeds',
        ...     interest_rate=0.05,
        ...     term=10
        ... )
        >>> class MyModel(ProformaModel):
        ...     bond_proceeds = FixedLine(values={2024: 1_000_000})
        ...     principal_payment = principal
        ...     interest_expense = interest

    Attributes:
        calculator (DebtCalculator): Shared calculator for debt schedules.
        label (str, optional): Human-readable label for display.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def _get_value(self, period: int) -> float:
        """
        Get principal payment for the specified period.

        Args:
            period (int): The period to get principal for.

        Returns:
            float: Total principal payment across all active bonds.
        """
        return self.calculator.get_principal(period)

    def __repr__(self):
        """Return a string representation of the DebtPrincipalLine."""
        parts = [
            f"par_amounts_line_item={self.calculator.par_amounts_line_item!r}",
            f"interest_rate={self.calculator.interest_rate}",
            f"term={self.calculator.term}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtPrincipalLine({', '.join(parts)})"


class DebtInterestLine(DebtBase):
    """
    Line item for interest payments from bond debt service.

    DebtInterestLine returns the total interest payment across all active
    bonds for each period. It shares a DebtCalculator with its corresponding
    DebtPrincipalLine to ensure consistent debt schedules.

    Example:
        >>> principal, interest = create_debt_lines(
        ...     par_amounts_line_item='bond_proceeds',
        ...     interest_rate=0.05,
        ...     term=10
        ... )
        >>> class MyModel(ProformaModel):
        ...     bond_proceeds = FixedLine(values={2024: 1_000_000})
        ...     principal_payment = principal
        ...     interest_expense = interest

    Attributes:
        calculator (DebtCalculator): Shared calculator for debt schedules.
        label (str, optional): Human-readable label for display.
        tags (list[str]): List of tags for categorizing the line item.
    """

    def _get_value(self, period: int) -> float:
        """
        Get interest payment for the specified period.

        Args:
            period (int): The period to get interest for.

        Returns:
            float: Total interest payment across all active bonds.
        """
        return self.calculator.get_interest(period)

    def __repr__(self):
        """Return a string representation of the DebtInterestLine."""
        parts = [
            f"par_amounts_line_item={self.calculator.par_amounts_line_item!r}",
            f"interest_rate={self.calculator.interest_rate}",
            f"term={self.calculator.term}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtInterestLine({', '.join(parts)})"


def create_debt_lines(
    par_amounts_line_item: str,
    interest_rate: float,
    term: int,
    principal_label: str | None = None,
    interest_label: str | None = None,
    tags: list[str] | None = None,
) -> tuple[DebtPrincipalLine, DebtInterestLine]:
    """
    Factory function to create matched principal and interest debt lines.

    This is the recommended way to create debt line items, as it ensures that
    both principal and interest share the same DebtCalculator instance and
    therefore have consistent debt schedules.

    Args:
        par_amounts_line_item (str): Name of the line item containing par amounts
            for new bond issuances. When this line item has a non-zero value
            for a period, a new bond is issued.
        interest_rate (float): Annual interest rate for all bonds (e.g., 0.05 for 5%).
        term (int): Term in years for bond amortization.
        principal_label (str, optional): Label for the principal line item.
            Defaults to None.
        interest_label (str, optional): Label for the interest line item.
            Defaults to None.
        tags (list[str], optional): Tags to apply to both line items.
            Defaults to None (empty list).

    Returns:
        tuple[DebtPrincipalLine, DebtInterestLine]: Matched principal and interest
            line items sharing the same calculator.

    Example:
        >>> principal, interest = create_debt_lines(
        ...     par_amounts_line_item='bond_proceeds',
        ...     interest_rate=0.05,
        ...     term=10,
        ...     principal_label='Principal Payment',
        ...     interest_label='Interest Expense',
        ...     tags=['debt_service']
        ... )
        >>>
        >>> class MyModel(ProformaModel):
        ...     bond_proceeds = FixedLine(values={2024: 1_000_000, 2026: 500_000})
        ...     principal_payment = principal
        ...     interest_expense = interest
        ...     total_debt_service = FormulaLine(
        ...         formula=lambda a, li, t: li.tag["debt_service"][t]
        ...     )
    """
    # Create shared calculator
    calculator = DebtCalculator(
        par_amounts_line_item=par_amounts_line_item,
        interest_rate=interest_rate,
        term=term,
    )

    # Create line items sharing the calculator
    principal = DebtPrincipalLine(
        calculator=calculator,
        label=principal_label,
        tags=tags,
    )

    interest = DebtInterestLine(
        calculator=calculator,
        label=interest_label,
        tags=tags,
    )

    return principal, interest
