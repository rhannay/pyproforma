from typing import Union
from ..line_item import LineItem
from ..category import Category
from pyproforma.models.multi_line_item import MultiLineItem
from ..results import CategoryResults, LineItemResults, ConstraintResults
from ..constraint import Constraint
from .serialization import SerializationMixin
import copy
from ..compare import Compare
from .value_matrix import generate_value_matrix
from .validations import validate_categories, validate_constraints, validate_multi_line_items, validate_formulas, validate_line_items
from .metadata import collect_category_metadata, collect_line_item_metadata

# Namespace imports
from pyproforma.tables import Tables
from pyproforma.charts import Charts
from .model_update import UpdateNamespace

class Model(SerializationMixin):
    """
    Core financial modeling framework for building pro forma financial statements.
    
    Creates structured financial models with line items, categories, multi line items, and constraints.
    Supports multi-year modeling, automatic dependency resolution, and rich output formatting.
    
    Args:
        line_items (list[LineItem]): LineItem objects defining the model structure
        years (list[int]): Years for the model time horizon (required)
        categories (list[Category], optional): Category definitions (auto-inferred if None)
        constraints (list[Constraint], optional): Validation constraints
        multi_line_items (list[MultiLineItem], optional): Components that generate multiple line items
    
    Examples:
        >>> from pyproforma import Model, LineItem
        >>> 
        >>> revenue = LineItem(name="revenue", category="income", formula="1000")
        >>> expenses = LineItem(name="expenses", category="income", formula="revenue * 0.8")
        >>> 
        >>> model = Model(line_items=[revenue, expenses], years=[2023, 2024, 2025])
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
    """
    
    # ============================================================================
    # INITIALIZATION & SETUP
    # ============================================================================
    
    def __init__(
        self,
        line_items: list[LineItem],
        years: list[int] = None,
        categories: list[Category] = None,
        constraints: list[Constraint] = None,
        multi_line_items: list[MultiLineItem] = None
    ):
        
        if years is None:
            raise ValueError("Years must be provided as a list of integers.")
        if years == []:
            raise ValueError("Years cannot be an empty list.")
        self.years = sorted(years)
        
        self._category_definitions = self._collect_category_definitions(line_items, categories)
        self._line_item_definitions = line_items
        self.multi_line_items = multi_line_items if multi_line_items is not None else []
        self.constraints = constraints if constraints is not None else []

        validate_categories(self._category_definitions)
        validate_line_items(self._line_item_definitions, self._category_definitions)
        validate_multi_line_items(self.multi_line_items, self._category_definitions)
        validate_constraints(self.constraints, self._line_item_definitions)
        
        self.category_metadata = collect_category_metadata(self._category_definitions, self.multi_line_items)
        self.line_item_metadata = collect_line_item_metadata(
            self._line_item_definitions, self.category_metadata, self.multi_line_items
        )
        validate_formulas(self._line_item_definitions, self.line_item_metadata)

        self._value_matrix = generate_value_matrix(
            self.years,
            self._line_item_definitions + self.multi_line_items,
            self._category_definitions,
            self.line_item_metadata
        )

    @staticmethod
    def _collect_category_definitions(
        line_items: list[LineItem], 
        categories: list[Category] = None
    ) -> list[Category]:
        """
        Collect category definitions from provided categories or infer from line items.
        
        If categories are provided, use them as the base. If not, automatically infer 
        categories from the unique category names used in the line items.
        Multi-line items are no longer added as category definitions - they are only 
        captured in metadata.
        
        Args:
            line_items (list[LineItem]): Line items to infer categories from
            categories (list[Category], optional): Explicit category definitions
            
        Returns:
            list[Category]: List of category definitions to use in the model
        """
        if categories is None:
            # Auto-infer categories from line items
            category_names = set([item.category for item in line_items])
            category_definitions = []
            for name in category_names:
                category = Category(name=name, label=name)
                category_definitions.append(category)
        else:
            # Use provided categories as base
            category_definitions = list(categories)
        
        return category_definitions

    def _recalculate(self):
        validate_categories(self._category_definitions)
        validate_line_items(self._line_item_definitions, self._category_definitions)
        validate_constraints(self.constraints, self._line_item_definitions)
        validate_multi_line_items(self.multi_line_items, self._category_definitions)
        self.category_metadata = collect_category_metadata(self._category_definitions, self.multi_line_items)
        self.line_item_metadata = collect_line_item_metadata(
            self._line_item_definitions, self.category_metadata, self.multi_line_items
        )
        validate_formulas(self._line_item_definitions, self.line_item_metadata)
        self._value_matrix = generate_value_matrix(
            self.years,
            self._line_item_definitions + self.multi_line_items,
            self._category_definitions,
            self.line_item_metadata
        )

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
            KeyError: If key format is invalid, item name not found, or year not in model
            
        Examples:
            >>> model["revenue", 2023]  # Returns float value: 1000.0
            >>> model["revenue"]        # Returns LineItemResults object
        """
        if isinstance(key, tuple):
            key_name, year = key
            return self.value(key_name, year)
        elif isinstance(key, str):
            return self.line_item(key)
        raise KeyError("Key must be a tuple of (item_name, year) or a string item_name.")
    
    def value(self, name: str, year: int) -> float:
        """
        Retrieve a specific value from the model for a given item name and year.
        
        This is the primary method for accessing calculated values in the model. It returns
        the value for any defined name (line item, category total, or line item generator output)
        for a specific year in the model.
        
        Args:
            name (str): The name of the item to retrieve (must be a defined name in the model)
            year (int): The year to retrieve the value for (must be within the model's time horizon)
            
        Returns:
            float: The calculated value for the specified item and year
            
        Raises:
            KeyError: If the name is not found in the model's defined names or the year is not in the model's time horizon
            
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
        name_lookup = {item['name']: item for item in self.line_item_metadata}
        if name not in name_lookup:
            raise KeyError(f"Name '{name}' not found in defined names.")
        if year not in self.years:
            raise KeyError(f"Year {year} not found in years. Available years: {self.years}")
        return self._value_matrix[year][name]



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

    @property
    def line_item_definitions(self) -> tuple[LineItem, ...]:
        """
        Read-only access to line item definitions.
        
        Returns:
            tuple[LineItem, ...]: Immutable tuple of line item definitions
        """
        return self._line_item_definitions
    
    @property
    def line_item_names(self) -> list[str]:
        """
        Get list of all line item names.
        
        Returns:
            list[str]: List of line item names
        """
        return [item['name'] for item in self.line_item_metadata]

    @property
    def category_definitions(self) -> tuple[Category, ...]:
        """
        Read-only access to category definitions.
        
        Returns:
            tuple[Category, ...]: Immutable tuple of category definitions
        """
        return self._category_definitions
    
    @property
    def category_names(self) -> list[str]:
        """
        Get list of all category names.
        
        Returns:
            list[str]: List of category names
        """
        return [category['name'] for category in self.category_metadata]

    # ============================================================================
    # LOOKUP/GETTER METHODS
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
            if defined_name['name'] == item_name:
                return defined_name
        raise KeyError(f"Item '{item_name}' not found in model")

    def _metadata_for_category(self, category_name: str) -> dict:
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
            if category_meta['name'] == category_name:
                return category_meta
        available_categories = [cat['name'] for cat in self.category_metadata]
        raise KeyError(f"Category '{category_name}' not found in model. Available categories: {available_categories}")

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
            available_categories = [category['name'] for category in self.category_metadata]
            if available_categories:
                raise ValueError(f"Category name is required. Available category names are: {available_categories}")
            else:
                raise ValueError("Category name is required, but no categories are defined in this model.")
        
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
        """
        if constraint_name is None or constraint_name == "":
            available_constraints = [constraint.name for constraint in self.constraints]
            if available_constraints:
                raise ValueError(f"Constraint name is required. Available constraint names are: {available_constraints}")
            else:
                raise ValueError("Constraint name is required, but no constraints are defined in this model.")
        
        return ConstraintResults(self, constraint_name)
    
    def line_item(self, item_name: str = None) -> LineItemResults:
        """
        Get a LineItemResults object for exploring and analyzing a specific named item.
        
        This method returns a [`LineItemResults`][pyproforma.models.results.LineItemResults] instance that provides convenient methods
        for notebook exploration of individual items including line items,
        category totals, and generator outputs.
        
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
            model["revenue"]        # Returns LineItemResults object (equivalent to model.line_item("revenue"))
            ```

        """
        if item_name is None or item_name == "":
            available_items = sorted([item['name'] for item in self.line_item_metadata])
            if available_items:
                raise ValueError(f"Item name is required. Available item names are: {available_items}")
            else:
                raise ValueError("Item name is required, but no items are defined in this model.")
        
        return LineItemResults(self, item_name)
    
    def line_item_definition(self, name: str) -> LineItem:
        """
        Get a line item definition by name.
        
        This method retrieves the [`LineItem`][pyproforma.models.line_item.LineItem] object that defines
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
        raise KeyError(f"LineItem with name '{name}' not found. Valid line item names are: {valid_line_items}")
    
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
        valid_categories = [category['name'] for category in self.category_metadata]
        raise KeyError(f"Category item '{name}' not found. Valid categories are: {valid_categories}")
    
    def line_item_names_by_category(self, category_name: str) -> list[str]:
        """
        Get all line item names in a specific category.
        
        Args:
            category_name (str): The name of the category to filter by
            
        Returns:
            list[str]: List of line item names in the specified category
            
        Raises:
            KeyError: If the category name is not found
        """
        # Validate that the category exists
        if category_name not in self.category_names:
            available_categories = sorted(self.category_names)
            raise KeyError(f"Category '{category_name}' not found. Available categories: {available_categories}")
        
        # Get all line item names that belong to this category
        line_item_names = []
        for item in self._line_item_definitions:
            if item.category == category_name:
                line_item_names.append(item.name)
        
        return line_item_names

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
        raise KeyError(f"Constraint with name '{name}' not found. Valid constraint names are: {valid_constraints}")


    # ============================================================================
    # CALCULATION METHODS
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
        """
        # find category total name
        total_name_lookup = {x['source_name']: x['name'] for x in self.line_item_metadata if x['source_type'] == 'category'}
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
    # HELPER/UTILITY METHODS
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
        """
        # Count items by category
        line_items_by_category = {}
        for category in self.category_metadata:
            items_in_category = [item.name for item in self._line_item_definitions if item.category == category['name']]
            if items_in_category:  # Only include categories that have items
                line_items_by_category[category['name']] = items_in_category
        
        return {
            'years': self.years,
            'years_count': len(self.years),
            'year_range': f"{min(self.years)} - {max(self.years)}" if self.years else "None",
            'line_items_count': len(self._line_item_definitions),
            'categories_count': len(self.category_metadata),
            'multi_line_items_count': len(self.multi_line_items),
            'constraints_count': len(self.constraints),
            'line_items_by_category': line_items_by_category,
            'multi_line_item_names': [gen.name for gen in self.multi_line_items],
            'constraint_names': [const.name for const in self.constraints],
            'defined_names_count': len(self.line_item_metadata),
            'category_totals': [item['name'] for item in self.line_item_metadata if item['source_type'] == 'category']
        }

    def _repr_html_(self) -> str:
        """
        HTML representation for Jupyter notebooks.
        
        Returns:
            str: HTML string for rich display in Jupyter notebooks
        """
        summary = self.summary()
        
        html = """
        <div style="font-family: Arial, sans-serif; margin: 10px;">
            <h3 style="color: #2E8B57; margin-bottom: 15px;">📊 Model Summary</h3>
            
            <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #007acc;">
                    <strong>Years:</strong> {years_count} years<br>
                    <span style="color: #666; font-size: 0.9em;">{year_range}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #28a745;">
                    <strong>Line Items:</strong> {line_items_count}<br>
                    <span style="color: #666; font-size: 0.9em;">Across {categories_count} categories</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #ffc107;">
                    <strong>Multi Line Items:</strong> {multi_line_items_count}<br>
                    <strong>Constraints:</strong> {constraints_count}
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #6f42c1;">
                    <strong>Total Defined Names:</strong> {defined_names_count}<br>
                    <span style="color: #666; font-size: 0.9em;">Items available for reference</span>
                </div>
            </div>
        """.format(**summary)
        
        # Add categories and their line items
        if summary['line_items_by_category']:
            html += """
            <div style="margin-bottom: 20px;">
                <h4 style="color: #495057; margin-bottom: 10px;">📋 Categories & Line Items</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
            """
            
            for category, items in summary['line_items_by_category'].items():
                html += f"""
                    <div style="background: #ffffff; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px;">
                        <div style="font-weight: bold; color: #495057; margin-bottom: 8px; border-bottom: 1px solid #dee2e6; padding-bottom: 4px;">
                            {category} ({len(items)} items)
                        </div>
                        <div style="font-size: 0.9em; line-height: 1.4;">
                """
                
                for item in items:
                    html += f'<div style="color: #6c757d; padding: 2px 0;">• {item}</div>'
                
                html += """
                        </div>
                    </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        # Add multi line items if any
        if summary['multi_line_item_names']:
            html += """
            <div style="margin-bottom: 20px;">
                <h4 style="color: #495057; margin-bottom: 10px;">⚙️ Multi Line Items</h4>
                <div style="background: #ffffff; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px;">
            """
            for gen_name in summary['multi_line_item_names']:
                html += f'<span style="display: inline-block; background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 0.9em;">{gen_name}</span>'
            html += """
                </div>
            </div>
            """
        
        # Add constraints if any
        if summary['constraint_names']:
            html += """
            <div style="margin-bottom: 20px;">
                <h4 style="color: #495057; margin-bottom: 10px;">🔒 Constraints</h4>
                <div style="background: #ffffff; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px;">
            """
            for const_name in summary['constraint_names']:
                html += f'<span style="display: inline-block; background: #fff3e0; color: #f57c00; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 0.9em;">{const_name}</span>'
            html += """
                </div>
            </div>
            """
        
        # Add category totals if any
        if summary['category_totals']:
            html += """
            <div style="margin-bottom: 20px;">
                <h4 style="color: #495057; margin-bottom: 10px;">📈 Category Totals</h4>
                <div style="background: #ffffff; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px;">
            """
            for total_name in summary['category_totals']:
                html += f'<span style="display: inline-block; background: #e8f5e8; color: #2e7d32; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 0.9em;">{total_name}</span>'
            html += """
                </div>
            </div>
            """
        
        html += """
        </div>
        """
        
        return html

    def _is_last_item_in_category(self, name: str) -> bool:
        """Check if the given item name is the last item in its category"""
        # Find the item with the given name and get its category
        target_item = self.line_item_definition(name)
        
        # Get all items in the same category
        items_in_category = [item for item in self._line_item_definitions if item.category == target_item.category]
        
        # Check if this is the last item in the category list
        return items_in_category[-1].name == name

    # ============================================================================
    # CLASS METHODS & ALTERNATIVE CONSTRUCTORS
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
        """
        # Create deep copies of all mutable objects
        copied_line_items = copy.deepcopy(self._line_item_definitions)
        copied_categories = copy.deepcopy(self._category_definitions)
        copied_multi_line_items = copy.deepcopy(self.multi_line_items)
        copied_constraints = copy.deepcopy(self.constraints)
        copied_years = copy.deepcopy(self.years)
        
        # Create new Model instance with copied objects
        copied_model = Model(
            line_items=copied_line_items,
            years=copied_years,
            categories=copied_categories,
            multi_line_items=copied_multi_line_items,
            constraints=copied_constraints
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
            >>> optimistic = model.scenario([("revenue", {"updated_values": {2023: 200000}})])
            >>> pessimistic = model.scenario([("revenue", {"updated_values": {2023: 80000}})])
            
        Note:
            The scenario method preserves all model structure including categories,
            constraints, and line item generators. Only the specified line items
            are modified according to the provided parameters.
        """
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
    # SERIALIZATION METHODS
    # ============================================================================
    # Serialization methods are provided by SerializationMixin






