import pytest

from pyproforma import LineItem
from pyproforma.models.formula import calculate_formula


class DummyLineItemSet:
    def __getitem__(self, key):
        # key is a tuple: (var_name, year)
        var_name, year = key
        # Return dummy values for testing
        return {
            ("a", 2024): 10,
            ("b", 2024): 5,
            ("c", 2024): 2,
        }.get((var_name, year), 1)


sample_value_matrix = {
    2024: {"a": 10, "b": 5, "c": 2},
    2023: {"a": 8, "b": 4, "c": 1},
}


def test_lineitem_formula_init_with_label():
    f = LineItem(
        name="test", category="calculated", formula="a + b", label="Test Label"
    )
    assert f.name == "test"
    assert f.formula == "a + b"
    assert f.label == "Test Label"


def test_lineitem_formula_init_without_label():
    f = LineItem(name="test2", category="calculated", formula="b - c")
    assert f.name == "test2"
    assert f.formula == "b - c"
    assert f.label is None


def test_lineitem_formula_from_dict():
    data = {
        "name": "test3",
        "formula": "a * b",
        "label": "Test 3",
        "category": "calculated",
    }
    f = LineItem.from_dict(data)
    assert f.name == "test3"
    assert f.formula == "a * b"
    assert f.label == "Test 3"

    # No label provided
    data = {"name": "test3", "formula": "a * b", "category": "calculated"}
    f = LineItem.from_dict(data)
    assert f.name == "test3"
    assert f.formula == "a * b"
    assert f.label is None


def test_lineitem_formula_calc_simple_addition():
    # Test that LineItem with formula can calculate values through get_value
    from pyproforma.models.formula import calculate_formula

    f = LineItem(name="sum", category="calculated", formula="a + b")
    result = calculate_formula(f.formula, sample_value_matrix, 2024)
    assert result == 10 + 5


def test_lineitem_formula_calc_with_multiple_variables():
    from pyproforma.models.formula import calculate_formula

    f = LineItem(name="complex", category="calculated", formula="a * b + c")
    result = calculate_formula(f.formula, sample_value_matrix, 2024)
    assert result == 10 * 5 + 2


def test__calculate_formula_simple_addition():
    values_matrix = {2024: {"a": 10, "b": 5}}
    result = calculate_formula("a + b", values_matrix, 2024)
    assert result == 15.0


def test__calculate_formula_multiplication_and_addition():
    values_matrix = {2024: {"a": 2, "b": 3, "c": 4}}
    result = calculate_formula("a * b + c", values_matrix, 2024)
    assert result == 2 * 3 + 4


def test__calculate_formula_with_float_values():
    values_matrix = {2024: {"x": 1.5, "y": 2.5}}
    result = calculate_formula("x + y", values_matrix, 2024)
    assert result == 4.0


def test__calculate_formula_missing_year_raises_valueerror():
    values_matrix = {2023: {"a": 1}}
    with pytest.raises(ValueError):
        calculate_formula("a + 1", values_matrix, 2024)


def test__calculate_formula_missing_variable_raises_valueerror():
    values_matrix = {2024: {"a": 1}}
    with pytest.raises(ValueError):
        calculate_formula("a + b", values_matrix, 2024)


def test__calculate_formula_complex_expression():
    values_matrix = {2024: {"a": 2, "b": 3, "c": 4, "d": 5}}
    result = calculate_formula("(a + b) * (c - d)", values_matrix, 2024)
    assert result == (2 + 3) * (4 - 5)


def test__calculate_formula_with_negative_offset():
    values_matrix = {2024: {"a": 10, "b": 5}, 2023: {"a": 8, "b": 4}}
    result = calculate_formula("a[-1] + b", values_matrix, 2024)
    assert result == 8 + 5


def test__calculate_formula_with_invalid_formulas():
    values_matrix = {2024: {"a": 10, "b": 5}, 2023: {"a": 8, "b": 4}}
    with pytest.raises(SyntaxError):
        calculate_formula("a +", values_matrix, 2024)
    with pytest.raises(SyntaxError):
        calculate_formula("a + b -", values_matrix, 2024)
    # year offset out of range
    with pytest.raises(ValueError):
        calculate_formula("a[-2] + b", values_matrix, 2024)
    with pytest.raises(ValueError) as excinfo:
        calculate_formula(
            "a + c", values_matrix, 2024
        )  # c is not defined, should raise KeyError
    assert "'c' not found" in str(excinfo.value)
    # leading/trailing spaces in formula OK
    result = calculate_formula(" a  +  b ", values_matrix, 2024)
    assert result == 15.0  # should still work with extra spaces
    # extra spaces in the middle of the formula ok
    result = calculate_formula("a  +     b", values_matrix, 2024)
    assert result == 15.0  # should still work with extra spaces
    # positive offset
    with pytest.raises(ValueError):
        calculate_formula("a[2] + b", values_matrix, 2024)
    # Order of operations
    result = calculate_formula("a + b * 2", values_matrix, 2024)
    assert (
        result == 10 + 5 * 2
    )  # should respect order of operations (multiplication before addition)
    # Parentheses
    result = calculate_formula("(a + b) * 2", values_matrix, 2024)
    assert result == (10 + 5) * 2  # should respect parentheses
    # Nested parentheses
    result = calculate_formula("((a + b) * 2) + a", values_matrix, 2024)
    assert result == ((10 + 5) * 2) + 10  # should respect nested parentheses


def test__calculate_formula_with_parentheses_after_variable():
    """Test what happens when parentheses are used after a variable."""
    values_matrix = {2024: {"a": 10, "b": 5}, 2023: {"a": 8, "b": 4}}

    # Test with parentheses instead of square brackets
    # This causes a TypeError because a(-1) is interpreted as calling 'a' as a function
    # but 'a' is an integer (10), not a callable function
    with pytest.raises(TypeError, match="'int' object is not callable"):
        calculate_formula("a(-1) + b", values_matrix, 2024)

    # Test with multiple variables using parentheses
    with pytest.raises(TypeError, match="'int' object is not callable"):
        calculate_formula("a(-1) + b(-1)", values_matrix, 2024)

    # Test mixed usage - one with correct brackets, one with incorrect parentheses
    with pytest.raises(TypeError, match="'int' object is not callable"):
        calculate_formula("a[-1] + b(-1)", values_matrix, 2024)

    # Test just a variable with parentheses
    with pytest.raises(TypeError, match="'int' object is not callable"):
        calculate_formula("a(-1)", values_matrix, 2024)

    # For comparison, test that the correct square bracket syntax works
    result = calculate_formula("a[-1] + b", values_matrix, 2024)
    assert result == 8 + 5  # a[-1] is 8 (from 2023), b is 5 (from 2024)
