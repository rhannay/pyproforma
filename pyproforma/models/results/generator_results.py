from typing import TYPE_CHECKING, Dict

import pandas as pd

if TYPE_CHECKING:
    from ..model import Model


class GeneratorResults:
    """
    A helper class that provides convenient access to generator field values.

    This class is instantiated through the Model.generator() method and provides
    an interface for accessing generator field values across years.

    Args:
        model: The parent Model instance
        generator_name: The name of the generator

    Examples:
        >>> debt_gen = model.generator('debt')
        >>> debt_gen.field('principal')  # Returns dict of year: value for principal field
        >>> debt_gen.field('principal', 2024)  # Get principal value for 2024
        >>> debt_gen.to_dataframe()  # Returns DataFrame with all fields
    """

    def __init__(self, model: "Model", generator_name: str):
        self.model = model
        self._generator_name = generator_name

        # Validate that generator exists in the model
        if not any(gen.name == generator_name for gen in self.model.generators):
            raise KeyError(f"Generator '{generator_name}' not found in model")

        # Get the generator instance
        self._generator = next(
            gen for gen in self.model.generators if gen.name == generator_name
        )

    @property
    def name(self) -> str:
        """Get the generator name."""
        return self._generator_name

    @property
    def field_names(self) -> list[str]:
        """Get the list of field names defined by this generator."""
        return self._generator.defined_names

    def field(self, field_name: str, year: int = None) -> Dict[int, float] | float:
        """
        Get values for a specific field.

        Args:
            field_name: The name of the field to retrieve
            year: Optional year to get value for. If None, returns all years.

        Returns:
            Dictionary mapping years to values if year is None,
            or a single float value for the specified year.

        Raises:
            KeyError: If field_name is not defined by this generator or year not found
        """
        if field_name not in self.field_names:
            raise KeyError(
                f"Field '{field_name}' not found in generator '{self.name}'. "
                f"Available fields: {self.field_names}"
            )

        full_name = f"{self.name}.{field_name}"

        if year is None:
            # Return all years
            return {
                y: self.model._value_matrix[y][full_name]
                for y in self.model.years
            }
        else:
            # Return specific year
            if year not in self.model.years:
                raise KeyError(
                    f"Year {year} not found in model. Available years: {self.model.years}"
                )
            return self.model._value_matrix[year][full_name]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert generator field values to a pandas DataFrame.

        Returns:
            DataFrame with fields as rows and years as columns
        """
        data = {}
        for year in self.model.years:
            data[year] = [
                self.model._value_matrix[year][f"{self.name}.{field}"]
                for field in self.field_names
            ]

        return pd.DataFrame(data, index=self.field_names)

    def __repr__(self) -> str:
        return f"GeneratorResults(name='{self.name}', fields={self.field_names})"

    def __str__(self) -> str:
        return f"Generator: {self.name}\nFields: {', '.join(self.field_names)}"
