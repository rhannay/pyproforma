"""
Base class for ProForma models in v2 API.

The ProformaModel class is inspired by Pydantic's design pattern where class attributes
become model fields. Users define models by subclassing ProformaModel and declaring
line items as class attributes using FixedLine, FormulaLine, or Assumption.
"""

from pyproforma.v2.assumption import Assumption
from pyproforma.v2.assumption_result import AssumptionResult
from pyproforma.v2.assumption_values import AssumptionValues
from pyproforma.v2.calculation_engine import calculate_line_items
from pyproforma.v2.line_items.line_item import LineItem
from pyproforma.v2.line_items.line_item_result import LineItemResult
from pyproforma.v2.line_items.line_item_selection import LineItemSelection
from pyproforma.v2.line_items.line_item_values import LineItemValues
from pyproforma.v2.reserved_words import validate_name
from pyproforma.v2.tables import Tables
from pyproforma.v2.tags_namespace import ModelTagNamespace


class ProformaModel:
    """
    Base class for user-defined financial models.

    ProformaModel provides a Pydantic-inspired interface for defining financial models.
    Users subclass ProformaModel and declare line items as class attributes. Each line
    item can be a FixedLine (with explicit period values), FormulaLine (with calculation
    logic), or Assumption (simple value).

    The class automatically discovers all line items declared as class attributes and
    manages the model structure. Periods (years) are defined when creating model instances.

    Examples:
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100, 2025: 110})
        ...     expenses = FormulaLine(formula=lambda: revenue * 0.6)
        ...     profit = FormulaLine(formula=lambda: revenue - expenses)
        ...
        >>> model = MyModel(periods=[2024, 2025])

    Attributes:
        periods (list[int]): List of periods (typically years) for the model.
    """

    def __init_subclass__(cls, **kwargs):
        """
        Called when a subclass is created.

        This method automatically discovers and stores the names of all Assumption
        and LineItem attributes defined on the subclass. It also validates that
        no reserved words are used as line item or assumption names.

        Args:
            **kwargs: Additional keyword arguments passed to super().__init_subclass__

        Raises:
            ValueError: If any line item or assumption name is a reserved word
        """
        super().__init_subclass__(**kwargs)

        # Discover assumption names from class attributes
        assumption_names = []
        line_item_names = []

        for name, value in cls.__dict__.items():
            if isinstance(value, Assumption):
                # Validate name is not reserved
                validate_name(name)
                assumption_names.append(name)
            elif isinstance(value, LineItem):
                # Validate name is not reserved
                validate_name(name)
                line_item_names.append(name)

        # Store as class attributes
        cls._assumption_names = assumption_names
        cls._line_item_names = line_item_names

    def __init__(self, periods: list[int] | None = None):
        """
        Initialize a ProformaModel instance.

        Args:
            periods (list[int], optional): List of periods (years) for the model.
                Defaults to None.
        """
        self.periods = periods or []

        # Store instance copies of discovered names
        self.line_item_names = self.__class__._line_item_names
        self.assumption_names = self.__class__._assumption_names

        # Initialize assumption values
        self.av = self._initialize_assumptions()

        # Calculate line item values
        if self.periods:
            self._li = calculate_line_items(self, self.av, self.periods)
        else:
            self._li = LineItemValues(periods=[])

        # Initialize tables namespace
        self.tables = Tables(self)

        # Initialize tag namespace
        self._tag_namespace = ModelTagNamespace(self)

    def _initialize_assumptions(self) -> AssumptionValues:
        """
        Initialize assumption values from class attributes.

        Returns:
            AssumptionValues: Container with all assumption values.
        """
        assumption_values = {}

        # Extract values from each assumption
        for name in self.assumption_names:
            assumption = getattr(self.__class__, name)
            if isinstance(assumption, Assumption):
                assumption_values[name] = assumption.value

        return AssumptionValues(assumption_values)

    def get_value(self, name: str, period: int) -> float:
        """
        Get the calculated value for a line item at a specific period.

        Args:
            name (str): The name of the line item.
            period (int): The period to get the value for.

        Returns:
            float: The calculated value.

        Raises:
            AttributeError: If the line item name doesn't exist.
            KeyError: If the period hasn't been calculated.
        """
        # Use attribute access which raises proper errors
        line_item = getattr(
            self._li, name
        )  # Raises AttributeError if name doesn't exist
        return line_item[period]  # Raises KeyError if period doesn't exist

    @property
    def li(self) -> LineItemValues:
        """
        Access line item values.

        Returns:
            LineItemValues: Container with all calculated line item values.

        Examples:
            >>> model.li.revenue[2024]
            100000
        """
        return self._li

    @property
    def tags(self) -> list[str]:
        """
        Get all unique tags used across line items.

        Returns:
            list[str]: Sorted list of unique tag strings.

        Examples:
            >>> model.tags
            ['expense', 'income', 'operating']
        """
        all_tags = set()
        for name in self.line_item_names:
            line_item_spec = getattr(self.__class__, name)
            if hasattr(line_item_spec, "tags"):
                all_tags.update(line_item_spec.tags)
        return sorted(all_tags)

    @property
    def tag(self) -> ModelTagNamespace:
        """
        Access line items by tags.

        Returns:
            ModelTagNamespace: Namespace for selecting line items by their tags.

        Examples:
            >>> income_selection = model.tag["income"]
            >>> income_selection.names
            ['revenue', 'interest']
        """
        return self._tag_namespace

    def select(self, names: list[str]) -> LineItemSelection:
        """
        Create a selection of specific line items.

        Args:
            names: List of line item names to include in the selection.

        Returns:
            LineItemSelection: Selection object containing the specified line items.

        Raises:
            ValueError: If any name is not a valid line item in the model.

        Examples:
            >>> selection = model.select(['revenue', 'expenses', 'profit'])
            >>> selection.names
            ['revenue', 'expenses', 'profit']
        """
        return LineItemSelection(self, names)

    def __getitem__(self, name: str) -> LineItemResult | AssumptionResult:
        """
        Get LineItemResult or AssumptionResult using dictionary-style access.

        This enables convenient access to line items and assumptions using subscript
        notation. Returns a LineItemResult for line items or an AssumptionResult for
        assumptions, providing read-only access to values and metadata.

        Args:
            name (str): The name of the line item or assumption

        Returns:
            LineItemResult | AssumptionResult: Results object for the specified item

        Raises:
            TypeError: If name is not a string
            AttributeError: If the name doesn't exist in line items or assumptions

        Examples:
            >>> revenue = model['revenue']  # LineItemResult
            >>> revenue[2024]
            100000
            >>> inflation = model['inflation_rate']  # AssumptionResult
            >>> inflation.value
            0.03
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected string for item name, got {type(name).__name__}")

        # Check if it's a line item
        if name in self.line_item_names:
            return LineItemResult(self, name)

        # Check if it's an assumption
        if name in self.assumption_names:
            return AssumptionResult(self, name)

        # Not found in either - raise descriptive error
        raise AttributeError(
            f"Item '{name}' not found in model. "
            f"Available line items: {', '.join(sorted(self.line_item_names))}. "
            f"Available assumptions: {', '.join(sorted(self.assumption_names))}"
        )

    def __repr__(self):
        """Return a string representation of the model."""
        line_item_count = len(self.line_item_names)
        return (
            f"{self.__class__.__name__}("
            f"periods={self.periods}, "
            f"line_items={line_item_count})"
        )
