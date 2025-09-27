import pytest

from pyproforma.models.model.value_matrix import (
    ValueMatrixValidationError,
    calculate_line_item_value,
)


class TestCalculateLineItemValue:
    def test_calculate_line_item_value_no_formula(self):
        hardcoded_values = {2020: 1.0, 2021: 2.0}
        vals = {}
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2020, "test_item")
            == 1.0
        )
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2021, "test_item")
            == 2.0
        )

        # Should return None when no value and no formula
        result = calculate_line_item_value(
            hardcoded_values, None, vals, 2022, "test_item"
        )
        assert result is None

    def test_calculate_line_item_value_with_formula(self):
        hardcoded_values = {2020: 1.0, 2021: 2.0}
        formula = "test_item[-1] * 1.05"
        vals = {}
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2020, "test_item"
            )
            == 1.0
        )
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2021, "test_item"
            )
            == 2.0
        )
        vals = {2021: {"test_item": 2.0}}
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2022, "test_item"
            )
            == 2.0 * 1.05
        )
        val = {2022: {"test_item": 2.1}}
        assert (
            calculate_line_item_value(hardcoded_values, formula, val, 2023, "test_item")
            == 2.1 * 1.05
        )

        # Test for year referencing [-1] but previous value does not exist
        with pytest.raises(ValueError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2019, "test_item"
            )
        assert "2018 not found" in str(excinfo.value)

    def test_calculate_line_item_value_with_gap_in_years(self):
        hardcoded_values = {2020: 1.0, 2022: 2.0}
        formula = None
        vals = {}
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2020, "test_item"
            )
            == 1.0
        )

        # Should return None when no value and no formula
        result = calculate_line_item_value(
            hardcoded_values, formula, vals, 2021, "test_item"
        )
        assert result is None

        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2022, "test_item"
            )
            == 2.0
        )

        # add formula
        formula = "test_item[-1] * 1.05"
        vals = {2020: {"test_item": 2.0}}
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, vals, 2021, "test_item"
            )
            == 2.0 * 1.05
        )

    def test_calculate_line_item_value_formula_references_other_item(self):
        hardcoded_values = {2020: 3.0}
        formula = "item1 * 2"
        vals = {2021: {"item1": 5.0}}
        assert (
            calculate_line_item_value(hardcoded_values, formula, vals, 2021, "item2")
            == 5.0 * 2
        )

    def test_calculate_line_item_value_returns_none_from_values(self):
        """Test that None values now trigger formula usage when available."""
        hardcoded_values = {2020: 1.0, 2021: None, 2022: 3.0}
        vals = {}

        # Non-None values still work as before
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2020, "test_item")
            == 1.0
        )
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2022, "test_item")
            == 3.0
        )

        # None value with no formula returns None
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2021, "test_item")
            is None
        )

        # None value with formula should use formula
        formula = "test_item[-1] * 2"
        vals_with_prev = {2020: {"test_item": 1.0}}
        result = calculate_line_item_value(
            hardcoded_values, formula, vals_with_prev, 2021, "test_item"
        )
        assert result == 2.0  # 1.0 * 2

    def test_calculate_line_item_value_none_in_formula_treated_as_zero(self):
        """Test that None values in formulas are treated as zero."""
        from pyproforma.models.formula import evaluate

        # Test with None value in value matrix - should treat None as 0
        value_matrix = {2023: {"revenue": None, "costs": 100}}

        result = evaluate("revenue + costs", value_matrix, 2023)
        assert result == 100  # None (treated as 0) + 100 = 100

        # Test with offset reference to None value - should treat None as 0
        value_matrix = {2022: {"revenue": None}, 2023: {"revenue": 100, "costs": 50}}

        result = evaluate("revenue[-1] + costs", value_matrix, 2023)
        assert result == 50  # None (treated as 0) + 50 = 50

        # Test multiple None values
        value_matrix = {2023: {"revenue": None, "costs": None, "other": 25}}

        result = evaluate("revenue + costs + other", value_matrix, 2023)
        assert result == 25  # 0 + 0 + 25 = 25


class TestCalculateLineItemValueValidation:
    """Test validation of interim_values_by_year in calculate_line_item_value."""

    def test_calculate_line_item_value_validates_interim_values_non_integer_keys(
        self,
    ):
        """Test that calculate_line_item_value validates interim_values_by_year has
        integer keys."""
        hardcoded_values = {2020: 100.0}

        # Invalid: non-integer keys
        invalid_interim_values = {"2020": {"other_item": 50.0}}

        with pytest.raises(ValueMatrixValidationError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, invalid_interim_values, 2020, "test_item"
            )
        assert "All keys must be integers representing years" in str(excinfo.value)

    def test_calculate_line_item_value_validates_interim_values_by_year_unordered_years(
        self,
    ):
        """Test that calculate_line_item_value validates interim_values_by_year has
        years in ascending order."""
        hardcoded_values = {2020: 100.0}

        # Invalid: years not in ascending order
        invalid_interim_values = {
            2022: {"other_item": 50.0},
            2020: {"another_item": 25.0},
        }

        with pytest.raises(ValueMatrixValidationError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, invalid_interim_values, 2020, "test_item"
            )
        assert "Years must be in ascending order" in str(excinfo.value)

    def test_calculate_line_item_value_validates_interim_values_by_year_non_dict_values(
        self,
    ):
        """Test that calculate_line_item_value validates interim_values_by_year
        has dict values."""
        hardcoded_values = {2020: 100.0}

        # Invalid: values are not dictionaries
        invalid_interim_values = {2020: "not_a_dict"}

        with pytest.raises(ValueMatrixValidationError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, invalid_interim_values, 2020, "test_item"
            )
        assert "Values for years [2020] must be dictionaries" in str(excinfo.value)

    def test_calculate_line_item_value_validates_interim_values_inconsistent_keys(
        self,
    ):
        """Test validation of consistent variable names across years."""
        hardcoded_values = {2020: 100.0}

        # Invalid: inconsistent variable names between years
        invalid_interim_values = {
            2020: {"var1": 10.0, "var2": 20.0},
            2021: {"var1": 15.0, "var3": 25.0},  # var2 missing, var3 extra
            2022: {"var1": 20.0},  # last year can be subset
        }

        with pytest.raises(ValueMatrixValidationError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, invalid_interim_values, 2020, "test_item"
            )
        assert "Year 2021 has inconsistent variable names" in str(excinfo.value)

    def test_calculate_line_item_value_validates_extra_keys_in_last_year(
        self,
    ):
        """Test validation that last year doesn't have extra variables."""
        hardcoded_values = {2020: 100.0}

        # Invalid: last year has extra variables not in previous years
        invalid_interim_values = {
            2020: {"var1": 10.0},
            2021: {"var1": 15.0, "var2": 25.0},  # var2 is extra
        }

        with pytest.raises(ValueMatrixValidationError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, invalid_interim_values, 2020, "test_item"
            )
        assert "Last year (2021) contains extra variables" in str(excinfo.value)

    def test_calculate_line_item_value_accepts_valid_interim_values_by_year(self):
        """Test that calculate_line_item_value accepts valid interim_values_by_year."""
        hardcoded_values = {2020: 100.0}

        # Valid interim values
        valid_interim_values = {
            2020: {"var1": 10.0, "var2": 20.0},
            2021: {"var1": 15.0, "var2": 25.0},
            2022: {"var1": 20.0},  # last year can be subset
        }

        # Should not raise an error
        result = calculate_line_item_value(
            hardcoded_values, None, valid_interim_values, 2020, "test_item"
        )
        assert result == 100.0

    def test_calculate_line_item_value_accepts_empty_interim_values_by_year(self):
        """Test that calculate_line_item_value accepts empty interim_values_by_year."""
        hardcoded_values = {2020: 100.0}

        # Empty interim values should be valid
        empty_interim_values = {}

        # Should not raise an error
        result = calculate_line_item_value(
            hardcoded_values, None, empty_interim_values, 2020, "test_item"
        )
        assert result == 100.0

    def test_calculate_line_item_value_duplicate_in_interim_values_raises_error(self):
        """Test error when value already exists in interim_values_by_year."""
        hardcoded_values = {2020: 100.0}
        interim_values = {2020: {"test_item": 50.0}}  # Already exists

        with pytest.raises(ValueError) as excinfo:
            calculate_line_item_value(
                hardcoded_values, None, interim_values, 2020, "test_item"
            )
        assert (
            "Value for test_item in year 2020 already exists in interim values"
            in str(excinfo.value)
        )


class TestCalculateLineItemValueNoneValues:
    """Test class for None value functionality in calculate_line_item_value."""

    def test_calculate_line_item_value_accepts_none_values(self):
        """Test that calculate_line_item_value can work with None values."""
        hardcoded_values = {2020: 100.0, 2021: None, 2022: 200.0}
        vals = {}

        # Non-None values work as before
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2020, "test_none")
            == 100.0
        )
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2022, "test_none")
            == 200.0
        )

        # None value with no formula returns None
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2021, "test_none")
            is None
        )

        # None value with formula should use formula
        formula = "test_none[-1] * 1.5"
        vals_with_prev = {2020: {"test_none": 100.0}}
        result = calculate_line_item_value(
            hardcoded_values, formula, vals_with_prev, 2021, "test_none"
        )
        assert result == 150.0  # 100.0 * 1.5

    def test_calculate_line_item_value_all_none_values(self):
        """Test calculate_line_item_value with all None values."""
        hardcoded_values = {2020: None, 2021: None, 2022: None}
        vals = {}

        # None values with no formula return None
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2020, "all_none")
            is None
        )
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2021, "all_none")
            is None
        )
        assert (
            calculate_line_item_value(hardcoded_values, None, vals, 2022, "all_none")
            is None
        )

        # None values with formula should use formula if previous values exist
        formula = "all_none[-1] * 2"
        vals_with_prev = {2019: {"all_none": 10.0}}
        result = calculate_line_item_value(
            hardcoded_values, formula, vals_with_prev, 2020, "all_none"
        )
        assert result == 20.0  # 10.0 * 2

    def test_calculate_line_item_value_returns_none_from_hardcoded_values(self):
        """Test that None values in hardcoded_values can return None."""
        hardcoded_values = {2020: 100.0, 2021: None, 2022: 200.0}

        interim_values = {}
        assert (
            calculate_line_item_value(
                hardcoded_values, None, interim_values, 2020, "none_test"
            )
            == 100.0
        )
        assert (
            calculate_line_item_value(
                hardcoded_values, None, interim_values, 2021, "none_test"
            )
            is None
        )
        assert (
            calculate_line_item_value(
                hardcoded_values, None, interim_values, 2022, "none_test"
            )
            == 200.0
        )

    def test_calculate_line_item_value_returns_none_when_no_data(self):
        """Test that calculate_line_item_value returns None when no value exists
        and no formula."""
        hardcoded_values = {}

        interim_values = {}
        result = calculate_line_item_value(
            hardcoded_values, None, interim_values, 2020, "empty"
        )
        assert result is None

    def test_calculate_line_item_value_formula_overrides_none_values(self):
        """Test that formulas work even when hardcoded_values dict contains None."""
        hardcoded_values = {2020: None}  # None in values
        formula = "test_item * 2"  # But has formula

        # Formula should be used since year not in values (None doesn't count as having a value)  # noqa: E501
        interim_values = {2021: {"test_item": 50.0}}
        result = calculate_line_item_value(
            hardcoded_values, formula, interim_values, 2021, "formula_test"
        )
        assert result == 100.0  # 50 * 2

    def test_calculate_line_item_value_mixed_none_and_formula_behavior(self):
        """Test complex scenario with None values and formulas."""
        hardcoded_values = {2020: 100.0, 2021: None, 2023: 300.0}  # Gap at 2022
        formula = "complex_test[-1] * 1.1"

        interim_values = {}

        # 2020: explicit value
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, interim_values, 2020, "complex_test"
            )
            == 100.0
        )

        # 2021: None value should now use formula, referencing 2020
        interim_values = {2020: {"complex_test": 100.0}}
        result_2021 = calculate_line_item_value(
            hardcoded_values, formula, interim_values, 2021, "complex_test"
        )
        assert result_2021 == pytest.approx(110.0)  # 100.0 * 1.1

        # 2022: no explicit value, should use formula with 2021 value
        interim_values = {2021: {"complex_test": 110.0}}
        result_2022 = calculate_line_item_value(
            hardcoded_values, formula, interim_values, 2022, "complex_test"
        )
        assert result_2022 == pytest.approx(121.0)  # 110.0 * 1.1

        # 2023: explicit value (should override formula)
        assert (
            calculate_line_item_value(
                hardcoded_values, formula, {}, 2023, "complex_test"
            )
            == 300.0
        )
