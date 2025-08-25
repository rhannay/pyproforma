import pytest

from pyproforma import LineItem, Model


def test_simple_model_with_formulas_works():

    """Test that a simple model with line items and formulas works correctly."""
    # Line item with values
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )

    # Line item with formula that references 'a'
    b = LineItem(
        name='b',
        category='test',
        formula='a * 2'
    )

    # Create model
    model = Model(
        line_items=[a, b],
        years=[2023, 2024]
    )

    # Test the values are calculated correctly
    assert model['a', 2023] == 10
    assert model['a', 2024] == 20

    assert model['b', 2023] == 20  # 10 * 2
    assert model['b', 2024] == 40  # 20 * 2


def test_formula_error_raises_with_undefined_line_item():
    """Test that a formula referencing an undefined line item raises an error with the correct message."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='c * 2'
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Formula contains undefined line item names: c" in str(excinfo.value)

def test_formula_points_to_itself():
    """Test that a formula referencing itself without time offset raises a circular reference error."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='b',
        values={2023: 10}
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Circular reference detected: formula for 'b' references itself without a time offset" in str(excinfo.value)


def test_formula_points_to_itself_with_zero_offset():
    """Test that a formula referencing itself with [0] time offset raises a circular reference error."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='b[0] + 5',
        values={2023: 10}
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Circular reference detected: formula for 'b' references itself with [0] time offset" in str(excinfo.value)


def test_formula_with_positive_offset_raises_error():
    """Test that a formula with positive time offset raises an error."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='a[1] + 5'
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Future time references are not allowed: a[1]" in str(excinfo.value)


def test_formula_error_raises_with_two_undefined_line_items():
    """Test that a formula referencing two undefined line items raises an error with the correct message."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='c + d'
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Formula contains undefined line item names: c, d" in str(excinfo.value)

def test_error_future_offset():
    """Test that a formula with future time offset raises an error with enhanced error message."""
    a = LineItem(
        name='a',
        category='test',
        values={2023: 10, 2024: 20}
    )
    b = LineItem(
        name='b',
        category='test',
        formula='a[1] * 2'
    )
    with pytest.raises(ValueError) as excinfo:
        Model(
            line_items=[a, b],
            years=[2023, 2024]
        )
    assert "Error in formula for line item 'b': Future time references are not allowed: a[1]" in str(excinfo.value)

# def test_misc():
#     """Test that a formula with future time offset raises an error with enhanced error message."""
#     formula = 'a * 2'
#     validate_formula(formula, 'b', ['a', 'b'])
#     a = LineItem(
#         name='a',
#         category='test',
#         values={2023: 10, 2024: 20}
#     )
#     b = LineItem(
#         name='b',
#         category='test',
#         formula=formula
#     )
#     Model(
#         line_items=[a, b],
#         years=[2023, 2024]
#     )
