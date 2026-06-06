"""
Debt line items for bond principal and interest payments.

Provides line items for tracking bond debt service across multiple issuances,
using level annual debt service amortization.

Example:
    >>> class MyModel(ProformaModel):
    ...     bond_par  = FixedLine(values={2024: 1_000_000, 2026: 500_000})
    ...     bond_rate = ScalarLine(value=0.05, label="Bond Rate")
    ...     bond_term = ScalarLine(value=10,   label="Bond Term")
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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.engine.model_namespace import ModelNamespace


@dataclass
class DebtConfig:
    """
    Declarative config for a debt line pair — class-level, no mutable state.

    Holds the names of the three model items needed to compute debt service.
    Both DebtPrincipalLine and DebtInterestLine in a pair reference the same
    DebtConfig instance, so ProformaModel.__init__ can group them and create
    one fresh DebtCalculator per pair per model instance.
    """
    par_amounts: str
    interest_rate: str
    term: str


class DebtCalculator:
    """
    Per-instance stateful calculator for bond debt schedules across multiple issuances.

    Created fresh for each model instance by ProformaModel.__init__ — never shared
    across instances. Reads interest rate and term from the model namespace at
    calculation time, so they can be varied via ScalarInputLine for scenario analysis.

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

    def eval(self, ns: "ModelNamespace", t: int) -> None:
        """Process a period, detecting new issuances and building schedules."""
        rate = getattr(ns, self.interest_rate)
        term = int(getattr(ns, self.term))

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
        config: DebtConfig,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=tags, value_format=value_format)
        self.config = config

    def eval(self, ns: "ModelNamespace", t: int, calculator: DebtCalculator) -> float:
        calculator.eval(ns, t)
        return self._get_value(calculator, t)

    @abstractmethod
    def _get_value(self, calculator: DebtCalculator, period: int) -> float:
        pass

    def get_value(self, period: int) -> float | None:
        return None


class DebtPrincipalLine(DebtBase):
    """Line item returning total principal payments across all active bond issues."""

    def _get_value(self, calculator: DebtCalculator, period: int) -> float:
        return calculator.get_principal(period)

    def __repr__(self):
        parts = [
            f"par_amounts={self.config.par_amounts!r}",
            f"interest_rate={self.config.interest_rate!r}",
            f"term={self.config.term!r}",
        ]
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"DebtPrincipalLine({', '.join(parts)})"


class DebtInterestLine(DebtBase):
    """Line item returning total interest payments across all active bond issues."""

    def _get_value(self, calculator: DebtCalculator, period: int) -> float:
        return calculator.get_interest(period)

    def __repr__(self):
        parts = [
            f"par_amounts={self.config.par_amounts!r}",
            f"interest_rate={self.config.interest_rate!r}",
            f"term={self.config.term!r}",
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
    line items must be defined on the same model — typically ScalarLine(value=...)
    for rate and term, and FixedLine(values={...}) or ScalarInputLine for par amounts.

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
        tuple[DebtPrincipalLine, DebtInterestLine]: Matched pair sharing one DebtConfig.

    Example:
        >>> class MyModel(ProformaModel):
        ...     bond_par  = FixedLine(values={2024: 0, 2025: 10_000_000})
        ...     bond_rate = ScalarInputLine(default=0.045, label="Bond Rate")
        ...     bond_term = ScalarLine(value=20, label="Bond Term")
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
                f"Define a ScalarLine or ScalarInputLine for this value and pass its name."
            )

    config = DebtConfig(
        par_amounts=par_amounts,
        interest_rate=interest_rate,
        term=term,
    )

    principal = DebtPrincipalLine(
        config=config,
        label=principal_label,
        tags=tags,
        value_format=principal_value_format,
    )

    interest = DebtInterestLine(
        config=config,
        label=interest_label,
        tags=tags,
        value_format=interest_value_format,
    )

    return principal, interest
