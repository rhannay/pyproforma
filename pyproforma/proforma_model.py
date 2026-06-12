"""
Base class for ProForma models.

Users define models by subclassing ProformaModel and declaring line items as
class attributes using FixedLine, FormulaLine, InputLine, ScalarLine, or
ScalarInputLine.
"""

from typing import Any

from pyproforma.charts import Charts
from pyproforma.engine.calculation_engine import calculate_line_items
from pyproforma.engine.line_item_values import LineItemValues
from pyproforma.reserved_words import validate_name
from pyproforma.results.line_item_result import LineItemResult
from pyproforma.results.line_item_selection import LineItemSelection
from pyproforma.results.scalar_result import ScalarResult
from pyproforma.results.tags_namespace import TagNamespace
from pyproforma.specs.debt_line import DebtBase, DebtCalculator
from pyproforma.specs.input_line import InputLine
from pyproforma.specs.line_item import LineItem
from pyproforma.specs.scalar_input_line import ScalarInputLine
from pyproforma.specs.scalar_line import ScalarLine
from pyproforma.tables import Tables


class ProformaModel:
    """
    Base class for user-defined financial models.

    Subclass and declare line items as class attributes. Periods are supplied
    at instantiation. InputLine and ScalarInputLine values are supplied as
    keyword arguments.

    Class attributes:
        default_periods (list[int]): Optional. Periods used when none are passed to
            ``__init__``. Declare on the subclass to make ``periods`` optional at
            instantiation.
        period_label (str): Optional display label for the period column in tables
            (e.g. ``"Fiscal Year"``). Defaults to ``""``.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     default_periods = [2024, 2025, 2026]
        ...     tax_rate = ScalarLine(value=0.21)
        ...     revenue  = FixedLine(values={2024: 100, 2025: 110, 2026: 120})
        ...     profit   = FormulaLine(lambda li, t: li.revenue[t] * (1 - li.tax_rate))
        ...
        >>> model = MyModel()              # uses default_periods
        >>> model = MyModel(periods=[2024, 2025])  # override
        >>> model.revenue[2024]   # dot notation — primary API
        100
        >>> model["revenue"][2024]  # bracket notation — for dynamic/programmatic access
        100
    """

    period_label: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        line_item_names = []
        scalar_names = []
        input_line_names = []
        scalar_input_names = []

        for name, value in cls.__dict__.items():
            if isinstance(value, LineItem):
                validate_name(name)
                if value._is_scalar:
                    scalar_names.append(name)
                    if isinstance(value, ScalarInputLine):
                        scalar_input_names.append(name)
                else:
                    line_item_names.append(name)
                    if isinstance(value, InputLine):
                        input_line_names.append(name)

        cls._line_item_names = line_item_names
        cls._scalar_names = scalar_names
        cls._input_line_names = input_line_names
        cls._scalar_input_names = scalar_input_names

    def __init__(self, periods: list[int] | None = None, **kwargs):
        """
        Initialize a ProformaModel instance.

        Args:
            periods: List of periods (typically years) for the model. If ``None``,
                falls back to ``default_periods`` defined on the subclass. Raises no
                error if both are absent — the model simply has no periods.
            **kwargs: Values for ``InputLine`` and ``ScalarInputLine`` fields declared
                on the subclass. Period-indexed inputs are passed as
                ``{period: value}`` dicts; scalar inputs as plain floats.

        Raises:
            TypeError: If unknown kwargs are supplied or required inputs are missing.
            ValueError: If a kwarg attempts to override a locked period (``values=``
                or ``None`` in ``default``).
        """
        if periods is None:
            periods = getattr(self.__class__, "default_periods", [])
        self.periods = list(periods)
        self.line_item_names = self.__class__._line_item_names
        self.scalar_names = self.__class__._scalar_names

        all_input_names = self.__class__._input_line_names + self.__class__._scalar_input_names
        unknown = set(kwargs) - set(all_input_names)
        if unknown:
            valid_str = ", ".join(sorted(all_input_names)) or "none"
            raise TypeError(
                f"{self.__class__.__name__} received unexpected keyword arguments: "
                f"{', '.join(sorted(unknown))}. "
                f"Valid inputs: {valid_str}"
            )

        self._scalars: dict[str, float] = {}
        self._input_line_values: dict[str, dict[int, float]] = {}
        missing = []

        # Resolve ScalarInputLine values → _scalars
        for name in self.__class__._scalar_input_names:
            attr = getattr(self.__class__, name)
            if name in kwargs:
                self._scalars[name] = kwargs[name]
            elif attr.has_default:
                self._scalars[name] = attr.default
            else:
                missing.append(name)

        # Resolve period-indexed InputLine values → _input_line_values
        for name in self.__class__._input_line_names:
            attr = getattr(self.__class__, name)
            locked_vals = attr.locked_values  # {period: value} — cannot be overridden
            none_periods = (
                {p for p, v in attr.default.items() if v is None}
                if attr.has_default else set()
            )
            if name in kwargs:
                provided = kwargs[name]
                # Reject attempts to override values-locked periods
                bad_locked = sorted(p for p, v in provided.items() if p in locked_vals)
                if bad_locked:
                    raise ValueError(
                        f"'{name}' period(s) {bad_locked} are locked via values= "
                        f"and cannot be overridden."
                    )
                # Reject attempts to set None-locked periods to a real value
                bad_none = sorted(p for p, v in provided.items()
                                  if p in none_periods and v is not None)
                if bad_none:
                    raise ValueError(
                        f"'{name}' period(s) {bad_none} are locked (None in the model spec) "
                        f"and cannot be overridden."
                    )
                # Auto-fill locked periods so callers don't need to include them
                merged = {**provided, **{p: None for p in none_periods if p not in provided}}
            elif attr.has_default:
                merged = dict(attr.default)
            elif attr.locked_values:
                merged = {}  # locked_values applied below is sufficient
            else:
                missing.append(name)
                continue
            # Always apply values-locked periods on top (they supersede everything)
            merged.update(locked_vals)
            self._input_line_values[name] = merged

        if missing:
            raise TypeError(
                f"{self.__class__.__name__} requires values for: "
                f"{', '.join(missing)}"
            )

        # Collect ScalarLine values → _scalars
        for name in self.__class__._scalar_names:
            attr = getattr(self.__class__, name)
            if isinstance(attr, ScalarLine):
                self._scalars[name] = float(attr.value)

        # Build per-instance debt calculators, one per DebtConfig (i.e. per pair)
        self._debt_calculators: dict[int, DebtCalculator] = {}
        for name in self.line_item_names:
            spec = getattr(self.__class__, name)
            if isinstance(spec, DebtBase):
                config_id = id(spec.config)
                if config_id not in self._debt_calculators:
                    self._debt_calculators[config_id] = DebtCalculator(
                        par_amounts=spec.config.par_amounts,
                        interest_rate=spec.config.interest_rate,
                        term=spec.config.term,
                    )

        # Run the calculation engine
        if self.periods:
            self._li = calculate_line_items(self, self._scalars, self.periods)
        else:
            self._li = LineItemValues(periods=[])

        self.tables: Tables = Tables(self)
        self.charts: Charts = Charts(self)
        self._tag_namespace = TagNamespace(self)

    def get_value(self, name: str, period: int) -> Any:
        if name in self.scalar_names:
            return self._scalars[name]
        line_item = getattr(self._li, name)
        return line_item[period]

    @property
    def tags(self) -> list[str]:
        all_tags = set()
        for name in self.line_item_names:
            spec = getattr(self.__class__, name)
            if hasattr(spec, "tags"):
                all_tags.update(spec.tags)
        return sorted(all_tags)

    @property
    def tag(self) -> TagNamespace:
        return self._tag_namespace

    def select(self, names: list[str]) -> LineItemSelection:
        return LineItemSelection(self, names)

    def __getitem__(self, name: str):
        if not isinstance(name, str):
            raise TypeError(f"Expected string for item name, got {type(name).__name__}")
        if name in self.line_item_names:
            return LineItemResult(self, name)
        if name in self.scalar_names:
            return ScalarResult(self, name)
        raise AttributeError(
            f"Item '{name}' not found in model. "
            f"Available line items: {', '.join(sorted(self.line_item_names))}. "
            f"Available scalars: {', '.join(sorted(self.scalar_names))}"
        )

    def dependents(self, name: str) -> list[str]:
        """Return names of line items whose formulas directly reference the given name."""
        from pyproforma.specs.formula_line import FormulaLine
        return [
            n for n in self.line_item_names
            if n != name
            and isinstance(getattr(self.__class__, n), FormulaLine)
            and name in (getattr(self.__class__, n).precedents or [])
        ]

    def compare(self, *others, labels=None):
        from pyproforma.compare import ModelComparison
        return ModelComparison(self, *others, labels=labels)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"periods={self.periods}, "
            f"line_items={len(self.line_item_names)}, "
            f"scalars={len(self.scalar_names)})"
        )
