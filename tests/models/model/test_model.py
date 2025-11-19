import pytest

from pyproforma import Category, LineItem, Model
from pyproforma.models.constraint import Constraint
from pyproforma.models.generator.debt import Debt


class TestItemTypeValidation:
    def test_item_type_created_if_not_provided(self):
        li_set = Model(
            line_items=[
                LineItem(
                    name="item1",
                    label="Item 1",
                    category="revenue",
                    values={2020: 100.0},
                )
            ],
            years=[2020],
        )
        assert len(li_set._category_definitions) == 1
        assert li_set._category_definitions[0].name == "revenue"

    def test_item_type_auto_added(self):
        # Test that missing categories from line items are automatically added
        # to the provided categories
        model = Model(
            line_items=[
                LineItem(
                    name="item1",
                    label="Item 1",
                    category="expense",
                    values={2020: 100.0},
                )
            ],
            categories=[Category(name="revenue")],
            years=[2020],
        )

        # Should have both the provided category and the auto-added one
        assert len(model._category_definitions) == 2
        category_names = [cat.name for cat in model._category_definitions]
        assert "revenue" in category_names  # Provided category
        assert "expense" in category_names  # Auto-added from line item


class TestLineItemsWithFormulas:
    @pytest.fixture
    def sample_line_item_set_2(self) -> Model:
        # Create a sample Model with LineItems and Formulas
        rev_1 = LineItem(
            name="rev_1",
            label="Item 1",
            category="revenue",
            values={2020: 300.0},
            formula="rev_1[-1] * 1.05",
        )
        rev_2 = LineItem(
            name="rev_2",
            label="Item 2",
            category="revenue",
            values={2020: 100.0},
            formula="rev_2[-1] + 50.0",
        )
        exp_1 = LineItem(
            name="exp_1",
            label="Item 3",
            category="expense",
            values={2020: 200.0},
            formula="exp_1[-1] * 0.95",
        )

        categories = [
            Category(name="expense"),
            Category(name="revenue"),
            Category(name="calculated"),
        ]

        # Convert formulas to LineItems
        net_revenue = LineItem(
            name="net_revenue",
            label="Net Revenue",
            category="calculated",
            formula="rev_1 + rev_2 - exp_1",
        )

        return Model(
            line_items=[rev_1, rev_2, exp_1, net_revenue],
            categories=categories,
            years=[2020, 2021, 2022],
        )

    def test_line_item_set_init(self, sample_line_item_set_2: Model):
        # Check the Model initialization
        assert isinstance(sample_line_item_set_2, Model)
        assert (
            len(sample_line_item_set_2._line_item_definitions) == 4
        )  # Now includes the formula as a LineItem
        assert (
            len(sample_line_item_set_2._category_definitions) == 3
        )  # Added 'calculated' category
        assert sample_line_item_set_2.years == [2020, 2021, 2022]

        assert sample_line_item_set_2["rev_1"].value(2020) == 300.0
        assert sample_line_item_set_2["rev_1"].value(2021) == 300.0 * 1.05
        assert sample_line_item_set_2["rev_1"].value(2022) == 300.0 * 1.05 * 1.05
        assert sample_line_item_set_2["rev_2"].value(2020) == 100.0
        assert sample_line_item_set_2["rev_2"].value(2021) == 100.0 + 50.0
        assert sample_line_item_set_2["rev_2"].value(2022) == 100.0 + 50.0 + 50.0
        assert sample_line_item_set_2["exp_1"].value(2020) == 200.0
        assert sample_line_item_set_2["exp_1"].value(2021) == 200.0 * 0.95
        assert sample_line_item_set_2["exp_1"].value(2022) == 200.0 * 0.95 * 0.95
        assert sample_line_item_set_2["net_revenue"].value(2020) == 200.0
        assert sample_line_item_set_2["net_revenue"].value(2021) == (
            300.0 * 1.05 + 100.0 + 50.0
        ) - (200.0 * 0.95)
        assert sample_line_item_set_2["net_revenue"].value(2022) == (
            300.0 * 1.05 * 1.05 + 100.0 + 50.0 + 50.0
        ) - (200.0 * 0.95 * 0.95)


class TestModelWithBalanceSheetConcept:
    @pytest.fixture
    def sample_line_item_set(self) -> Model:
        rev_1 = LineItem(
            name="rev_1",
            label="Item 1",
            category="revenue",
            values={2020: 300.0, 2021: 400.0},
        )
        rev_2 = LineItem(
            name="rev_2",
            label="Item 2",
            category="revenue",
            values={2020: 100.0, 2021: 200.0},
        )
        exp_1 = LineItem(
            name="exp_1",
            label="Item 3",
            category="expense",
            values={2020: 200.0, 2021: 300.0},
        )
        begin_cash = LineItem(
            name="begin_cash",
            label="Beginning Cash",
            category="balance",
            values={2020: 1000.0},
            formula="end_cash[-1]",
        )
        end_cash = LineItem(
            name="end_cash",
            label="Ending Cash",
            category="balance",
            values={},
            formula="begin_cash + rev_1 + rev_2 - exp_1",
        )

        return Model(
            line_items=[rev_1, rev_2, exp_1, begin_cash, end_cash],
            # balance_sheet_line_items=[begin_cash, end_cash],
            years=[2020, 2021],
        )

    def test_line_item_set_init(self, sample_line_item_set: Model):
        assert sample_line_item_set.value("rev_1", 2020) == 300.0
        expected_end_cash_2020 = 1000.0 + 300.0 + 100.0 - 200.0
        assert sample_line_item_set.value("end_cash", 2020) == expected_end_cash_2020
        assert sample_line_item_set.value("begin_cash", 2021) == expected_end_cash_2020
        expected_end_cash_2021 = expected_end_cash_2020 + 400.0 + 200.0 - 300.0
        assert sample_line_item_set.value("end_cash", 2021) == expected_end_cash_2021


class TestSetWithAssumptions:
    def test_with_assumption_init(self):
        liset = Model(
            line_items=[
                LineItem(
                    name="revenue", category="revenue", values={2020: 100, 2021: 200}
                ),
                LineItem(name="rate_increase", category="assumption"),
            ],
            years=[2020, 2021],
        )
        assert isinstance(liset, Model)
        defined_names = [x["name"] for x in liset.line_item_metadata]
        assert "rate_increase" in defined_names

    def test_assumption_in_value_matrix(self):
        liset = Model(
            line_items=[
                LineItem(
                    name="revenue",
                    category="revenue",
                    values={2020: 100, 2021: 200, 2022: 300},
                ),
                LineItem(
                    name="rate_increase",
                    category="assumption",
                    values={2020: 0.05, 2021: 0.07},
                ),
            ],
            years=[2020, 2021, 2022],
        )
        value_matrix = liset._value_matrix
        assert "rate_increase" in value_matrix[2020]
        assert value_matrix[2020]["rate_increase"] == 0.05
        assert liset.value("rate_increase", 2020) == 0.05
        assert liset.value("rate_increase", 2021) == 0.07
        assert liset.value("rate_increase", 2022) is None

    def test_line_item_uses_assumption(self):
        liset = Model(
            line_items=[
                LineItem(
                    name="revenue",
                    category="revenue",
                    values={2020: 100},
                    formula="revenue[-1] * (1 + rate_increase)",
                ),
                LineItem(
                    name="rate_increase",
                    category="assumption",
                    values={2021: 0.05, 2022: 0.07},
                ),
            ],
            years=[2020, 2021, 2022],
        )
        value_matrix = liset._value_matrix
        assert value_matrix[2020]["revenue"] == 100.0
        assert value_matrix[2021]["revenue"] == 100 * 1.05
        assert value_matrix[2022]["revenue"] == 100 * 1.05 * 1.07


class TestModelWithGenerators:
    @pytest.fixture
    def sample_line_item_set_with_generators(self) -> Model:
        # Create a sample Model with LineItems and LineItemGenerators
        p = LineItem(
            name="principal",
            category="debt_service",
            values={2020: 300.0},
            formula="debt: principal",
        )
        i = LineItem(
            name="interest",
            category="debt_service",
            values={2020: 100.0},
            formula="debt: interest",
        )
        debt = Debt(name="debt", par_amount={2021: 1000.0}, interest_rate=0.05, term=30)
        return Model(
            line_items=[p, i], years=[2020, 2021, 2022], generators=[debt]
        )

    def test_line_item_set_with_generators(
        self, sample_line_item_set_with_generators: Model
    ):
        lis = sample_line_item_set_with_generators
        ds_schedule = Debt.generate_debt_service_schedule(1000.0, 0.05, 2021, 30)

        assert isinstance(lis, Model)
        assert lis.generator("debt").field("principal", 2020) == 0
        assert lis.generator("debt").field("principal", 2021) == ds_schedule[0]["principal"]
        assert lis.generator("debt").field("principal", 2022) == ds_schedule[1]["principal"]
        assert lis.value("principal", 2020) == 300.0
        assert lis.value("principal", 2021) == ds_schedule[0]["principal"]
        assert lis.value("principal", 2022) == ds_schedule[1]["principal"]
        assert lis.generator("debt").field("interest", 2020) == 0
        assert lis.generator("debt").field("interest", 2021) == ds_schedule[0]["interest"]
        assert lis.generator("debt").field("interest", 2022) == ds_schedule[1]["interest"]
        assert lis.value("interest", 2020) == 100.0
        assert lis.value("interest", 2021) == ds_schedule[0]["interest"]
        assert lis.value("interest", 2022) == ds_schedule[1]["interest"]


class TestOtherMisc:
    def test_line_item_set_get_item(self, sample_line_item_set: Model):
        # assert item values by year
        assert sample_line_item_set["item1"].value(2020) == 100.0
        assert sample_line_item_set["item2"].value(2021) == 75.0

        # check categories
        sorted_1 = sorted(
            sample_line_item_set._category_definitions, key=lambda x: x.name
        )
        assert sorted_1[0].name == "expense"
        assert sorted_1[1].name == "revenue"

        with pytest.raises(KeyError) as excinfo:
            sample_line_item_set["item4"].value(2020)
        assert "not found" in str(excinfo.value)

        with pytest.raises(KeyError) as excinfo:
            sample_line_item_set["item1"].value(2022)
        assert "Year 2022 not found" in str(excinfo.value)

    def test_getitem_string_returns_line_item_results(
        self, sample_line_item_set: Model
    ):
        """Test that __getitem__ with string key returns LineItemResults object."""
        from pyproforma.models.results import LineItemResults

        # Test string key returns LineItemResults
        result = sample_line_item_set["item1"]
        assert isinstance(result, LineItemResults)
        assert result.name == "item1"
        assert result.source_type == "line_item"

        # Test that it's equivalent to line_item() method
        line_item_result = sample_line_item_set.line_item("item1")
        assert isinstance(result, type(line_item_result))
        assert result.name == line_item_result.name
        assert result.source_type == line_item_result.source_type

        # Test with different item
        result2 = sample_line_item_set["item2"]
        assert isinstance(result2, LineItemResults)
        assert result2.name == "item2"

        # Test invalid item name raises KeyError
        with pytest.raises(KeyError):
            sample_line_item_set["nonexistent"]

        # Test invalid key type raises TypeError
        with pytest.raises(TypeError) as excinfo:
            sample_line_item_set[123]
        assert "Key must be a string item_name" in str(excinfo.value)

    def test_is_last_item_in_category(self):
        sample = Model(
            line_items=[
                LineItem(name="item1", category="revenue", values={2020: 100.0}),
                LineItem(name="item2", category="expense", values={2020: 200.0}),
                LineItem(name="item3", category="revenue", values={2020: 100.0}),
                LineItem(name="item4", category="expense", values={2020: 150.0}),
            ],
            categories=[Category(name="revenue"), Category(name="expense")],
            years=[2020],
        )

        # Test if the last item in a category is identified correctly
        assert sample._is_last_item_in_category("item1") is False
        assert sample._is_last_item_in_category("item2") is False
        assert sample._is_last_item_in_category("item3") is True
        assert sample._is_last_item_in_category("item4") is True

    def test_get_item_info(self):
        sample = Model(
            line_items=[
                LineItem(name="item1", category="revenue", values={2020: 100.0}),
                LineItem(name="item2", category="expense", values={2020: 200.0}),
                LineItem(
                    name="growth_rate",
                    label="Growth Rate",
                    category="assumption",
                    value_format="two_decimals",
                ),
            ],
            categories=[
                Category(name="revenue"),
                Category(name="expense"),
                Category(name="assumption"),
            ],
            years=[2020],
        )

        # Test getting item info for line item
        item_info = sample._get_item_metadata("item1")
        assert item_info["name"] == "item1"
        assert item_info["source_type"] == "line_item"
        assert item_info["source_name"] == "item1"

        # Test getting item info for assumption
        assumption_info = sample._get_item_metadata("growth_rate")
        assert assumption_info["name"] == "growth_rate"
        assert assumption_info["label"] == "Growth Rate"
        assert assumption_info["value_format"] == "two_decimals"
        assert assumption_info["source_type"] == "line_item"

        # Test KeyError for non-existent item
        with pytest.raises(KeyError) as excinfo:
            sample._get_item_metadata("non_existent_item")
        assert "not found in model" in str(excinfo.value)


class TestModelWithConstraints:
    """Test that Model works correctly with constraints."""

    @pytest.fixture
    def sample_model_with_constraints(self) -> Model:
        """Create a sample model with constraints for testing."""
        line_items = [
            LineItem(
                name="revenue", category="income", values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses", category="costs", values={2023: 50000, 2024: 60000}
            ),
        ]

        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs"),
        ]

        return Model(line_items=line_items, years=[2023, 2024], categories=categories)

    def test_model_initialization_with_constraints(
        self, sample_model_with_constraints: Model
    ):
        """Test that model can be initialized with constraints."""

        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt",
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=70000.0,
                operator="le",
            ),
        ]

        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints,
        )

        assert len(model.constraints) == 2
        assert model.constraints[0].name == "min_revenue"
        assert model.constraints[1].name == "max_expenses"

        # Test that model still functions normally
        assert model.value("revenue", 2023) == 100000
        assert model.value("expenses", 2024) == 60000

    def test_constraints_preserved_during_copy(
        self, sample_model_with_constraints: Model
    ):
        """Test that constraints are preserved when copying a model."""

        constraints = [
            Constraint(
                name="revenue_constraint",
                line_item_name="revenue",
                target=50000.0,
                operator="gt",
            )
        ]

        original_model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints,
        )

        copied_model = original_model.copy()

        # Check that constraints are copied
        assert len(copied_model.constraints) == 1
        assert copied_model.constraints[0].name == "revenue_constraint"

        # Check that they are independent objects
        assert original_model.constraints[0] is not copied_model.constraints[0]

    def test_constraints_in_serialization(self, sample_model_with_constraints: Model):
        """Test that constraints are included in serialization."""

        constraints = [
            Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=90000.0,
                operator="ge",
            )
        ]

        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints,
        )

        # Test to_dict
        model_dict = model.to_dict()
        assert "constraints" in model_dict
        assert len(model_dict["constraints"]) == 1
        assert model_dict["constraints"][0]["name"] == "test_constraint"

        # Test from_dict
        reconstructed_model = Model.from_dict(model_dict)
        assert len(reconstructed_model.constraints) == 1
        assert reconstructed_model.constraints[0].name == "test_constraint"

        # Test to_yaml
        yaml_str = model.to_yaml()
        assert "constraints:" in yaml_str
        assert "test_constraint" in yaml_str

        # Test from_yaml
        yaml_model = Model.from_yaml(yaml_str=yaml_str)

        assert len(yaml_model.constraints) == 1
        assert yaml_model.constraints[0].name == "test_constraint"

    def test_model_functions_with_many_constraints(
        self, sample_model_with_constraints: Model
    ):
        """Test that model functions correctly with many constraints."""

        constraints = [
            Constraint(f"constraint_{i}", "revenue", 1000.0 * i, "gt")
            for i in range(10)
        ]

        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints,
        )

        # Test that model still functions normally
        assert len(model.constraints) == 10
        assert model.value("revenue", 2023) == 100000
        assert model.value("expenses", 2024) == 60000

        # Test that all constraints are there
        constraint_names = [c.name for c in model.constraints]
        for i in range(10):
            assert f"constraint_{i}" in constraint_names
