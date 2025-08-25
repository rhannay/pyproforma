import json
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

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
