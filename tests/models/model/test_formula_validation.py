import pytest
from pyproforma import Model, LineItem, Category


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

# def test_formula_points_to_itself():
    
#     a = LineItem(
#         name='a',
#         category='test',
#         values={2023: 10, 2024: 20}
#     )
#     b = LineItem(
#         name='b',
#         category='test',
#         formula='b[0]',
#         values={2023: 10}
#     )
#     model = Model(
#         line_items=[a, b],
#         years=[2023, 2024]
#     )


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

