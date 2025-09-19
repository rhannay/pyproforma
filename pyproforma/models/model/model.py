import copy
from typing import Union

from pyproforma.charts import Charts
from pyproforma.models.multi_line_item import MultiLineItem

# Namespace imports
from pyproforma.tables import Tables

from ..category import Category
from ..compare import Compare
from ..constraint import Constraint
from ..line_item import LineItem
from ..results import CategoryResults, ConstraintResults, LineItemResults
from .metadata import generate_category_metadata, generate_line_item_metadata
from .model_update import UpdateNamespace
from .serialization import SerializationMixin
from .validations import (
    validate_categories,
    validate_constraints,
    validate_formulas,
    validate_line_items,
    validate_multi_line_items,
    validate_years,
)
from .value_matrix import generate_value_matrix


class Model(SerializationMixin):
    """
    Core financial modeling framework for building pro forma financial statements.

    Creates structured financial models with line items, categories, multi line items,
    and constraints. Supports multi-year modeling, automatic dependency resolution,
    and rich output formatting.

    Args:
        line_items (Union[list[LineItem], list[str], list[dict]], optional):
            LineItem objects defining the model structure. Can be LineItem objects,
            strings (which will be converted to LineItems with those names),
            or dictionaries (which will be used with LineItem.from_dict).
            If None, creates an empty model. Default: None
        years (list[int], optional): Years for the model time horizon.
            If None, defaults to empty list []. Models can be created with
            line items but empty years for template/workflow purposes. Default: None
        categories (list[Category], optional): Category definitions
            (auto-inferred if None)
        constraints (list[Constraint], optional): Validation constraints
        multi_line_items (list[MultiLineItem], optional): Components that generate
            multiple line items

    Examples:
        >>> from pyproforma import Model, LineItem
        >>>
        >>> # Create an empty model
        >>> empty_model = Model()
        >>>
        >>> # Create a model with line items as strings
        >>> model = Model(line_items=["revenue", "expenses"], years=[2023, 2024])
        >>>
        >>> # Create a model with line items as dictionaries
        >>> line_items = [
        ...     {"name": "revenue", "category": "income", "formula": "1000"},
        ...     {"name": "expenses", "category": "costs", "formula": "revenue * 0.8"}
        ... ]
        >>> model = Model(line_items=line_items, years=[2023, 2024])
        >>>
        >>> # Create a model with mixed line item types
        >>> revenue = LineItem(name="revenue", category="income", formula="1000")
        >>> model = Model(
        ...     line_items=[revenue, {"name": "expenses", "formula": "800"}, "profit"],
        ...     years=[2023, 2024]
        ... )
        >>>
        >>> # Access values
        >>> model.value("revenue", 2023)  # 1000
        >>> model["expenses", 2024]  # 800
        >>>
        >>> # Analysis
        >>> model.category("income").total()  # Category totals by year
        >>> model.line_item("revenue").to_series()  # Pandas Series
        >>> model.line_item("revenue").percent_change(2024)  # Growth rates
        >>>
        >>> # Output
        >>> model.tables.financial_statement()  # Formatted tables
        >>> model.charts.line_chart(["revenue", "expenses"])  # Charts
        >>>
        >>> # Scenario analysis
        >>> scenario = model.scenario([("revenue", {"updated_values": {2023: 1200}})])
        >>> scenario["revenue", 2023]  # 1200 in scenario, original unchanged

    Key Methods:
        - value(name, year): Get value for any item/year
        - category(name)/line_item(name): Get analysis objects
        - line_item(name).percent_change(), .index_to_year(): Calculate metrics
        - scenario(item_updates): Create what-if scenarios
        - copy(): Create independent model copies
        - summary(): Model structure overview
        - tables/charts: Rich output generation
        - update.years(): Update years through the update namespace
    """

    # ============================================================================
    # INITIALIZATION & SETUP
    # ============================================================================

    def __init__(
        self,
        line_items: Union[list[LineItem], list[str], list[dict]] = None,
        years: list[int] = None,
        categories: Union[list[Category], list[str]] = None,
        constraints: list[Constraint] = None,
        multi_line_items: list[MultiLineItem] = None,
    ):
        self._years = years if years is not None else []
        self._line_item_definitions = self._collect_line_item_definitions(line_items)
        self._category_definitions = self._collect_category_definitions(
            self._line_item_definitions, categories
        )
        self.multi_line_items = multi_line_items if multi_line_items is not None else []
        self.constraints = constraints if constraints is not None else []

        self._build_and_calculate()

    @staticmethod
    def _collect_line_item_definitions(
        line_items: Union[list[LineItem], list[str], list[dict]] = None,
    ) -> list[LineItem]:
        """
        Collect and convert line item definitions from various input formats.

        This method handles three input formats for line items:
        1. List of LineItem objects - used as-is
        2. List of strings - converted to LineItem objects with those names
        3. List of dictionaries - converted using LineItem.from_dict()

        Args:
            line_items (Union[list[LineItem], list[str], list[dict]], optional):
                Line items in various formats. If None, returns empty list.

        Returns:
            list[LineItem]: List of LineItem objects

        Raises:
            TypeError: If line_items contains unsupported types
            ValueError: If string names are invalid or dictionaries are malformed
        """
        if line_items is None or len(line_items) == 0:
            return []

        line_item_definitions = []

        for item in line_items:
            if isinstance(item, LineItem):
                # Already a LineItem object, use as-is
                line_item_definitions.append(item)
            elif isinstance(item, str):
                # String name, create LineItem with that name
                line_item = LineItem(name=item)
                line_item_definitions.append(line_item)
            elif isinstance(item, dict):
                # Dictionary, use from_dict to create LineItem
                line_item = LineItem.from_dict(item)
                line_item_definitions.append(line_item)
            else:
                raise TypeError(
                    f"Line items must be LineItem objects, strings, or dictionaries, "
                    f"got {type(item)} for value: {item}"
                )

        return line_item_definitions

    @staticmethod
    def _collect_category_definitions(
        line_items: list[LineItem], categories: Union[list[Category], list[str]] = None
    ) -> list[Category]:
        """
        Collect category definitions from provided categories or infer from line items.

        If categories are provided, use them as the base. Categories can be provided
        as Category objects or as strings (which will be converted to Category objects
        with name=label). If not provided, automatically infer categories from the
        unique category names used in the line items. Multi-line items are no longer
        added as category definitions - they are only captured in metadata.

        Args:
            line_items (list[LineItem]): Line items to infer categories from
            categories (Union[list[Category], list[str]], optional): Explicit category
                definitions as Category objects or strings

        Returns:
            list[Category]: List of category definitions to use in the model
        """
        if categories is None or len(categories) == 0:
            # Auto-infer categories from line items when None or empty list
            category_names = set([item.category for item in line_items])
            category_definitions = []
            for name in category_names:
                category = Category(name=name, label=name)
                category_definitions.append(category)
        else:
            # Handle provided categories - could be Category objects or strings
            category_definitions = []
            for cat in categories:
                if isinstance(cat, Category):
                    # Already a Category object, use as-is
                    category_definitions.append(cat)
                elif isinstance(cat, str):
                    # String category name, convert to Category object
                    category = Category(name=cat, label=cat)
                    category_definitions.append(category)
                else:
                    raise TypeError(
                        f"Categories must be Category objects or strings, "
                        f"got {type(cat)} for value: {cat}"
                    )

        return category_definitions

    def _build_and_calculate(self):
        validate_years(self._years)
        validate_categories(self._category_definitions)
        validate_line_items(self._line_item_definitions, self._category_definitions)
        validate_multi_line_items(self.multi_line_items, self._category_definitions)
        validate_constraints(self.constraints, self._line_item_definitions)

        self.category_metadata = generate_category_metadata(
            self._category_definitions, self.multi_line_items
        )
        self.line_item_metadata = generate_line_item_metadata(
            self._line_item_definitions, self.category_metadata, self.multi_line_items
        )
        validate_formulas(self._line_item_definitions, self.line_item_metadata)

        self._value_matrix = generate_value_matrix(
            self._years,
            self._line_item_definitions + self.multi_line_items,
            self._category_definitions,
            self.line_item_metadata,
        )

    @property
    def years(self) -> list[int]:
        """
        Get or set the model's years.

        Setting years will trigger model recalculation.

        Returns:
            list[int]: Sorted list of years in the model
        """
        return self._years.copy()  # Return copy to prevent external modification

    @years.setter
    def years(self, new_years: list[int]) -> None:
        """
        Set the model's years and trigger recalculation.

        Args:
            new_years (list[int]): New years for the model
        """
        self.update.years(new_years)

    # ============================================================================
    # CORE DATA ACCESS (Magic Methods & Primary Interface)
    # ============================================================================

    def __getitem__(self, key: Union[tuple, str]) -> Union[float, LineItemResults]:
        """
        Get item values or LineItemResults using dictionary-style access.

        Supports two access patterns:
        - Tuple (item_name, year): Returns the float value for that item and year
        - String item_name: Returns a LineItemResults object for exploring the item

        Args:
            key: Either a tuple of (item_name, year) or a string item_name

        Returns:
            Union[float, LineItemResults]: Float value for tuple keys,
                LineItemResults object for string keys

        Raises:
            KeyError: If key format is invalid, item name not found,
                or year not in model

        Examples:
            >>> model["revenue", 2023]  # Returns float value: 1000.0
            >>> model["revenue"]        # Returns LineItemResults object
        """
        if isinstance(key, tuple):
            key_name, year = key
            return self.value(key_name, year)
        elif isinstance(key, str):
            return self.line_item(key)
        raise KeyError(
            "Key must be a tuple of (item_name, year) or a string item_name."
        )

    def value(self, name: str, year: int) -> float:
        """
        Retrieve a specific value from the model for a given item name and year.

        This is the primary method for accessing calculated values in the model.
        It returns the value for any defined name (line item, category total,
        or line item generator output) for a specific year in the model.

        Args:
            name (str): The name of the item to retrieve
                (must be a defined name in the model)
            year (int): The year to retrieve the value for
                (must be within the model's time horizon)

        Returns:
            float: The calculated value for the specified item and year

        Raises:
            KeyError: If the name is not found in the model's defined names
                or the year is not in the model's time horizon

        Examples:
            >>> model.value("revenue", 2023)  # Get revenue for 2023
            1000.0
            >>> model.value("profit_margin", 2024)  # Get profit margin for 2024
            0.15

        Notes:
            Dictionary-style lookup at the Model level is also supported:

            ```python
            model["revenue", 2023]  # Equivalent to model.value("revenue", 2023)
            ```
        """
        name_lookup = {item["name"]: item for item in self.line_item_metadata}
        if name not in name_lookup:
            raise KeyError(f"Name '{name}' not found in defined names.")
        if year not in self._years:
            raise KeyError(
                f"Year {year} not found in years. Available years: {self._years}"
            )
        return self._value_matrix[year][name]

    # ============================================================================
    # RESULTS OBJECTS & ANALYSIS
    # ============================================================================

    def line_item(self, item_name: str = None) -> LineItemResults:
        """
        Get a LineItemResults object for exploring and analyzing a specific named item.

        This method returns a [`LineItemResults`][pyproforma.models.results.LineItemResults]
        instance that provides convenient methods for notebook exploration of individual items
        including line items, category totals, and generator outputs.

        Args:
            item_name (str): The name of the item to analyze

        Returns:
            LineItemResults: An object with methods for exploring the item

        Raises:
            ValueError: If item_name is None or empty
            KeyError: If the item name is not found in defined names

        Examples:
            >>> revenue_item = model.line_item('revenue')
            >>> print(revenue_item)  # Shows summary information
            >>> revenue_item.values()  # Returns dict of year: value
            >>> revenue_item.to_series()  # Returns pandas Series

        Notes:
            Dictionary-style lookup at the Model level is also supported:

            ```python
            model["revenue"]
            # Returns LineItemResults object
            # (equivalent to model.line_item("revenue"))
            ```

        """  # noqa: E501
        if item_name is None or item_name == "":
            available_items = sorted([item["name"] for item in self.line_item_metadata])
            if available_items:
                raise ValueError(
                    (
                        "Item name is required. "
                        f"Available item names are: {available_items}"
                    )
                )
            else:
                raise ValueError(
                    "Item name is required, but no items are defined in this model."
                )

        return LineItemResults(self, item_name)

    def category(self, category_name: str = None) -> CategoryResults:
        """
        Get a CategoryResults object for exploring and analyzing a specific category.

        This method returns a CategoryResults instance that provides convenient methods
        for notebook exploration, including summary statistics, totals by year,
        DataFrame conversion, and more.

        Args:
            category_name (str): The name of the category to analyze

        Returns:
            CategoryResults: An object with methods for exploring the category

        Raises:
            ValueError: If category_name is None or empty
            KeyError: If the category name is not found

        Examples:
            >>> revenue = model.category('revenue')
            >>> print(revenue)  # Shows summary information
            >>> revenue.total()  # Returns dict of year: total
            >>> revenue.to_dataframe()  # Returns pandas DataFrame
        """
        if category_name is None or category_name == "":
            available_categories = [
                category["name"] for category in self.category_metadata
            ]
            if available_categories:
                raise ValueError(
                    (
                        f"Category name is required. "
                        f"Available category names are: {available_categories}"
                    )
                )
            else:
                raise ValueError(
                    (
                        "Category name is required, but no categories are "
                        "defined in this model."
                    )
                )

        return CategoryResults(self, category_name)

    def constraint(self, constraint_name: str = None) -> ConstraintResults:
        """
        Get a ConstraintResults object for exploring and analyzing a specific constraint.

        This method returns a ConstraintResults instance that provides convenient methods
        for notebook exploration, including constraint values, validation status,
        table formatting, and more.

        Args:
            constraint_name (str): The name of the constraint to analyze

        Returns:
            ConstraintResults: An object with methods for exploring the constraint

        Raises:
            ValueError: If constraint_name is None or empty
            KeyError: If the constraint name is not found

        Examples:
            >>> debt_constraint = model.constraint('debt_limit')
            >>> print(debt_constraint)  # Shows summary information
            >>> debt_constraint.values()  # Returns dict of year: value
            >>> debt_constraint.table()  # Returns Table object
        """  # noqa: E501
        if constraint_name is None or constraint_name == "":
            available_constraints = [constraint.name for constraint in self.constraints]
            if available_constraints:
                raise ValueError(
                    (
                        f"Constraint name is required. "
                        f"Available constraint names are: {available_constraints}"
                    )
                )
            else:
                raise ValueError(
                    (
                        "Constraint name is required, but no constraints are "
                        "defined in this model."
                    )
                )

        return ConstraintResults(self, constraint_name)

    # ============================================================================
    # NAMESPACE PROPERTIES
    # ============================================================================

    @property
    def tables(self):
        """Tables namespace"""
        return Tables(self)

    @property
    def charts(self):
        """Charts namespace"""
        return Charts(self)

    @property
    def update(self):
        """Update namespace for adding, updating, and deleting model components"""
        return UpdateNamespace(self)

    # ============================================================================
    # MODEL OPERATIONS
    # ============================================================================

    def copy(self) -> "Model":
        """
        Create a deep copy of the Model instance.

        This method creates a completely independent copy of the model, including
        deep copies of all line items, categories, line item generators, constraints, and
        the value matrix. Changes to the copy will not affect the original model.

        Returns:
            Model: A deep copy of the current Model instance

        Examples:
            >>> original_model = Model(line_items, years=[2023, 2024])
            >>> copied_model = original_model.copy()  # Changes won't affect original
        """  # noqa: E501
        # Create deep copies of all mutable objects
        copied_line_items = copy.deepcopy(self._line_item_definitions)
        copied_categories = copy.deepcopy(self._category_definitions)
        copied_multi_line_items = copy.deepcopy(self.multi_line_items)
        copied_constraints = copy.deepcopy(self.constraints)
        copied_years = copy.deepcopy(self._years)

        # Create new Model instance with copied objects
        copied_model = Model(
            line_items=copied_line_items,
            years=copied_years,
            categories=copied_categories,
            multi_line_items=copied_multi_line_items,
            constraints=copied_constraints,
        )

        return copied_model

    def scenario(self, item_updates: list[tuple[str, dict]]) -> "Model":
        """
        Create a new Model instance with the specified changes applied as a scenario.

        This method creates a deep copy of the current model and applies the provided
        updates to create a scenario for analysis. The original model remains unchanged.
        This is useful for what-if analysis, sensitivity testing, and comparing different
        scenarios without modifying the base model.

        The API matches the update_multiple_line_items method, accepting a list of tuples
        where each tuple contains a line item name and a dictionary of update parameters.

        Args:
            item_updates (list[tuple[str, dict]]): List of (name, update_params) tuples.
                Each tuple's first element is the line item name to update.
                Each tuple's second element is a dictionary of parameters to update,
                which can include: new_name, category, label, values, updated_values,
                formula, value_format.

        Returns:
            Model: A new Model instance with the specified changes applied

        Raises:
            ValueError: If any of the updates would result in an invalid model
            KeyError: If any line item name is not found in model

        Examples:
            >>> # Create a scenario with updated revenue and cost assumptions
            >>> scenario_model = model.scenario([
            ...     ("revenue", {"updated_values": {2023: 150000, 2024: 165000}}),
            ...     ("costs", {"formula": "revenue * 0.6"})
            ... ])
            >>>
            >>> # Compare scenarios
            >>> base_profit = model["profit", 2023]
            >>> scenario_profit = scenario_model["profit", 2023]
            >>> print(f"Base: {base_profit}, Scenario: {scenario_profit}")
            >>>
            >>> # Chain scenarios for complex analysis
            >>> optimistic = model.scenario([
            ...     ("revenue", {"updated_values": {2023: 200000}})
            ... ])
            >>> pessimistic = model.scenario([
            ...     ("revenue", {"updated_values": {2023: 80000}})
            ... ])

        Note:
            The scenario method preserves all model structure including categories,
            constraints, and line item generators. Only the specified line items
            are modified according to the provided parameters.
        """  # noqa: E501
        # Create a copy of the current model
        scenario_model = self.copy()

        # Apply updates to the copied model using the existing update functionality
        scenario_model.update.update_multiple_line_items(item_updates)

        return scenario_model

    def compare(self, other_model) -> Compare:
        """
        Create a comparison analysis between this model and another model.

        This method returns a Compare instance that provides comprehensive methods
        for analyzing differences between two models. The comparison includes value
        differences, structural changes, and analytical tools for understanding
        the impact of changes.

        Args:
            other_model (Model): The model to compare against this one

        Returns:
            Compare: A Compare instance with methods for analyzing differences

        Raises:
            ValueError: If models have no overlapping years for comparison

        Examples:
            >>> # Compare base model with scenario
            >>> base_model = Model(line_items, years=[2023, 2024])
            >>> scenario_model = base_model.scenario([("revenue", {"formula": "1200"})])
            >>> comparison = base_model.compare(scenario_model)
            >>>
            >>> # Analyze differences
            >>> comparison.difference("revenue", 2023)  # Absolute difference
            >>> comparison.percent_difference("revenue", 2023)  # Percentage difference
            >>> comparison.largest_changes(5)  # Top 5 changes
            >>>
            >>> # Structural analysis
            >>> comparison.structural_changes()  # What changed structurally
            >>> comparison.summary_stats()  # Overall comparison statistics
            >>>
            >>> # Export and reporting
            >>> comparison.to_dataframe()  # DataFrame of all differences
            >>> comparison.report()  # Text summary
            >>>
            >>> # Financial impact analysis
            >>> comparison.net_impact(2023)  # Total impact in 2023
            >>> comparison.category_difference("revenue")  # Category-level changes

        Available Compare Methods:
            - difference(item, year): Absolute difference for specific item/year
            - percent_difference(item, year): Percentage difference
            - ratio(item, year): Ratio between models
            - all_differences(): DataFrame of all differences
            - structural_changes(): Added/removed items and formula changes
            - largest_changes(n): Top N items with biggest changes
            - category_difference(category): Category-level differences
            - summary_stats(): Overall comparison statistics
            - net_impact(year): Total financial impact for a year
            - to_dataframe(): Export to structured DataFrame
            - report(): Formatted text summary
        """
        from ..compare import Compare

        return Compare(self, other_model)

    # ============================================================================
    # MODEL ELEMENTS
    # ============================================================================

    @property
    def line_item_names(self) -> list[str]:
        """
        Get list of all line item names.

        Returns:
            list[str]: List of line item names
        """
        return [item["name"] for item in self.line_item_metadata]

    def line_item_names_by_category(
        self, category_name: str = None
    ) -> Union[list[str], dict[str, list[str]]]:
        """
        Get line item names by category.

        Args:
            category_name (str, optional): The name of the category to filter by.
                If None, returns a dictionary mapping all category names to
                their line items.

        Returns:
            Union[list[str], dict[str, list[str]]]:
                - If category_name is provided: List of line item names in the
                  specified category
                - If category_name is None: Dictionary mapping category names to
                  lists of line item names

        Raises:
            KeyError: If the category name is not found (when category_name is
                provided)
        """
        if category_name is None:
            # Return dictionary mapping all categories to their line items
            result = {}
            for category in self.category_names:
                line_item_names = []
                for item in self.line_item_metadata:
                    if item["category"] == category:
                        line_item_names.append(item["name"])
                result[category] = line_item_names
            return result

        # Validate that the category exists
        if category_name not in self.category_names:
            available_categories = sorted(self.category_names)
            raise KeyError(
                f"Category '{category_name}' not found. "
                f"Available categories: {available_categories}"
            )

        # Get all line item names that belong to this category
        line_item_names = []
        for item in self.line_item_metadata:
            if item["category"] == category_name:
                line_item_names.append(item["name"])

        return line_item_names

    @property
    def line_item_definitions(self) -> tuple[LineItem, ...]:
        """
        Read-only access to line item definitions.

        Returns:
            tuple[LineItem, ...]: Immutable tuple of line item definitions
        """
        return self._line_item_definitions

    def line_item_definition(self, name: str) -> LineItem:
        """
        Get a line item definition by name.

        This method retrieves the
        [`LineItem`][pyproforma.models.line_item.LineItem] object that defines
        a specific line item in the model. This is useful for accessing the line item's
        properties such as formula, category, label, and value format.

        Args:
            name (str): The name of the line item to retrieve

        Returns:
            LineItem: The LineItem object with the specified name
        """
        for item in self._line_item_definitions:
            if item.name == name:
                return item
        valid_line_items = [item.name for item in self._line_item_definitions]
        raise KeyError(
            f"LineItem with name '{name}' not found. "
            f"Valid line item names are: {valid_line_items}"
        )

    @property
    def category_names(self) -> list[str]:
        """
        Get list of all category names.

        Returns:
            list[str]: List of category names
        """
        return [category["name"] for category in self.category_metadata]

    @property
    def category_definitions(self) -> tuple[Category, ...]:
        """
        Read-only access to category definitions.

        Returns:
            tuple[Category, ...]: Immutable tuple of category definitions
        """
        return self._category_definitions

    def category_definition(self, name: str) -> Category:
        """
        Get a category definition by name.

        This method retrieves the Category object that defines
        a specific category in the model. This is useful for accessing the category's
        properties such as label, total name, and whether it includes totals.

        Args:
            name (str): The name of the category to retrieve

        Returns:
            Category: The Category object with the specified name
        """
        for category in self._category_definitions:
            if category.name == name:
                return category
        valid_categories = [category["name"] for category in self.category_metadata]
        raise KeyError(
            f"Category item '{name}' not found. "
            f"Valid categories are: {valid_categories}"
        )

    def constraint_definition(self, name: str) -> Constraint:
        """Get a constraint definition by name.

        Args:
            name (str): The name of the constraint to retrieve

        Returns:
            Constraint: The constraint object with the specified name

        Raises:
            KeyError: If no constraint with the given name is found
        """
        for constraint in self.constraints:
            if constraint.name == name:
                return constraint
        valid_constraints = [constraint.name for constraint in self.constraints]
        raise KeyError(
            f"Constraint with name '{name}' not found. "
            f"Valid constraint names are: {valid_constraints}"
        )

    # ============================================================================
    # METADATA & INTERNAL LOOKUPS
    # ============================================================================

    def _get_item_metadata(self, item_name: str) -> dict:
        """
        Get item metadata from defined_names.

        Args:
            item_name (str): The name of the item to get info for

        Returns:
            dict: Dictionary containing item metadata including name, label,
                  value_format, source_type, and source_name

        Raises:
            KeyError: If the item name is not found in defined names
        """
        for defined_name in self.line_item_metadata:
            if defined_name["name"] == item_name:
                return defined_name
        raise KeyError(f"Item '{item_name}' not found in model")

    def _get_category_metadata(self, category_name: str) -> dict:
        """
        Get category metadata for a specific category name.

        Args:
            category_name (str): The name of the category to get metadata for

        Returns:
            dict: Dictionary containing category metadata including name, label,
                  include_total, total_name, total_label, and system_generated

        Raises:
            KeyError: If the category name is not found in category metadata
        """
        for category_meta in self.category_metadata:
            if category_meta["name"] == category_name:
                return category_meta
        available_categories = [cat["name"] for cat in self.category_metadata]
        raise KeyError(
            f"Category '{category_name}' not found in model. "
            f"Available categories: {available_categories}"
        )

    # ============================================================================
    # CATEGORY TOTALS
    # ============================================================================

    def category_total(self, category: str, year: int) -> float:
        """
        Retrieve a pre-calculated category total from the model's value matrix.

        This is a lookup method that returns the already computed total for a category
        from the model's value matrix. The total must have been previously calculated
        during model initialization.

        Args:
            category (str): The category name to get the total for
            year (int): The year to get the total for

        Returns:
            float: The pre-calculated category total

        Raises:
            KeyError: If the category total is not found in defined names or value matrix
        """  # noqa: E501
        # find category total name
        total_name_lookup = {
            x["source_name"]: x["name"]
            for x in self.line_item_metadata
            if x["source_type"] == "category"
        }
        total_name = total_name_lookup[category]
        return self.value(total_name, year)

    def _category_total(self, value_matrix, category: str, year: int) -> float:
        """
        Calculate the sum of all line items in a category for a specific year.

        This is an internal calculation method that computes the category total
        by summing all line item values in the specified category. Used during
        model initialization to populate the value matrix. None values are treated as 0.

        Args:
            value_matrix (dict): The value matrix containing calculated line item values
            category (str): The category name to calculate the total for
            year (int): The year to calculate the total for

        Returns:
            float: The calculated sum of all line items in the category
        """
        category_item = self.category_definition(category)
        total = 0
        for item in self._line_item_definitions:
            if item.category == category_item.name:
                value = value_matrix[year][item.name]
                if value is not None:
                    total += value
        return total

    # ============================================================================
    # UTILITIES & DISPLAY
    # ============================================================================

    def summary(self) -> dict:
        """
        Get a comprehensive summary of the model's structure and configuration.

        Returns:
            dict: Dictionary containing model summary information including:
                - years: List of years in the model
                - line_items_count: Number of line items
                - categories_count: Number of categories
                - multi_line_items_count: Number of multi line items
                - constraints_count: Number of constraints
                - line_items_by_category: Dictionary mapping category names to lists of line item names
                - multi_line_item_names: List of multi line item names
                - constraint_names: List of constraint names
                - defined_names_count: Total number of defined names (items that can be referenced)
        """  # noqa: E501
        # Count items by category
        line_items_by_category = {}
        for category in self.category_metadata:
            items_in_category = [
                item.name
                for item in self._line_item_definitions
                if item.category == category["name"]
            ]
            if items_in_category:  # Only include categories that have items
                line_items_by_category[category["name"]] = items_in_category

        return {
            "years": self._years,
            "years_count": len(self._years),
            "year_range": (
                f"{min(self._years)} - {max(self._years)}" if self._years else "None"
            ),
            "line_items_count": len(self._line_item_definitions),
            "categories_count": len(self.category_metadata),
            "multi_line_items_count": len(self.multi_line_items),
            "constraints_count": len(self.constraints),
            "line_items_by_category": line_items_by_category,
            "multi_line_item_names": [gen.name for gen in self.multi_line_items],
            "constraint_names": [const.name for const in self.constraints],
            "defined_names_count": len(self.line_item_metadata),
            "category_totals": [
                item["name"]
                for item in self.line_item_metadata
                if item["source_type"] == "category"
            ],
        }

    def _repr_html_(self) -> str:
        """
        HTML representation for Jupyter notebooks.

        Returns:
            str: Simple HTML string for rich display in Jupyter notebooks
        """
        summary = self.summary()

        lines = []
        lines.append("<strong>Model Summary:</strong><br>")
        lines.append(
            f"Years: {summary['year_range']} ({summary['years_count']} years)<br>"
        )
        lines.append(f"Line Items: {summary['line_items_count']}<br>")
        lines.append(f"Categories: {summary['categories_count']}<br>")
        lines.append(f"Multi Line Items: {summary['multi_line_items_count']}<br>")
        lines.append(f"Constraints: {summary['constraints_count']}<br>")

        return "".join(lines)

    def _is_last_item_in_category(self, name: str) -> bool:
        """Check if the given item name is the last item in its category"""
        # Find the item with the given name and get its category
        target_item = self.line_item_definition(name)

        # Get all items in the same category
        items_in_category = [
            item
            for item in self._line_item_definitions
            if item.category == target_item.category
        ]

        # Check if this is the last item in the category list
        return items_in_category[-1].name == name

    # ============================================================================
    # SERIALIZATION METHODS
    # ============================================================================
    # Serialization methods are provided by SerializationMixin
