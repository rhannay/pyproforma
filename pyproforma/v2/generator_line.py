"""
GeneratorLine class for line items that produce multiple related fields.

GeneratorLine represents a line item that generates multiple calculated fields
from a single specification. For example, a debt issue might generate fields
for principal, interest, debt outstanding, and proceeds.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING

from pyproforma.v2.line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.v2.assumption_values import AssumptionValues
    from pyproforma.v2.line_item_values import LineItemValues


class GeneratorLine(LineItem):
    """
    A line item that produces multiple related calculated fields.

    GeneratorLine is an abstract base class for line items that need to generate
    multiple related fields from a single specification. Examples include debt
    issues (generating principal, interest, outstanding balance, proceeds) or
    depreciation schedules (generating depreciation for multiple assets).

    Subclasses must implement the `field_names` property (to specify which fields
    are generated) and the `generate_fields` method (to calculate values for all
    fields in a given period).

    The generated fields are accessible as separate line items with names
    formatted as "{generator_name}_{field_name}".

    Examples:
        >>> # Subclass example
        >>> class DebtLine(GeneratorLine):
        ...     @property
        ...     def field_names(self):
        ...         return ["principal", "interest", "debt_outstanding", "proceeds"]
        ...
        ...     def generate_fields(self, a, li, t):
        ...         # Calculate and return all field values for period t
        ...         return {
        ...             "principal": 10000,
        ...             "interest": 500,
        ...             "debt_outstanding": 90000,
        ...             "proceeds": 0
        ...         }
        >>>
        >>> # In a model definition
        >>> class MyModel(ProformaModel):
        ...     debt = DebtLine(label="Long-term Debt")
        ...     # Access generated fields: li.debt_principal[t], li.debt_interest[t]

    Attributes:
        label (str, optional): Human-readable label for display purposes.
    """

    def __init__(self, label: str | None = None):
        """
        Initialize a GeneratorLine.

        Args:
            label (str, optional): Human-readable label. Defaults to None.
        """
        super().__init__(label=label)

    @property
    @abstractmethod
    def field_names(self) -> list[str]:
        """
        Return the list of field names this generator produces.

        Each field name will be prefixed with the generator's name when
        stored in the model (e.g., "principal" becomes "debt_principal"
        for a generator named "debt").

        Returns:
            list[str]: List of field names (without the generator name prefix).
        """
        pass

    @abstractmethod
    def generate_fields(
        self,
        a: "AssumptionValues",
        li: "LineItemValues",
        t: int,
    ) -> dict[str, float | None]:
        """
        Generate all field values for a specific period.

        This method should calculate and return values for all fields defined
        in `field_names` for the given period.

        Args:
            a (AssumptionValues): Container for accessing assumption values
            li (LineItemValues): Container for accessing other line item values
            t (int): Current period being calculated

        Returns:
            dict[str, float | None]: Dictionary mapping field names to their
                calculated values for the period. Keys should match the field
                names returned by `field_names`.

        Raises:
            ValueError: If unable to calculate field values
        """
        pass

    def get_value(self, period: int) -> None:
        """
        Get the value for a specific period.

        GeneratorLine doesn't have a single value; it generates multiple fields.
        This method returns None to satisfy the LineItem interface.

        Args:
            period (int): The period (year) to get the value for.

        Returns:
            None: GeneratorLine produces multiple fields, not a single value.
        """
        return None

    def __repr__(self):
        """Return a string representation of the GeneratorLine."""
        class_name = self.__class__.__name__
        if self.label:
            return f"{class_name}(label={self.label!r})"
        return f"{class_name}()"
