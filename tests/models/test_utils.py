import pytest

from pyproforma.models._utils import check_interim_values_by_year, check_name


class TestCheckName:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("valid_name", True),
            ("anotherValidName123", True),
            ("", False),
            ("name with spaces", False),
            ("name-with-dash", True),
            ("name_with_underscore", True),
            ("name.with.dot", False),
            ("name$", False),
            ("123name", True),
            ("_leading_underscore", True),
            ("trailing_underscore_", True),
            ("name!", False),
        ],
    )
    def test_check_name(self, name, expected):
        assert check_name(name) == expected


class TestCheckInterimValuesByYear:
    def test_empty_values_by_year(self):
        """Empty dictionary should be valid."""
        result, error = check_interim_values_by_year({})
        assert result is True
        assert error is None

    def test_single_year(self):
        """Dictionary with a single year should be valid."""
        values = {2023: {"revenue": 1000, "expenses": 800, "profit": 200}}
        result, error = check_interim_values_by_year(values)
        assert result is True
        assert error is None

    def test_multiple_years_same_keys(self):
        """Multiple years with identical keys should be valid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "expenses": 850, "profit": 250},
            2025: {"revenue": 1200, "expenses": 900, "profit": 300},
        }
        result, error = check_interim_values_by_year(values)
        assert result is True
        assert error is None

    def test_last_year_subset_keys(self):
        """Last year with a subset of keys should be valid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "expenses": 850, "profit": 250},
            2025: {"revenue": 1200, "expenses": 900},  # Missing "profit"
        }
        result, error = check_interim_values_by_year(values)
        assert result is True
        assert error is None

    def test_non_integer_keys(self):
        """Dictionary with non-integer keys should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            "2024": {"revenue": 1100, "expenses": 850},  # String key
        }
        result, error = check_interim_values_by_year(values)
        assert result is False
        assert "integers representing years" in error

    def test_unordered_years(self):
        """Dictionary with unordered years should be invalid."""
        values = {
            2024: {"revenue": 1100, "expenses": 850},
            2023: {"revenue": 1000, "expenses": 800},  # Out of order
        }
        result, error = check_interim_values_by_year(values)
        assert result is False
        assert "ascending order" in error

    def test_non_dict_values(self):
        """Dictionary with non-dict values should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            2024: [1100, 850],  # List instead of dict
        }
        result, error = check_interim_values_by_year(values)
        assert result is False
        assert "must be dictionaries" in error
        assert "2024" in error

    def test_inconsistent_keys_middle_year(self):
        """Middle year with different keys should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800, "profit": 200},
            2024: {"revenue": 1100, "profit": 250},  # Missing "expenses"
            2025: {"revenue": 1200, "expenses": 900, "profit": 300},
        }
        result, error = check_interim_values_by_year(values)
        assert result is False
        assert "inconsistent variable names" in error
        assert "2024" in error
        assert "missing: expenses" in error

    def test_last_year_extra_key(self):
        """Last year with an extra key should be invalid."""
        values = {
            2023: {"revenue": 1000, "expenses": 800},
            2024: {"revenue": 1100, "expenses": 850},
            2025: {"revenue": 1200, "expenses": 900, "new_metric": 50},  # Extra key
        }
        result, error = check_interim_values_by_year(values)
        assert result is False
        assert "Last year" in error
        assert "new_metric" in error
