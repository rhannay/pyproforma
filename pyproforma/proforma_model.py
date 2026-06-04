"""
Base class for ProForma models.

Users define models by subclassing ProformaModel and declaring line items as
class attributes using FixedLine, FormulaLine, or InputLine.
"""

from pyproforma.calculation_engine import calculate_line_items
from pyproforma.line_items.fixed_line import FixedLine
from pyproforma.line_items.input_line import InputLine
from pyproforma.line_items.line_item import LineItem
from pyproforma.line_items.line_item_result import LineItemResult
from pyproforma.line_items.line_item_selection import LineItemSelection
from pyproforma.line_items.line_item_values import LineItemValues
from pyproforma.charts import Charts
from pyproforma.reserved_words import validate_name
from pyproforma.tables import Tables
from pyproforma.tags_namespace import ModelTagNamespace


class ProformaModel:
    period_label: str = ""
    """
    Base class for user-defined financial models.

    Subclass and declare line items as class attributes. Periods are supplied
    at instantiation. InputLine values and scalar InputLine constants are
    supplied as keyword arguments.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     tax_rate = FixedLine(value=0.21)
        ...     revenue  = FixedLine(values={2024: 100, 2025: 110})
        ...     profit   = FormulaLine(lambda li, t: li.revenue[t] * (1 - li.tax_rate))
        ...
        >>> model = MyModel(periods=[2024, 2025])
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        line_item_names = []
        input_line_names = []

        for name, value in cls.__dict__.items():
            if isinstance(value, LineItem):
                validate_name(name)
                line_item_names.append(name)
                if isinstance(value, InputLine):
                    input_line_names.append(name)

        cls._line_item_names = line_item_names
        cls._input_line_names = input_line_names

    def __init__(self, periods: list[int] | None = None, **kwargs):
        """
        Initialize a ProformaModel instance.

        Args:
            periods: List of periods (typically years) for the model.
            **kwargs: Values for InputLine fields. Period-indexed InputLines
                expect a dict; scalar InputLines expect a float/int.

        Raises:
            TypeError: If unknown kwargs or missing required inputs.
        """
        if periods is None:
            periods = getattr(self.__class__, "default_periods", [])
        self.periods = list(periods)
        self.line_item_names = self.__class__._line_item_names
        input_line_names = self.__class__._input_line_names

        unknown = set(kwargs) - set(input_line_names)
        if unknown:
            valid_str = ", ".join(sorted(input_line_names)) or "none"
            raise TypeError(
                f"{self.__class__.__name__} received unexpected keyword arguments: "
                f"{', '.join(sorted(unknown))}. "
                f"Valid inputs: {valid_str}"
            )

        # Resolve InputLine values; scalars go into _scalars, dicts into _input_line_values
        self._scalars: dict[str, float] = {}
        self._input_line_values: dict[str, dict[int, float]] = {}
        missing = []

        for name in input_line_names:
            attr = getattr(self.__class__, name)
            if name in kwargs:
                raw = kwargs[name]
            elif attr.has_default:
                raw = attr.default
            else:
                missing.append(name)
                continue

            if isinstance(raw, (int, float)):
                self._scalars[name] = float(raw)
                # Also expand into period dict so the engine can store it in _li
                self._input_line_values[name] = {p: float(raw) for p in self.periods}
            else:
                self._input_line_values[name] = raw

        if missing:
            raise TypeError(
                f"{self.__class__.__name__} requires values for: "
                f"{', '.join(missing)}"
            )

        # Collect scalar FixedLine values into _scalars
        for name in self.line_item_names:
            attr = getattr(self.__class__, name)
            if isinstance(attr, FixedLine) and attr.is_scalar:
                self._scalars[name] = float(attr._scalar_value)

        # Run the calculation engine
        if self.periods:
            self._li = calculate_line_items(self, self._scalars, self.periods)
        else:
            self._li = LineItemValues(periods=[])

        self.tables: Tables = Tables(self)
        self.charts: Charts = Charts(self)
        self._tag_namespace = ModelTagNamespace(self)

    def get_value(self, name: str, period: int) -> float:
        line_item = getattr(self._li, name)
        return line_item[period]

    @property
    def li(self) -> LineItemValues:
        return self._li

    @property
    def tags(self) -> list[str]:
        all_tags = set()
        for name in self.line_item_names:
            spec = getattr(self.__class__, name)
            if hasattr(spec, "tags"):
                all_tags.update(spec.tags)
        return sorted(all_tags)

    @property
    def tag(self) -> ModelTagNamespace:
        return self._tag_namespace

    def select(self, names: list[str]) -> LineItemSelection:
        return LineItemSelection(self, names)

    def __getitem__(self, name: str) -> LineItemResult:
        if not isinstance(name, str):
            raise TypeError(f"Expected string for item name, got {type(name).__name__}")
        if name in self.line_item_names:
            return LineItemResult(self, name)
        raise AttributeError(
            f"Item '{name}' not found in model. "
            f"Available line items: {', '.join(sorted(self.line_item_names))}"
        )

    def dependents(self, name: str) -> list[str]:
        """Return names of line items whose formulas directly reference the given name.

        Args:
            name: A line item name to find dependents for.

        Returns:
            List of line item names that directly reference this item in their formula.

        Examples:
            >>> model.dependents("revenue")
            ['expenses', 'profit']
        """
        from pyproforma.line_items.formula_line import FormulaLine
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
            f"line_items={len(self.line_item_names)})"
        )
