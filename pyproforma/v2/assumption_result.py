"""
AssumptionResult class for v2 API.

This class provides a results wrapper for assumptions, providing a consistent
interface with LineItemResult for dictionary-style model access.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel


class AssumptionResult:
    """
    A read-only results wrapper for a single assumption in a v2 model.

    AssumptionResult provides convenient access to assumption values and metadata.
    It mirrors the interface of LineItemResult for consistency.

    Args:
        model: The parent ProformaModel instance
        name: The name of the assumption

    Examples:
        >>> result = model['inflation_rate']
        >>> result.value
        0.03
        >>> result.name
        'inflation_rate'
        >>> float(result)
        0.03
    """

    def __init__(self, model: "ProformaModel", name: str):
        """
        Initialize AssumptionResult.

        Args:
            model: The parent ProformaModel instance
            name: The name of the assumption

        Raises:
            AttributeError: If the assumption name doesn't exist in the model
        """
        self._model = model
        self._name = name

        # Validate that the assumption exists
        if name not in model.assumption_names:
            raise AttributeError(
                f"Assumption '{name}' not found in model. "
                f"Available assumptions: {', '.join(sorted(model.assumption_names))}"
            )

        # Cache the value from assumption_values
        self._value = model.av.get(name)

        # Cache the assumption specification for metadata access
        self._assumption_spec = getattr(model.__class__, name, None)

    def __repr__(self) -> str:
        """Return a string representation of the AssumptionResult."""
        return f"AssumptionResult(name='{self._name}', value={self._value})"

    def __str__(self) -> str:
        """Return a string representation showing the assumption name and value."""
        return f"{self._name}: {self._value}"

    def __float__(self) -> float:
        """
        Convert to float for numeric operations.

        Returns:
            float: The assumption value

        Examples:
            >>> inflation = model['inflation_rate']
            >>> float(inflation)
            0.03
        """
        return float(self._value)

    @property
    def name(self) -> str:
        """
        Get the name of the assumption.

        Returns:
            str: The assumption name
        """
        return self._name

    @property
    def value(self) -> float:
        """
        Get the assumption value.

        Returns:
            float: The assumption value

        Examples:
            >>> result = model['inflation_rate']
            >>> result.value
            0.03
        """
        return self._value

    @property
    def label(self) -> str | None:
        """
        Get the display label of the assumption.

        Returns the user-defined label if available, otherwise returns None.
        This is a read-only property.

        Returns:
            str | None: The assumption's display label, or None if not set

        Examples:
            >>> result = model['inflation_rate']
            >>> result.label
            'Inflation Rate'
        """
        if self._assumption_spec is not None and hasattr(
            self._assumption_spec, "label"
        ):
            return self._assumption_spec.label
        return None
