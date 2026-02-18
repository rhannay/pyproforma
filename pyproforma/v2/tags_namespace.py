"""
TagNamespace classes for tag-based operations.

This module provides tag-based functionality:
- TagNamespace: For summing line items by tag (used in model.li.tag)
- ModelTagNamespace: For selecting line items by tag (used in model.tag)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.v2.line_items.line_item_selection import LineItemSelection
    from pyproforma.v2.line_items.line_item_values import LineItemValues
    from pyproforma.v2.proforma_model import ProformaModel


class TagNamespace:
    """
    Namespace for accessing tag-based summations.

    TagNamespace provides a convenient interface for summing line items by tag.
    It supports subscript notation to get the sum of all line items with a specific
    tag for a given period.

    Args:
        model: The parent ProformaModel instance
        li: The LineItemValues container

    Examples:
        >>> # Define a model with tags
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100}, tags=["income"])
        ...     interest = FixedLine(values={2024: 5}, tags=["income"])
        ...     expenses = FixedLine(values={2024: 60}, tags=["expense"])
        ...
        >>> model = MyModel(periods=[2024])
        >>> model.li.tag["income"][2024]  # Sum of revenue + interest
        105
        >>> model.li.tag["expense"][2024]
        60
    """

    def __init__(self, model: "ProformaModel", li: "LineItemValues"):
        """
        Initialize TagNamespace.

        Args:
            model: The parent ProformaModel instance
            li: The LineItemValues container
        """
        self._model = model
        self._li = li

    def __getitem__(self, tag: str) -> "TagSum":
        """
        Get a TagSum object for a specific tag.

        Args:
            tag (str): The tag name to sum

        Returns:
            TagSum: Object that supports period subscripting to get tag sums

        Examples:
            >>> income_sum = model.li.tag["income"]
            >>> income_sum[2024]
            105
        """
        return TagSum(self._model, self._li, tag)

    def __repr__(self):
        """Return a string representation of TagNamespace."""
        return f"TagNamespace(model={self._model.__class__.__name__})"


class TagSum:
    """
    Wrapper for summing line items with a specific tag.

    TagSum provides subscript access to get the sum of all line items
    with a specific tag for a given period.

    Args:
        model: The parent ProformaModel instance
        li: The LineItemValues container
        tag: The tag to sum

    Examples:
        >>> tag_sum = TagSum(model, li, "income")
        >>> tag_sum[2024]
        105
    """

    def __init__(self, model: "ProformaModel", li: "LineItemValues", tag: str):
        """
        Initialize TagSum.

        Args:
            model: The parent ProformaModel instance
            li: The LineItemValues container
            tag: The tag to sum
        """
        self._model = model
        self._li = li
        self._tag = tag

    def __getitem__(self, period: int) -> float:
        """
        Get the sum of all line items with this tag for a specific period.

        Args:
            period (int): The period to sum values for

        Returns:
            float: The sum of all line items with this tag for the period

        Raises:
            KeyError: If the period doesn't exist in the model

        Examples:
            >>> tag_sum = TagSum(model, li, "income")
            >>> tag_sum[2024]
            105
        """
        # Validate period exists
        if period not in self._model.periods:
            raise KeyError(
                f"Period {period} not found in model. "
                f"Available periods: {self._model.periods}"
            )

        total = 0.0

        # Sum all line items with this tag
        for line_item_name in self._model.line_item_names:
            # Get the line item specification from the class
            line_item_spec = getattr(self._model.__class__, line_item_name)

            # Check if the line item has this tag
            if hasattr(line_item_spec, "tags") and self._tag in line_item_spec.tags:
                # Get the value for this period from LineItemValues directly
                try:
                    value = self._li.get(line_item_name, period)
                    if value is not None:
                        total += value
                except (AttributeError, KeyError):
                    # Line item doesn't have a value for this period yet, skip it
                    pass

        return total

    def __repr__(self):
        """Return a string representation of TagSum."""
        return f"TagSum(tag={self._tag!r})"


class ModelTagNamespace:
    """
    Namespace for accessing line items by tag.

    ModelTagNamespace provides a convenient interface for selecting line items
    by tag. It supports subscript notation to get a LineItemSelection of all
    line items with a specific tag.

    Args:
        model: The parent ProformaModel instance

    Examples:
        >>> # Define a model with tags
        >>> class MyModel(ProformaModel):
        ...     revenue = FixedLine(values={2024: 100}, tags=["income"])
        ...     interest = FixedLine(values={2024: 5}, tags=["income"])
        ...     expenses = FixedLine(values={2024: 60}, tags=["expense"])
        ...
        >>> model = MyModel(periods=[2024])
        >>> income_selection = model.tag["income"]  # LineItemSelection
        >>> income_selection.names
        ['revenue', 'interest']
    """

    def __init__(self, model: "ProformaModel"):
        """
        Initialize ModelTagNamespace.

        Args:
            model: The parent ProformaModel instance
        """
        self._model = model

    def __getitem__(self, tag: str) -> "LineItemSelection":
        """
        Get a LineItemSelection for all line items with a specific tag.

        Args:
            tag (str): The tag name to select

        Returns:
            LineItemSelection: Selection containing all line items with the tag

        Examples:
            >>> income_items = model.tag["income"]
            >>> income_items.names
            ['revenue', 'interest']
        """
        # Import here to avoid circular dependency
        from pyproforma.v2.line_items.line_item_selection import LineItemSelection

        # Find all line items with this tag
        matching_names = []
        for name in self._model.line_item_names:
            line_item_spec = getattr(self._model.__class__, name)
            if hasattr(line_item_spec, "tags") and tag in line_item_spec.tags:
                matching_names.append(name)

        # Return a LineItemSelection with the matching names
        return LineItemSelection(self._model, matching_names)

    def __repr__(self):
        """Return a string representation of ModelTagNamespace."""
        return f"ModelTagNamespace(model={self._model.__class__.__name__})"
