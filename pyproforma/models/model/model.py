from ..line_item import LineItem, Category
from pyproforma.models.line_item_generator import LineItemGenerator
from ..results import CategoryResults, LineItemResults, ConstraintResults
from ..constraint import Constraint
from .serialization import SerializationMixin
import copy
from ..compare import Compare

# Namespace imports
from pyproforma.tables import Tables
from pyproforma.charts import Charts
from .model_update import UpdateNamespace

class Model(SerializationMixin):
    """
    Core financial modeling framework for building pro forma financial statements.
    
    Creates structured financial models with line items, categories, line item generators, and constraints.
    Supports multi-year modeling, automatic dependency resolution, and rich output formatting.
    
    Args:
        line_items (list[LineItem]): LineItem objects defining the model structure
        years (list[int]): Years for the model time horizon (required)
        categories (list[Category], optional): Category definitions (auto-inferred if None)
        constraints (list[Constraint], optional): Validation constraints
        line_item_generators (list[LineItemGenerator], optional): Components that generate multiple line items
    
    Examples:
        >>> from pyproforma import Model, LineItem
        >>> 
        >>> revenue = LineItem(name="revenue", category="income", formula="1000")
        >>> expenses = LineItem(name="expenses", category="income", formula="revenue * 0.8")
        >>> 
        >>> model = Model(line_items=[revenue, expenses], years=[2023, 2024, 2025])
        >>> 
        >>> # Access values
        >>> model.get_value("revenue", 2023)  # 1000
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
        - get_value(name, year): Get value for any item/year
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
        line_item_generators: list[LineItemGenerator] = None
    ):
        
        if years is None:
            raise ValueError("Years must be provided as a list of integers.")
        if years == []:
            raise ValueError("Years cannot be an empty list.")
        self.years = sorted(years)
        
        self._line_item_definitions = line_items

        # if no categories provided, gather unique categories from line_items
        if categories is None:
            category_names = set([item.category for item in line_items])
            self._category_definitions = [
                Category(name=name, label=name)
                for name in category_names
            ]
        else:
            self._category_definitions = categories

        self.constraints = constraints if constraints is not None else []
        self.line_item_generators = line_item_generators if line_item_generators is not None else []

        self._validate_categories()
        self._validate_constraints()
        self._validate_line_item_generators()

        self.defined_names_metadata = self._gather_defined_names()

        self._value_matrix = self._generate_value_matrix()

    def _validate_categories(self):
        """
        Validates that all categories referenced by line items are defined in the model's categories,
        and that all category names are unique.

        Raises:
            ValueError: If a line item's category is not present in the list of defined categories,
                       or if duplicate category names are found.
        """
        # Validate that all category names are unique
        category_names = [category.name for category in self._category_definitions]
        duplicates = set([name for name in category_names if category_names.count(name) > 1])
        
        if duplicates:
            raise ValueError(f"Duplicate category names not allowed: {', '.join(sorted(duplicates))}")
        
        # Validate that all item types in line_items are defined in categories        
        for item in self._line_item_definitions:
            if item.category not in category_names:
                raise ValueError(f"Category '{item.category}' for LineItem '{item.name}' is not defined category.")


    def _validate_constraints(self):
        """
        Validates that all constraints have unique names and reference existing line items.

        Raises:
            ValueError: If two or more constraints have the same name, or if a constraint
                       references a line item that doesn't exist.
        """
        if not self.constraints:
            return
            
        constraint_names = [constraint.name for constraint in self.constraints]
        duplicates = set([name for name in constraint_names if constraint_names.count(name) > 1])
        
        if duplicates:
            raise ValueError(f"Duplicate constraint names not allowed: {', '.join(sorted(duplicates))}")
        
        # Validate that all constraint line_item_names reference existing line items
        line_item_names = [item.name for item in self._line_item_definitions]
        for constraint in self.constraints:
            if constraint.line_item_name not in line_item_names:
                raise ValueError(f"Constraint '{constraint.name}' references unknown line item '{constraint.line_item_name}'")

    def _validate_line_item_generators(self):
        """
        Validates that all line item generators have unique names.

        Raises:
            ValueError: If two or more line item generators have the same name.
        """
        if not self.line_item_generators:
            return
            
        generator_names = [generator.name for generator in self.line_item_generators]
        duplicates = set([name for name in generator_names if generator_names.count(name) > 1])
        
        if duplicates:
            raise ValueError(f"Duplicate line item generator names not allowed: {', '.join(sorted(duplicates))}")

    def _gather_defined_names(self) -> list[dict]:
        """
        Collects all defined names across the model to create a comprehensive namespace.
        
        This method aggregates identifiers from all model components including 
        line items, category totals, and line item generators to 
        build a unified namespace for value lookups and validation.
        
        Returns:
            list[dict]: A list of dictionaries, each containing:
                - 'name' (str): The identifier name used for lookups
                - 'source_type' (str): The component type that defines this name
                  ('line_item', 'category', 'line_item_generator')
                - 'source_name' (str): The original source object's name
                
        Raises:
            ValueError: If duplicate names are found across different components
                       
        Example:
            For a model with revenue line item and revenue category:
            [
                {'name': 'revenue', 'source_type': 'line_item', 'source_name': 'revenue'},
                {'name': 'total_revenue', 'source_type': 'category', 'source_name': 'revenue'}
            ]
        """
        defined_names = []
        for item in self._line_item_definitions:
            defined_names.append({'name': item.name, 'label': item.label, 'value_format': item.value_format, 'source_type': 'line_item', 'source_name': item.name, })
        for category in self._category_definitions:
            if category.include_total:
                # Only include category total if there are line items in this category
                items_in_category = [item for item in self._line_item_definitions if item.category == category.name]
                if items_in_category:  # Only add total if category has items
                    defined_names.append({'name': category.total_name, 'label': category.total_label, 'value_format': 'no_decimals', 'source_type': 'category', 'source_name': category.name})
        for generator in self.line_item_generators:
            for gen_name in generator.defined_names:
                defined_names.append({'name': gen_name, 'label': gen_name, 'value_format': 'no_decimals', 'source_type': 'line_item_generator', 'source_name': generator.name})
        
        # Check for duplicate names in defined_names
        # and raise ValueError if any duplicates are found.
        names_list = [item['name'] for item in defined_names]
        duplicates = set([name for name in names_list if names_list.count(name) > 1])
        if duplicates:
            raise ValueError(f"Duplicate defined names found in Model: {', '.join(duplicates)}")
        return defined_names

    def _generate_value_matrix(self) -> dict[int, dict[str, float]]:
        value_matrix = {}
        for year in self.years:
            value_matrix[year] = {}
        
            # Calculate line items in dependency order
            calculated_items = set()
            remaining_items = self._line_item_definitions.copy()
            max_iterations = len(self._line_item_definitions) + 1  # Safety valve
            iteration = 0
            
            # Track which line item generators have been successfully calculated
            remaining_generators = self.line_item_generators.copy() if self.line_item_generators else []
            
            while (remaining_items or remaining_generators) and iteration < max_iterations:
                iteration += 1
                items_calculated_this_round = []
                generators_calculated_this_round = []
                
                # Try to calculate line item generators for this year
                for generator in remaining_generators:
                    try:
                        # Try to calculate values for this line item generator
                        generated_values = generator.get_values(value_matrix, year)
                        
                        # Update value matrix with the generated values
                        value_matrix[year].update(generated_values)
                        
                        # Mark this generator as calculated
                        generators_calculated_this_round.append(generator)
                    except (KeyError, ValueError):
                        # Skip if dependencies are not yet met
                        # Will try again in the next iteration
                        continue
                
                # Remove successfully calculated generators from remaining list
                for generator in generators_calculated_this_round:
                    remaining_generators.remove(generator)
                
                for item in remaining_items:
                    try:
                        # Try to calculate the item
                        value_matrix[year][item.name] = item.get_value(value_matrix, year)
                        calculated_items.add(item.name)
                        items_calculated_this_round.append(item)
                                
                    except (KeyError, ValueError) as e:
                        # Check if this is a None value error - these should be raised immediately
                        if isinstance(e, ValueError) and "has None value" in str(e) and "Cannot use None values in formulas" in str(e):
                            raise e
                        
                        # Check if this is a missing variable error vs dependency issue
                        if isinstance(e, ValueError) and "not found for year" in str(e):
                            # Extract variable name from error message
                            import re as error_re
                            match = error_re.search(r"Variable '(\w+)' not found for year", str(e))
                            if match:
                                var_name = match.group(1)
                                # Check if this variable exists in our defined names
                                all_defined_names = [name['name'] for name in self.defined_names_metadata]
                                if var_name not in all_defined_names:
                                    # Variable truly doesn't exist, re-raise the error
                                    raise e
                        # Item depends on something not yet calculated, skip for now
                        continue
            
                # Remove successfully calculated items from remaining list
                for item in items_calculated_this_round:
                    remaining_items.remove(item)
                
                # After each round, check if we can calculate any category totals
                for category in self._category_definitions:
                    if category.include_total and category.total_name not in value_matrix[year]:
                        # Check if all items in this category have been calculated
                        items_in_category = [item for item in self._line_item_definitions if item.category == category.name]
                        all_items_calculated = all(item.name in calculated_items for item in items_in_category)
                        
                        if all_items_calculated and items_in_category:  # Only if category has items
                            category_total = self._category_total(value_matrix, category.name, year)
                            total_name = category.total_name
                            value_matrix[year][total_name] = category_total
                
                # If no progress was made this round, we have circular dependencies
                if not items_calculated_this_round and not generators_calculated_this_round:
                    break
            
            # Check if all items and generators were calculated
            errors = []
            if remaining_items:
                failed_items = [item.name for item in remaining_items]
                errors.append(f"Could not calculate line items due to missing dependencies or circular references: {failed_items}")
                
            if remaining_generators:
                failed_generators = [generator.name for generator in remaining_generators]
                errors.append(f"Could not calculate line item generators due to missing dependencies or circular references: {failed_generators}")
                
            if errors:
                raise ValueError("\n".join(errors))
        
            # Ensure all defined names are present in the value matrix
            for name in self.defined_names_metadata:
                if name['name'] not in value_matrix[year]:
                    raise KeyError(f"Defined name '{name['name']}' not found in value matrix for year {year}.")
    
        return value_matrix

    def _reclalculate(self):
        self._validate_categories()
        self._validate_constraints()
        self._validate_line_item_generators()
        self.defined_names_metadata = self._gather_defined_names()
        self._value_matrix = self._generate_value_matrix()

    # ============================================================================
    # CORE DATA ACCESS (Magic Methods & Primary Interface)
    # ============================================================================

    def __getitem__(self, key: tuple) -> float:
        if isinstance(key, tuple):
            key_name, year = key
            return self.get_value(key_name, year)
        raise KeyError("Key must be a tuple of (item_name, year).")
    
    def get_value(self, name: str, year: int) -> float:
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
            >>> model.get_value("revenue", 2023)  # Get revenue for 2023
            1000.0
            >>> model.get_value("profit_margin", 2024)  # Get profit margin for 2024
            0.15
            
        Notes:
            Dictionary-style lookup is also supported:
            
            ```python
            model["revenue", 2023]  # Equivalent to model.get_value("revenue", 2023)
            ```
        """
        name_lookup = {item['name']: item for item in self.defined_names_metadata}
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
        return [item.name for item in self._line_item_definitions]

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
        return [category.name for category in self._category_definitions]

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
        for defined_name in self.defined_names_metadata:
            if defined_name['name'] == item_name:
                return defined_name
        raise KeyError(f"Item '{item_name}' not found in model")

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
            available_categories = [category.name for category in self._category_definitions]
            if available_categories:
                raise ValueError(f"Category name is required. Available category names are: {available_categories}")
            else:
                raise ValueError("Category name is required, but no categories are defined in this model.")
        
        # Validate that the category exists
        self.get_category_definition(category_name)  # This will raise KeyError if not found
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
        """
        if item_name is None or item_name == "":
            available_items = sorted([item['name'] for item in self.defined_names_metadata])
            if available_items:
                raise ValueError(f"Item name is required. Available item names are: {available_items}")
            else:
                raise ValueError("Item name is required, but no items are defined in this model.")
        
        return LineItemResults(self, item_name)
    
    def li(self, item_name: str = None) -> LineItemResults:
        """Shorthand for line_item() - see line_item() for full documentation."""
        return self.line_item(item_name)
    
    def get_line_item_definition(self, name: str) -> LineItem:
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
    
    def get_category_definition(self, name: str) -> Category:
        """
        Get a category definition by name.
        
        This method retrieves the [`Category`][pyproforma.models.line_item.Category] object that defines
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
        valid_categories = [category.name for category in self._category_definitions]
        raise KeyError(f"Category item '{name}' not found. Valid categories are: {valid_categories}")
    
    def get_line_item_definitions_by_category(self, category_name: str) -> list[LineItem]:
        """Get all line items in a specific category."""
        items = []
        for item in self._line_item_definitions:
            if item.category == category_name:
                items.append(item)
        return items

    def get_line_item_names_by_category(self, category_name: str) -> list[str]:
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
        self.get_category_definition(category_name)  # This will raise KeyError if not found
        
        # Get all line item names that belong to this category
        line_item_names = []
        for item in self._line_item_definitions:
            if item.category == category_name:
                line_item_names.append(item.name)
        
        return line_item_names

    def get_constraint_definition(self, name: str) -> Constraint:
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
        total_name_lookup = {x['source_name']: x['name'] for x in self.defined_names_metadata if x['source_type'] == 'category'}
        total_name = total_name_lookup[category]
        return self.get_value(total_name, year)

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
        category_item = self.get_category_definition(category)
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
                - line_item_generators_count: Number of line item generators
                - constraints_count: Number of constraints
                - line_items_by_category: Dictionary mapping category names to lists of line item names
                - line_item_generator_names: List of line item generator names
                - constraint_names: List of constraint names
                - defined_names_count: Total number of defined names (items that can be referenced)
        """
        # Count items by category
        line_items_by_category = {}
        for category in self._category_definitions:
            items_in_category = [item.name for item in self._line_item_definitions if item.category == category.name]
            if items_in_category:  # Only include categories that have items
                line_items_by_category[category.name] = items_in_category
        
        return {
            'years': self.years,
            'years_count': len(self.years),
            'year_range': f"{min(self.years)} - {max(self.years)}" if self.years else "None",
            'line_items_count': len(self._line_item_definitions),
            'categories_count': len(self._category_definitions),
            'line_item_generators_count': len(self.line_item_generators),
            'constraints_count': len(self.constraints),
            'line_items_by_category': line_items_by_category,
            'line_item_generator_names': [gen.name for gen in self.line_item_generators],
            'constraint_names': [const.name for const in self.constraints],
            'defined_names_count': len(self.defined_names_metadata),
            'category_totals': [item['name'] for item in self.defined_names_metadata if item['source_type'] == 'category']
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
                    <strong>Line Item Generators:</strong> {line_item_generators_count}<br>
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
        
        # Add line item generators if any
        if summary['line_item_generator_names']:
            html += """
            <div style="margin-bottom: 20px;">
                <h4 style="color: #495057; margin-bottom: 10px;">⚙️ Line Item Generators</h4>
                <div style="background: #ffffff; border: 1px solid #dee2e6; border-radius: 6px; padding: 12px;">
            """
            for gen_name in summary['line_item_generator_names']:
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
        target_item = self.get_line_item_definition(name)
        
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
        copied_line_item_generators = copy.deepcopy(self.line_item_generators)
        copied_constraints = copy.deepcopy(self.constraints)
        copied_years = copy.deepcopy(self.years)
        
        # Create new Model instance with copied objects
        copied_model = Model(
            line_items=copied_line_items,
            years=copied_years,
            categories=copied_categories,
            line_item_generators=copied_line_item_generators,
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






