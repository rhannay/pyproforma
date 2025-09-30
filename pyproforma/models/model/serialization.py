import json
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import yaml

from .._utils import convert_to_name, validate_periods
from ..line_item import LineItem

if TYPE_CHECKING:
    from .model import Model


class SerializationMixin:
    """
    Mixin class providing serialization functionality for Model instances.

    This mixin provides methods to convert models to/from various formats
    including dictionary, YAML, and JSON representations.
    """

    def to_dict(self) -> dict:
        """
        Convert model to dictionary representation for serialization.

        Only includes user-defined categories

        Returns:
            dict: Dictionary containing all model data suitable for YAML/JSON export
        """
        return {
            "years": self.years,
            "line_items": [item.to_dict() for item in self._line_item_definitions],
            "categories": [
                category.to_dict() for category in self._category_definitions
            ],
            "line_item_generators": [
                generator.to_dict() for generator in self.multi_line_items
            ],
            "constraints": [constraint.to_dict() for constraint in self.constraints],
        }

    def to_yaml(self, file_path: str = None) -> str | None:
        """
        Export model configuration to YAML format.

        Args:
            file_path (str, optional): Path to save YAML file. If None, returns YAML string.  # noqa: E501

        Returns:
            str: YAML string representation of the model if file_path is None, otherwise None  # noqa: E501
        """  # noqa: E501
        config_dict = self.to_dict()
        yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)

        if file_path:
            Path(file_path).write_text(yaml_str)
            return None

        return yaml_str

    def to_json(self, file_path: str = None, indent: int = 2) -> str:
        """
        Export model configuration to JSON format.

        Args:
            file_path (str, optional): Path to save JSON file. If None, returns JSON string.  # noqa: E501
            indent (int): Number of spaces for JSON indentation

        Returns:
            str: JSON string representation of the model
        """  # noqa: E501
        config_dict = self.to_dict()
        json_str = json.dumps(config_dict, indent=indent)

        if file_path:
            Path(file_path).write_text(json_str)

        return json_str

    @classmethod
    def from_dict(cls, config_dict: dict) -> "Model":
        """
        Create Model from dictionary configuration.

        Args:
            config_dict (dict): Dictionary containing model configuration

        Returns:
            Model: New Model instance created from the configuration
        """
        from pyproforma.models.multi_line_item import MultiLineItem

        from ..category import Category
        from ..constraint import Constraint
        from ..line_item import LineItem

        # Reconstruct line items
        line_items = [
            LineItem.from_dict(item_dict)
            for item_dict in config_dict.get("line_items", [])
        ]

        # Reconstruct categories
        categories = [
            Category.from_dict(category_dict)
            for category_dict in config_dict.get("categories", [])
        ]

        # Reconstruct multi line items (basic implementation)
        multi_line_items = [
            MultiLineItem.from_dict(generator_dict)
            for generator_dict in config_dict.get("line_item_generators", [])
        ]

        # Reconstruct constraints
        constraints = [
            Constraint.from_dict(constraint_dict)
            for constraint_dict in config_dict.get("constraints", [])
        ]

        return cls(
            line_items=line_items,
            years=config_dict["years"],
            categories=categories,
            multi_line_items=multi_line_items,
            constraints=constraints,
        )

    @classmethod
    def from_yaml(cls, file_path: str = None, yaml_str: str = None) -> "Model":
        """
        Load model from YAML configuration.

        Args:
            file_path (str, optional): Path to YAML file to load
            yaml_str (str, optional): YAML string to parse

        Returns:
            Model: New Model instance loaded from YAML

        Raises:
            ValueError: If neither file_path nor yaml_str is provided
        """
        if file_path:
            yaml_str = Path(file_path).read_text()
        elif yaml_str is None:
            raise ValueError("Either file_path or yaml_str must be provided")

        config_dict = yaml.safe_load(yaml_str)
        return cls.from_dict(config_dict)

    @classmethod
    def from_json(cls, file_path: str = None, json_str: str = None) -> "Model":
        """
        Load model from JSON configuration.

        Args:
            file_path (str, optional): Path to JSON file to load
            json_str (str, optional): JSON string to parse

        Returns:
            Model: New Model instance loaded from JSON

        Raises:
            ValueError: If neither file_path nor json_str is provided
        """
        if file_path:
            json_str = Path(file_path).read_text()
        elif json_str is None:
            raise ValueError("Either file_path or json_str must be provided")

        config_dict = json.loads(json_str)
        return cls.from_dict(config_dict)

    @classmethod
    def from_dataframe(
        cls, df: pd.DataFrame, fill_in_periods: bool = False
    ) -> "Model":
        """
        Create Model from a pandas DataFrame.

        The DataFrame should have line item names in the first column and years
        in subsequent columns. Each row represents a line item with values for
        different years.

        Args:
            df (pd.DataFrame): DataFrame with line item names in first column
                and years as subsequent column headers. Column values should be
                numeric values for each year.
            fill_in_periods (bool, optional): If True, fills in missing years
                between the minimum and maximum year. Default is False.

        Returns:
            Model: New Model instance created from the DataFrame

        Raises:
            ValueError: If DataFrame is empty, has fewer than 2 columns, or
                contains invalid year columns or duplicate years.
            TypeError: If df is not a pandas DataFrame.

        Examples:
            >>> import pandas as pd
            >>> df = pd.DataFrame({
            ...     'name': ['revenue', 'expenses', 'profit'],
            ...     2023: [1000, 600, 400],
            ...     2024: [1200, 700, 500],
            ...     2025: [1400, 800, 600]
            ... })
            >>> model = Model.from_dataframe(df)
            >>> model.years
            [2023, 2024, 2025]
            >>> model['revenue', 2023]
            1000

            >>> # With fill_in_periods=True to fill gaps
            >>> df = pd.DataFrame({
            ...     'name': ['revenue'],
            ...     2023: [1000],
            ...     2025: [1400]
            ... })
            >>> model = Model.from_dataframe(df, fill_in_periods=True)
            >>> model.years
            [2023, 2024, 2025]
        """
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"Expected pandas DataFrame, got {type(df).__name__}"
            )

        if df.empty:
            raise ValueError("DataFrame cannot be empty")

        if len(df.columns) < 2:
            raise ValueError(
                "DataFrame must have at least 2 columns: "
                "one for names and at least one for years"
            )

        # Get the first column name (should be line item names)
        name_column = df.columns[0]

        # Get the year columns (all columns except the first)
        year_columns = df.columns[1:]

        # Validate and normalize the periods (year columns)
        periods = validate_periods(
            list(year_columns), fill_in_periods=fill_in_periods
        )

        # Create LineItem objects from the DataFrame
        line_items = []
        for _, row in df.iterrows():
            name = row[name_column]

            # Skip rows with missing names
            if pd.isna(name):
                continue

            # Convert name to string if it isn't already
            name = str(name)

            # Sanitize the name to ensure it meets validation requirements
            name = convert_to_name(name)

            # Build values dictionary for this line item
            values = {}
            for year_col in year_columns:
                year = int(year_col)  # Already validated by validate_periods
                value = row[year_col]

                # Only add non-null values
                if not pd.isna(value):
                    values[year] = value

            # Create LineItem with the name and values
            line_item = LineItem(name=name, values=values)
            line_items.append(line_item)

        # Create and return the Model with validated years
        return cls(line_items=line_items, years=periods)
