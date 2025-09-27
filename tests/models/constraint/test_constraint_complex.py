from pyproforma import Category, LineItem, Model
from pyproforma.models.constraint import Constraint
from pyproforma.models.multi_line_item.debt import Debt


class TestConstraintsWithComplexModels:
    """Test that constraints work correctly with complex models including line item generators."""  # noqa: E501

    def test_constraints_with_line_item_generators(self):
        """Test that constraints work with models that include line item generators."""
        line_items = [
            LineItem(
                name="revenue", category="income", values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="debt_service",
                category="expenses",
                formula="debt_principal + debt_interest",
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="expenses", label="Expenses"),
        ]

        line_item_generators = [
            Debt(name="debt", par_amount={2023: 50000}, interest_rate=0.05, term=10)
        ]

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
            ),
            Constraint(
                name="max_debt_service",
                line_item_name="debt_service",
                target=10000.0,
                operator="lt",
            ),
        ]

        model = Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories,
            multi_line_items=line_item_generators,
            constraints=constraints,
        )

        # Test that model functions correctly
        assert len(model.constraints) == 2
        assert len(model.multi_line_items) == 1
        assert len(model._line_item_definitions) == 2

        # Test that values can be accessed
        assert model.value("revenue", 2023) == 100000
        assert model.value("debt_principal", 2023) > 0
        assert model.value("debt_service", 2023) > 0

        # Test that constraints are preserved
        constraint_names = [c.name for c in model.constraints]
        assert "min_revenue" in constraint_names
        assert "max_debt_service" in constraint_names

    def test_constraints_with_formulas(self):
        """Test that constraints work with line items that have formulas."""
        line_items = [
            LineItem(
                name="base_revenue",
                category="income",
                values={2023: 100000, 2024: 110000},  # Added 2024 value
            ),
            LineItem(
                name="growth_rate",
                category="assumptions",
                values={2023: 0.05, 2024: 0.07},
            ),
            LineItem(
                name="projected_revenue",
                category="income",
                formula="base_revenue * (1 + growth_rate)",
            ),
            LineItem(
                name="net_income", category="calculated", formula="total_income * 0.8"
            ),
        ]

        constraints = [
            Constraint(
                name="min_net_income",
                line_item_name="net_income",
                target=80000.0,
                operator="gt",
            ),
            Constraint(
                name="reasonable_growth",
                line_item_name="growth_rate",
                target=0.10,
                operator="lt",
            ),
        ]

        model = Model(
            line_items=line_items, years=[2023, 2024], constraints=constraints
        )

        # Test that model functions correctly
        assert len(model.constraints) == 2

        # Test calculated values
        expected_projected_revenue_2023 = 100000 * (1 + 0.05)
        expected_total_income_2023 = 100000 + expected_projected_revenue_2023
        expected_net_income_2023 = expected_total_income_2023 * 0.8

        assert model.value("projected_revenue", 2023) == expected_projected_revenue_2023
        assert model.value("net_income", 2023) == expected_net_income_2023

        # Test that constraints are accessible
        assert model.constraints[0].name == "min_net_income"
        assert model.constraints[1].name == "reasonable_growth"

    def test_constraints_serialization_with_complex_model(self):
        """Test that serialization works with complex models including constraints."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000},
                formula="revenue[-1] * 1.05",
            ),
            LineItem(name="expenses", category="costs", formula="revenue * 0.6"),
        ]

        categories = [
            Category(name="income", label="Income", include_total=True),
            Category(name="costs", label="Costs", include_total=True),
        ]

        line_item_generators = [
            Debt(name="loan", par_amount={2023: 25000}, interest_rate=0.04, term=5)
        ]

        constraints = [
            Constraint(
                name="revenue_growth",
                line_item_name="revenue",
                target=95000.0,
                operator="gt",
            ),
            Constraint(
                name="expense_ratio",
                line_item_name="expenses",
                target=70000.0,
                operator="le",
            ),
        ]

        original_model = Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories,
            multi_line_items=line_item_generators,
            constraints=constraints,
        )

        # Test serialization and deserialization
        model_dict = original_model.to_dict()
        reconstructed_model = Model.from_dict(model_dict)

        # Verify all components are preserved
        assert len(reconstructed_model.constraints) == 2
        assert len(reconstructed_model.multi_line_items) == 1
        assert len(reconstructed_model._line_item_definitions) == 2
        assert (
            len(reconstructed_model._category_definitions) == 2
        )  # Multi-line items no longer create category definitions
        assert (
            len(reconstructed_model.category_metadata) == 4
        )  # 2 user categories + 1 multi-line item + 1 category_totals

        # Verify constraint details
        constraint_names = [c.name for c in reconstructed_model.constraints]
        assert "revenue_growth" in constraint_names
        assert "expense_ratio" in constraint_names

        # Verify model still calculates correctly
        assert reconstructed_model.value("revenue", 2023) == 100000
        assert reconstructed_model.value("expenses", 2023) == 60000

    def test_constraint_copy_with_complex_model(self):
        """Test that copying works correctly with complex models including constraints."""  # noqa: E501
        line_items = [
            LineItem(name="item1", category="cat1", values={2023: 1000}),
            LineItem(name="item2", category="cat2", values={2023: 2000}),
        ]

        constraints = [
            Constraint(
                name="copy_test",
                line_item_name="item1",
                target={2023: 1000, 2024: 1100},
                operator="eq",
            )
        ]

        model = Model(
            line_items=line_items, years=[2023, 2024], constraints=constraints
        )

        copied_model = model.copy()

        # Verify constraints are copied
        assert len(copied_model.constraints) == 1

        # Verify they are independent objects
        assert model.constraints[0] is not copied_model.constraints[0]

        # But have the same values
        assert copied_model.constraints[0].name == "copy_test"
        assert copied_model.constraints[0].target == {2023: 1000, 2024: 1100}
