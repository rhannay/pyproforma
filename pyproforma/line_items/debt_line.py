"""
Debt line items for bond principal and interest payments.

Provides line items for tracking bond debt service across multiple issuances,
using level annual debt service amortization.

Example:
    >>> class MyModel(ProformaModel):
    ...     bond_par  = FixedLine(values={2024: 1_000_000, 2026: 500_000})
    ...     bond_rate = FixedLine(value=0.05, label="Bond Rate")
    ...     bond_term = FixedLine(value=10,   label="Bond Term")
    ...
    ...     principal, interest = create_debt_lines(
    ...         par_amounts="bond_par",
    ...         interest_rate="bond_rate",
    ...         term="bond_term",
    ...         principal_label="Principal",
    ...         interest_label="Interest",
    ...     )
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.model_namespace import ModelNamespace


class DebtCalculator:
    """
    Stateful calculator for bond debt schedules across multiple issuances.

    Reads interest rate and term from scalar line items in the model namespace
    at calculation time, so they can be varied via InputLine for scenario analysis.

    Attributes:
        par_amounts (str): Name of the line item containing par amounts per period.
        interest_rate (str): Name of the scalar line item with the annual interest rate.
        term (str): Name of the scalar line item with the term in years.
    """

    def __init__(self, par_amounts: str, interest_rate: str, term: str):
        self.par_amounts = par_amounts
        self.interest_rate = interest_rate
        self.term = term

        self._schedules: dict[int, dict[int, dict[str, float]]] = {}
        self._last_period: int | None = None
        self._cached_rate: float | None = None
        self._cached_term: int | None = None

    def eval(self, ns: "ModelNamespace", t: int) -> None:
        """Process a period, detecting new issuances and building schedules."""
        rate = getattr(ns, self.interest_rate)
        term = int(getattr(ns, self.term))

        # Invalidate cache if rate or term changed (e.g. new model instantiation)
        if (rate, term) != (self._cached_rate, self._cached_term):
            self._schedules.clear()
            self._cached_rate = rate
            self._cached_term = term

        # Reset if called out of order (new model calculation)
        if self._last_period is not None and t < self._last_period:
            self._schedules.clear()

        self._last_period = t

        try:
            par_amount = getattr(ns, self.par_amounts)[t]
        except (KeyError, AttributeError):
            return

        if par_amount and par_amount > 0:
            self._add_bond_issue(par_amount, t, rate, term)

    def _calculate_annual_payment(self, par: float, rate: float, term: int) -> float:
        if rate == 0:
            return par / term
        numerator = rate * ((1 + rate) ** term)
        denominator = ((1 + rate) ** term) - 1
        return par * (numerator / denominator)

    def _add_bond_issue(self, par: float, issue_year: int, rate: float, term: int) -> None:
        annual_payment = self._calculate_annual_payment(par, rate, term)
        schedule = {}
        balance = par

        for year_offset in range(term):
            period = issue_year + year_offset
            interest = balance * rate
            principal = annual_payment - interest

            if year_offset == term - 1:
                principal = balance

            schedule[period] = {
                "principal": principal,
                "interest": interest,
                "balance": balance,
            }
            balance -= principal

        self._schedules[issue_year] = schedule

    def get_principal(self, period: int) -> float:
        return sum(
            s[period]["principal"] for s in self._schedules.values() if period in s
        )

    def get_interest(self, period: int) -> float:
        return sum(
            s[period]["interest"] for s in self._schedules.values() if period in s
        )

    def get_outstanding_balance(self, period: int) -> float:
        return sum(
            s[period]["balance"] - s[period]["principal"]
            for s in self._schedules.values()
            if period in s
        )


class DebtBase(LineItem):
    """Abstract base for DebtPrincipalLine and DebtInterestLine."""

    def __init__(
        self,
        calculator: DebtCalculator,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=tags, value_format=value_format)
        self.calculator = calculator

    def eval(self, ns: "ModelNamespace", t: int) -> float:
        self.calculator.eval(ns, t)
        return self._get_value(t)

    @abstractmethod
    def _get_value(self, period: int) -> float:
        pass

    def get_value(self, period: int) -> float | None:
        return None


class DebtPrincipalLine(DebtBase):
    """Line item returning total principal payments across all active bond issues."""

    def _get_value(self, period: int) -> float:
        return self.calculator.get_principal(period)

    def __repr__(self):
        parts = [
            f"par_amounts={self.calculator.par_amounts!r}",
            f"interest_rate={self.calculator.interest_rate!r}",
            f"term={self.calculator.term!r}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtPrincipalLine({', '.join(parts)})"


class DebtInterestLine(DebtBase):
    """Line item returning total interest payments across all active bond issues."""

    def _get_value(self, period: int) -> float:
        return self.calculator.get_interest(period)

    def __repr__(self):
        parts = [
            f"par_amounts={self.calculator.par_amounts!r}",
            f"interest_rate={self.calculator.interest_rate!r}",
            f"term={self.calculator.term!r}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtInterestLine({', '.join(parts)})"


def create_debt_lines(
    par_amounts: str,
    interest_rate: str,
    term: str,
    principal_label: str | None = None,
    interest_label: str | None = None,
    tags: list[str] | None = None,
    principal_value_format: Union[str, NumberFormatSpec, dict, None] = None,
    interest_value_format: Union[str, NumberFormatSpec, dict, None] = None,
) -> tuple[DebtPrincipalLine, DebtInterestLine]:
    """
    Factory function to create matched principal and interest debt line items.

    All three positional arguments are line item names (strings). The referenced
    line items must be defined on the same model — typically FixedLine(value=...)
    for rate and term, and FixedLine(values={...}) or InputLine for par amounts.

    Args:
        par_amounts (str): Name of the line item with par amounts per period.
            A non-zero value in a period triggers a new bond issuance.
        interest_rate (str): Name of a scalar line item with the annual interest rate.
        term (str): Name of a scalar line item with the term in years.
        principal_label: Display label for the principal line item.
        interest_label: Display label for the interest line item.
        tags: Tags applied to both line items.
        principal_value_format: Format for principal values.
        interest_value_format: Format for interest values.

    Returns:
        tuple[DebtPrincipalLine, DebtInterestLine]: Matched pair sharing one calculator.

    Example:
        >>> class MyModel(ProformaModel):
        ...     bond_par  = FixedLine(values={2024: 0, 2025: 10_000_000})
        ...     bond_rate = InputLine(default=0.045, label="Bond Rate")
        ...     bond_term = FixedLine(value=20, label="Bond Term")
        ...
        ...     principal, interest = create_debt_lines(
        ...         par_amounts="bond_par",
        ...         interest_rate="bond_rate",
        ...         term="bond_term",
        ...     )
    """
    for param_name, value in [
        ("par_amounts", par_amounts),
        ("interest_rate", interest_rate),
        ("term", term),
    ]:
        if not isinstance(value, str):
            raise TypeError(
                f"'{param_name}' must be a string (line item name), "
                f"got {type(value).__name__}. "
                f"Define a FixedLine or InputLine for this value and pass its name."
            )

    calculator = DebtCalculator(
        par_amounts=par_amounts,
        interest_rate=interest_rate,
        term=term,
    )

    principal = DebtPrincipalLine(
        calculator=calculator,
        label=principal_label,
        tags=tags,
        value_format=principal_value_format,
    )

    interest = DebtInterestLine(
        calculator=calculator,
        label=interest_label,
        tags=tags,
        value_format=interest_value_format,
    )

    return principal, interest
