import pytest

from pyproforma.models.model.value_matrix import (
    ValueMatrixValidationError,
    validate_value_matrix,
)


class TestValidateValueMatrix:
    def test_empty_values_by_year(self):
        """Empty dictionary should be valid."""
        # Should not raise any exception
        validate_value_matrix({})

    def test_single_year(self):
        """Dictionary with a single year should be valid."""
        values = {2023: {"revenue": 1000, "expenses": 800, "profit": 200}}
        # Should not raise any exception
        validate_value_matrix(values)

    def test_multiple_years_same_keys(self):
        """Multiple years with identical keys should be valid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "expenses": 850, "profit": 250},
            2025: {"revenue": 1200, "expenses": 900, "profit": 300},
        }
        # Should not raise any exception
        validate_value_matrix(values)

    def test_last_year_subset_keys(self):
        """Last year with a subset of keys should be valid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "expenses": 850, "profit": 250},
            2025: {"revenue": 1200, "expenses": 900},  # Missing "profit"
        }
        # Should not raise any exception
        validate_value_matrix(values)

    def test_non_integer_keys(self):
        """Dictionary with non-integer keys should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            "2024": {"revenue": 1100, "expenses": 850},  # String key
        }
        with pytest.raises(
            ValueMatrixValidationError, match="integers representing years"
        ):
            validate_value_matrix(values)

    def test_unordered_years(self):
        """Dictionary with unordered years should be invalid."""
        values = {
            2024: {"revenue": 1100, "expenses": 850},
            2023: {"revenue": 1000, "expenses": 800},  # Out of order
        }
        with pytest.raises(ValueMatrixValidationError, match="ascending order"):
            validate_value_matrix(values)

    def test_non_dict_values(self):
        """Dictionary with non-dict values should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            2024: [1100, 850],  # List instead of dict
        }
        with pytest.raises(ValueMatrixValidationError, match="must be dictionaries"):
            validate_value_matrix(values)

    def test_inconsistent_keys_middle_year(self):
        """Middle year with different keys should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "profit": 250},  # Missing "expenses"
            2025: {"revenue": 1200, "expenses": 900, "profit": 300},
        }
        with pytest.raises(
            ValueMatrixValidationError, match="inconsistent variable names"
        ):
            validate_value_matrix(values)

    def test_last_year_extra_key(self):
        """Last year with an extra key should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            2024: {"revenue": 1100, "expenses": 850},
            2025: {"revenue": 1200, "expenses": 900, "new_metric": 50},  # Extra key
        }
        with pytest.raises(
            ValueMatrixValidationError, match="Last year.*extra variables"
        ):
            validate_value_matrix(values)
