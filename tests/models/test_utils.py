import pytest

from pyproforma.models._utils import validate_name, validate_periods


class TestValidateName:
    @pytest.mark.parametrize(
        "name",
        [
            "valid_name",
            "anotherValidName123",
            "name-with-dash",
            "name_with_underscore",
            "123name",
            "_leading_underscore",
            "trailing_underscore_",
        ],
    )
    def test_validate_name_valid_names(self, name):
        # Should not raise an exception for valid names
        validate_name(name)

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "name with spaces",
            "name.with.dot",
            "name$",
            "name!",
        ],
    )
    def test_validate_name_invalid_names(self, name):
        # Should raise ValueError for invalid names
        with pytest.raises(
            ValueError, match="Name must only contain letters, numbers, underscores"
        ):
            validate_name(name)


class TestValidatePeriods:
    """Test the validate_periods function."""

    def test_valid_integer_periods(self):
        """Test that valid integer periods are returned sorted."""
        result = validate_periods([2023, 2024, 2025])
        assert result == [2023, 2024, 2025]

    def test_valid_integer_periods_unsorted(self):
        """Test that unsorted integer periods are returned sorted."""
        result = validate_periods([2025, 2023, 2024])
        assert result == [2023, 2024, 2025]

    def test_string_periods_converted_to_integers(self):
        """Test that string periods are converted to integers."""
        result = validate_periods(['2023', '2024', '2025'])
        assert result == [2023, 2024, 2025]

    def test_mixed_string_and_integer_periods(self):
        """Test that mixed string and integer periods work correctly."""
        result = validate_periods([2023, '2024', 2025])
        assert result == [2023, 2024, 2025]

    def test_single_period(self):
        """Test that a single period works correctly."""
        result = validate_periods([2023])
        assert result == [2023]

    def test_single_period_as_string(self):
        """Test that a single period as string works correctly."""
        result = validate_periods(['2023'])
        assert result == [2023]

    def test_negative_years(self):
        """Test that negative years are handled correctly."""
        result = validate_periods([-1, 0, 1])
        assert result == [-1, 0, 1]

    def test_negative_years_as_strings(self):
        """Test that negative years as strings are handled correctly."""
        result = validate_periods(['-1', '0', '1'])
        assert result == [-1, 0, 1]

    def test_duplicate_periods_raise_error(self):
        """Test that duplicate periods raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_periods([2023, 2024, 2023])

        error_msg = str(exc_info.value)
        assert "Duplicate years not allowed" in error_msg
        assert "2023" in error_msg

    def test_multiple_duplicates_raise_error(self):
        """Test that multiple duplicates are all reported."""
        with pytest.raises(ValueError) as exc_info:
            validate_periods([2023, 2024, 2023, 2025, 2024])

        error_msg = str(exc_info.value)
        assert "Duplicate years not allowed" in error_msg
        assert "2023" in error_msg
        assert "2024" in error_msg

    def test_invalid_string_raises_error(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_periods(['invalid'])

        error_msg = str(exc_info.value)
        assert "Invalid year" in error_msg
        assert "invalid" in error_msg

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_periods([2023, 2024.5])

        error_msg = str(exc_info.value)
        assert "Period must be an integer or string" in error_msg
        assert "float" in error_msg

    def test_none_periods_raise_type_error(self):
        """Test that None as periods raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            validate_periods(None)

        error_msg = str(exc_info.value)
        assert "Periods cannot be None" in error_msg

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_periods([])

        error_msg = str(exc_info.value)
        assert "Periods list cannot be empty" in error_msg

    def test_fill_in_periods_fills_gaps(self):
        """Test that fill_in_periods=True fills in missing years."""
        result = validate_periods([2023, 2025, 2027], fill_in_periods=True)
        assert result == [2023, 2024, 2025, 2026, 2027]

    def test_fill_in_periods_with_no_gaps(self):
        """Test that fill_in_periods=True works when there are no gaps."""
        result = validate_periods([2023, 2024, 2025], fill_in_periods=True)
        assert result == [2023, 2024, 2025]

    def test_fill_in_periods_single_year(self):
        """Test that fill_in_periods=True works with single year."""
        result = validate_periods([2023], fill_in_periods=True)
        assert result == [2023]

    def test_fill_in_periods_with_strings(self):
        """Test that fill_in_periods=True works with string periods."""
        result = validate_periods(['2023', '2025'], fill_in_periods=True)
        assert result == [2023, 2024, 2025]

    def test_fill_in_periods_unsorted_input(self):
        """Test that fill_in_periods=True works with unsorted input."""
        result = validate_periods([2027, 2023, 2025], fill_in_periods=True)
        assert result == [2023, 2024, 2025, 2026, 2027]

    def test_fill_in_periods_negative_years(self):
        """Test that fill_in_periods=True works with negative years."""
        result = validate_periods([-2, 2], fill_in_periods=True)
        assert result == [-2, -1, 0, 1, 2]

    def test_very_large_years(self):
        """Test that very large years work correctly."""
        result = validate_periods([9998, 9999, 10000])
        assert result == [9998, 9999, 10000]

    def test_zero_year(self):
        """Test that year zero is handled correctly."""
        result = validate_periods([-1, 0, 1])
        assert result == [-1, 0, 1]
