import pytest
from pyproforma import LineItem, Model, Category, Debt
from pyproforma.models.constraint import Constraint
from pyproforma.generators.debt import generate_debt_service_schedule

class TestItemTypeValidation:

    def test_item_type_created_if_not_provided(self):
        li_set = Model(
            line_items=[LineItem(name="item1", label="Item 1", category="revenue", values={2020: 100.0})],
            years=[2020]
        )
        assert len(li_set._category_definitions) == 1
        assert li_set._category_definitions[0].name == "revenue"
    
    def test_item_type_missing(self):
        with pytest.raises(ValueError) as excinfo:
            Model(
                line_items=[LineItem(name="item1", label="Item 1", category="expense", values={2020: 100.0})],
                categories=[Category(name="revenue")],
                years=[2020]
            )
        assert "not defined category" in str(excinfo.value)


class TestLineItemsWithFormulas:
    @pytest.fixture
    def sample_line_item_set_2(self) -> Model:
        # Create a sample Model with LineItems and Formulas
        rev_1 = LineItem(name="rev_1", label="Item 1", category="revenue", values={2020: 300.0}, formula='rev_1[-1] * 1.05')
        rev_2 = LineItem(name="rev_2", label="Item 2", category="revenue", values={2020: 100.0}, formula='rev_2[-1] + 50.0')
        exp_1 = LineItem(name="exp_1", label="Item 3", category="expense", values={2020: 200.0}, formula='exp_1[-1] * 0.95')

        categories = [
            Category(name="expense"),
            Category(name="revenue"),
            Category(name="calculated")
        ]

        # Convert formulas to LineItems
        net_revenue = LineItem(name="net_revenue", label="Net Revenue", category="calculated", formula="total_revenue - total_expense")

        return Model(
            line_items=[rev_1, rev_2, exp_1, net_revenue],
            categories=categories,
            years=[2020, 2021, 2022]
        )
    
    def test_line_item_set_init(self, sample_line_item_set_2: Model):
        # Check the Model initialization
        assert isinstance(sample_line_item_set_2, Model)
        assert len(sample_line_item_set_2._line_item_definitions) == 4  # Now includes the formula as a LineItem
        assert len(sample_line_item_set_2._category_definitions) == 3  # Added 'calculated' category
        assert sample_line_item_set_2.years == [2020, 2021, 2022]

        assert sample_line_item_set_2["rev_1", 2020] == 300.0
        assert sample_line_item_set_2["rev_1", 2021] == 300.0 * 1.05
        assert sample_line_item_set_2["rev_1", 2022] == 300.0 * 1.05 * 1.05
        assert sample_line_item_set_2["rev_2", 2020] == 100.0
        assert sample_line_item_set_2["rev_2", 2021] == 100.0 + 50.0
        assert sample_line_item_set_2["rev_2", 2022] == 100.0 + 50.0 + 50.0
        assert sample_line_item_set_2["exp_1", 2020] == 200.0       
        assert sample_line_item_set_2["exp_1", 2021] == 200.0 * 0.95
        assert sample_line_item_set_2["exp_1", 2022] == 200.0 * 0.95 * 0.95
        assert sample_line_item_set_2["net_revenue", 2020] == 200.0
        assert sample_line_item_set_2["net_revenue", 2021] == (300.0 * 1.05 + 100.0 + 50.0) - (200.0 * 0.95)
        assert sample_line_item_set_2["net_revenue", 2022] == (300.0 * 1.05 * 1.05 + 100.0 + 50.0 + 50.0) - (200.0 * 0.95 * 0.95)

        assert sample_line_item_set_2["total_revenue", 2020] == 300.0 + 100.0
        assert sample_line_item_set_2["total_revenue", 2021] == (300.0 * 1.05 + 100.0 + 50.0)
        assert sample_line_item_set_2["total_revenue", 2022] == (300.0 * 1.05 * 1.05 + 100.0 + 50.0 + 50.0)

class TestModelWithBalanceSheetConcept:
    @pytest.fixture
    def sample_line_item_set(self) -> Model:
        rev_1 = LineItem(name="rev_1", label="Item 1", category="revenue", values={2020: 300.0, 2021: 400.0})
        rev_2 = LineItem(name="rev_2", label="Item 2", category="revenue", values={2020: 100.0, 2021: 200.0})
        exp_1 = LineItem(name="exp_1", label="Item 3", category="expense", values={2020: 200.0, 2021: 300.0})
        begin_cash = LineItem(name="begin_cash", label="Beginning Cash", category="balance", values={2020: 1000.0}, formula='end_cash[-1]')
        end_cash = LineItem(name="end_cash", label="Ending Cash", category="balance", values={}, formula='begin_cash + total_revenue - total_expense')

        return Model(
            line_items=[rev_1, rev_2, exp_1,begin_cash, end_cash],
            # balance_sheet_line_items=[begin_cash, end_cash],
            years=[2020, 2021]
        )
    
    def test_line_item_set_init(self, sample_line_item_set: Model):
        assert sample_line_item_set['rev_1', 2020] == 300.0
        expected_end_cash_2020 = 1000.0 + 300.0 + 100.0 - 200.0
        assert sample_line_item_set['end_cash', 2020] == expected_end_cash_2020
        assert sample_line_item_set['begin_cash', 2021] == expected_end_cash_2020
        expected_end_cash_2021 = expected_end_cash_2020 + 400.0 + 200.0 - 300.0
        assert sample_line_item_set['end_cash', 2021] == expected_end_cash_2021

class TestSetWithAssumptions:

    def test_with_assumption_init(self):
        liset = Model(
            line_items=[
            LineItem(name='revenue', category='revenue', values={2020: 100, 2021: 200}),
            LineItem(name='rate_increase', category='assumption')
            ],
            years=[2020, 2021]
        )
        assert isinstance(liset, Model)
        defined_names = [x['name'] for x in liset.defined_names]
        assert 'rate_increase' in defined_names

    def test_assumption_in_value_matrix(self):
        liset = Model(
            line_items=[
            LineItem(name='revenue', category='revenue', values={2020: 100, 2021: 200, 2022: 300}),
            LineItem(name='rate_increase', category='assumption', values={2020: 0.05, 2021: 0.07})
            ],
            years=[2020, 2021, 2022]
        )
        value_matrix = liset._value_matrix
        assert 'rate_increase' in value_matrix[2020]
        assert value_matrix[2020]['rate_increase'] == 0.05
        assert liset['rate_increase', 2020] == 0.05
        assert liset['rate_increase', 2021] == 0.07
        assert liset['rate_increase', 2022] is None

    def test_line_item_uses_assumption(self):
        liset = Model(
            line_items=[
            LineItem(name='revenue', category='revenue', values={2020: 100}, formula='revenue[-1] * (1 + rate_increase)'),
            LineItem(name='rate_increase', category='assumption', values={2021: 0.05, 2022: 0.07})
            ],
            years=[2020, 2021, 2022]
        )
        value_matrix = liset._value_matrix
        assert value_matrix[2020]['revenue'] == 100.0
        assert value_matrix[2021]['revenue'] == 100 * 1.05
        assert value_matrix[2022]['revenue'] == 100 * 1.05 * 1.07


class TestModelWithGenerators:
    @pytest.fixture
    def sample_line_item_set_with_generators(self) -> Model:
        # Create a sample Model with LineItems and Generators
        p = LineItem(name="principal", category="debt_service", values={2020: 300.0}, formula='debt.principal')
        i = LineItem(name="interest", category="debt_service", values={2020: 100.0}, formula='debt.interest')
        debt = Debt(name='debt', par_amounts={2021: 1000.0}, interest_rate=0.05, term=30)
        return Model(
            line_items=[p, i],
            years=[2020, 2021, 2022],
            generators=[debt]
        )
    
    def test_line_item_set_with_generators(self, sample_line_item_set_with_generators: Model):
        lis = sample_line_item_set_with_generators
        ds_schedule = generate_debt_service_schedule(1000.0, 0.05, 2021, 30)
        
        assert isinstance(lis, Model)
        assert lis['debt.principal', 2020] == 0
        assert lis['debt.principal', 2021] == ds_schedule[0]['principal']
        assert lis['debt.principal', 2022] == ds_schedule[1]['principal']
        assert lis['principal', 2020] == 300.0
        assert lis['principal', 2021] == ds_schedule[0]['principal']
        assert lis['principal', 2022] == ds_schedule[1]['principal']
        assert lis['debt.interest', 2020] == 0
        assert lis['debt.interest', 2021] == ds_schedule[0]['interest']
        assert lis['debt.interest', 2022] == ds_schedule[1]['interest']
        assert lis['interest', 2020] == 100.0
        assert lis['interest', 2021] == ds_schedule[0]['interest']
        assert lis['interest', 2022] == ds_schedule[1]['interest']

class TestDuplicateNames:
    def test_names_conflict_with_categories(self):
        with pytest.raises(ValueError) as excinfo:
            Model(
                line_items=[LineItem(name="total_revenue", label='total revenue', category="revenue", values={2020: 100.0})],
                categories=[Category(name="revenue"),],
                years=[2020]
            )
        assert "Duplicate" in str(excinfo.value)
        
        # item name and formula name overlap
        with pytest.raises(ValueError) as excinfo:
            lis = [
                LineItem(name="op_rev", label="Total Revenue", category="revenue", values={2020: 100.0}),
                LineItem(name="op_rev", label="Net Revenue", category="calculated", formula="op_rev - item1")
            ]
            Model(lis, years=[2020])
        assert "Duplicate" in str(excinfo.value)


        # formula and category total name overlap
        with pytest.raises(ValueError) as excinfo:
            lis = [
                LineItem(name="op_rev", label="Total Revenue", category="revenue", values={2020: 100.0}),
                LineItem(name="total_revenue", label="Net Revenue", category="calculated", formula="op_rev")
            ]
            Model(lis, years=[2020])
        assert "Duplicate" in str(excinfo.value)

class TestOtherMisc:
    def test_line_item_set_get_item(self, sample_line_item_set: Model):
        
        # assert item values by year
        assert sample_line_item_set["item1", 2020] == 100.0
        assert sample_line_item_set["item2", 2021] == 75.0

        # check categories
        sorted_1 = sorted(sample_line_item_set._category_definitions, key=lambda x: x.name)
        assert sorted_1[0].name == "expense"
        assert sorted_1[0].label == "expense"
        assert sorted_1[1].name == "revenue"
        assert sorted_1[1].label == "revenue"

        with pytest.raises(KeyError) as excinfo:
            sample_line_item_set["item4", 2020]
        assert "not found" in str(excinfo.value)

        with pytest.raises(KeyError) as excinfo:
            sample_line_item_set["item1", 2022]
        assert "Year 2022 not found" in str(excinfo.value)

        # get a category total
        assert sample_line_item_set["total_revenue", 2020] == 300.0  

    def test_is_last_item_in_category(self):
        sample = Model(
            line_items=[
                LineItem(name="item1", category="revenue", values={2020: 100.0}),
                LineItem(name="item2", category="expense", values={2020: 200.0}),                
                LineItem(name="item3", category="revenue", values={2020: 100.0}),
                LineItem(name="item4", category="expense", values={2020: 150.0})
            ],
            categories=[Category(name="revenue"), Category(name="expense")],
            years=[2020]
        )
        
        # Test if the last item in a category is identified correctly
        assert sample._is_last_item_in_category("item1") is False
        assert sample._is_last_item_in_category("item2") is False
        assert sample._is_last_item_in_category("item3") is True
        assert sample._is_last_item_in_category("item4") is True

    def test_category_total(self):
        sample = Model(
            line_items=[
                LineItem(name="item1", category="revenue", values={2020: 100.0}),
                LineItem(name="item2", category="expense", values={2020: 200.0}),
                LineItem(name="item3", category="revenue", values={2020: 150.0}),
                LineItem(name="item4", category="expense", values={2020: 250.0})
            ],
            categories=[Category(name="revenue"), Category(name="expense")],
            years=[2020]
        )
        
        # Test category total calculation
        assert sample.category_total("revenue", 2020) == 250.0
        assert sample.category_total("expense", 2020) == 450.0

    def test_get_item_info(self):
        sample = Model(
            line_items=[
            LineItem(name="item1", category="revenue", values={2020: 100.0}),
            LineItem(name="item2", category="expense", values={2020: 200.0}),
            LineItem(name="growth_rate", label='Growth Rate', category='assumption', value_format='two_decimals')
            ],
            categories=[Category(name="revenue"), Category(name="expense"), Category(name="assumption")],
            years=[2020]
        )
        
        # Test getting item info for line item
        item_info = sample._get_item_metadata("item1")
        assert item_info['name'] == 'item1'
        assert item_info['source_type'] == 'line_item'
        assert item_info['source_name'] == 'item1'
        
        # Test getting item info for assumption
        assumption_info = sample._get_item_metadata("growth_rate")
        assert assumption_info['name'] == 'growth_rate'
        assert assumption_info['label'] == 'Growth Rate'
        assert assumption_info['value_format'] == 'two_decimals'
        assert assumption_info['source_type'] == 'line_item'
        
        # Test getting item info for category total
        total_info = sample._get_item_metadata("total_revenue")
        assert total_info['name'] == 'total_revenue'
        assert total_info['source_type'] == 'category'
        assert total_info['source_name'] == 'revenue'
        
        # Test KeyError for non-existent item
        with pytest.raises(KeyError) as excinfo:
            sample._get_item_metadata("non_existent_item")
        assert "not found in model" in str(excinfo.value)


class TestPercentChange:
    """Test cases for the percent_change method."""
    
    @pytest.fixture
    def sample_model_for_percent_change(self) -> Model:
        """Create a sample model with predictable values for percent change testing."""
        return Model(
            line_items=[
                LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 120.0}),
                LineItem(name="expense", category="expense", values={2020: 50.0, 2021: 50.0, 2022: 75.0, 2023: 0.0}),
                LineItem(name="zero_item", category="other", values={2020: 0.0, 2021: 10.0, 2022: 0.0, 2023: 5.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )
    
    def test_percent_change_basic_calculation(self, sample_model_for_percent_change: Model):
        """Test basic percent change calculation."""
        model = sample_model_for_percent_change
        
        # Revenue: 100 -> 120 = 20% increase = 0.2
        assert model.percent_change("revenue", 2021) == 0.2
        
        # Revenue: 120 -> 150 = 25% increase = 0.25  
        assert model.percent_change("revenue", 2022) == 0.25
        
        # Revenue: 150 -> 120 = -20% decrease = -0.2
        assert model.percent_change("revenue", 2023) == -0.2
    
    def test_percent_change_no_change(self, sample_model_for_percent_change: Model):
        """Test percent change when values don't change."""
        model = sample_model_for_percent_change
        
        # Expense: 50 -> 50 = 0% change = 0.0
        assert model.percent_change("expense", 2021) == 0.0
    
    def test_percent_change_first_year_returns_none(self, sample_model_for_percent_change: Model):
        """Test that first year returns None (no previous year to compare)."""
        model = sample_model_for_percent_change
        
        # First year should always return None
        assert model.percent_change("revenue", 2020) is None
        assert model.percent_change("expense", 2020) is None
        assert model.percent_change("zero_item", 2020) is None
    
    def test_percent_change_with_zero_previous_value(self, sample_model_for_percent_change: Model):
        """Test percent change when previous value is zero (should return None)."""
        model = sample_model_for_percent_change
        
        # zero_item: 0 -> 10, can't calculate percent change from zero
        assert model.percent_change("zero_item", 2021) is None
        
        # zero_item: 0 -> 5, can't calculate percent change from zero  
        assert model.percent_change("zero_item", 2023) is None
    
    def test_percent_change_to_zero(self, sample_model_for_percent_change: Model):
        """Test percent change when current value becomes zero."""
        model = sample_model_for_percent_change
        
        # expense: 75 -> 0 = -100% decrease = -1.0
        assert model.percent_change("expense", 2023) == -1.0
        
        # zero_item: 10 -> 0 = -100% decrease = -1.0
        assert model.percent_change("zero_item", 2022) == -1.0
    
    def test_percent_change_with_none_values(self):
        """Test percent change when values are None."""
        # Create a simple model with None values for specific test
        model = Model(
            line_items=[
            LineItem(name="test_item", category="revenue", values={2020: 100.0, 2021: 150.0, 2022: 200.0}),
            LineItem(name="none_assumption", category="assumption", values={2020: 10.0, 2021: None, 2022: 20.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # none_assumption: 10.0 -> None, can't calculate
        assert model.percent_change("none_assumption", 2021) is None
        
        # none_assumption: None -> 20.0, can't calculate  
        assert model.percent_change("none_assumption", 2022) is None
    
    def test_percent_change_invalid_name(self, sample_model_for_percent_change: Model):
        """Test percent change with invalid item name."""
        model = sample_model_for_percent_change
        
        with pytest.raises(KeyError) as excinfo:
            model.percent_change("nonexistent_item", 2021)
        assert "not found in defined names" in str(excinfo.value)
    
    def test_percent_change_invalid_year(self, sample_model_for_percent_change: Model):
        """Test percent change with invalid year."""
        model = sample_model_for_percent_change
        
        with pytest.raises(KeyError) as excinfo:
            model.percent_change("revenue", 2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
    
    def test_percent_change_with_assumptions(self):
        """Test percent change with assumption values."""
        
        model = Model(
            line_items=[
            LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 110.0, 2022: 120.0}),
            LineItem(name="growth_rate", category="assumption", values={2020: 0.05, 2021: 0.10, 2022: 0.15})
            ],
            years=[2020, 2021, 2022]
        )
        
        # growth_rate: 0.05 -> 0.10 = 100% increase = 1.0
        assert model.percent_change("growth_rate", 2021) == 1.0
        
        # growth_rate: 0.10 -> 0.15 = 50% increase = 0.5 (use approximation for floating point)
        result = model.percent_change("growth_rate", 2022)
        assert abs(result - 0.5) < 1e-10
    
    def test_percent_change_with_category_totals(self):
        """Test percent change with category total values."""
        model = Model(
            line_items=[
                LineItem(name="rev1", category="revenue", values={2020: 60.0, 2021: 80.0, 2022: 100.0}),
                LineItem(name="rev2", category="revenue", values={2020: 40.0, 2021: 40.0, 2022: 50.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # total_revenue: 100 -> 120 = 20% increase = 0.2
        assert model.percent_change("total_revenue", 2021) == 0.2
        
        # total_revenue: 120 -> 150 = 25% increase = 0.25
        assert model.percent_change("total_revenue", 2022) == 0.25
    
    def test_percent_change_edge_case_precision(self):
        """Test percent change with very small numbers for precision."""
        model = Model(
            line_items=[
                LineItem(name="small_values", category="revenue", values={2020: 0.001, 2021: 0.002, 2022: 0.0015})
            ],
            years=[2020, 2021, 2022]
        )
        
        # 0.001 -> 0.002 = 100% increase = 1.0
        result_2021 = model.percent_change("small_values", 2021)
        assert abs(result_2021 - 1.0) < 1e-10
        
        # 0.002 -> 0.0015 = -25% decrease = -0.25
        result_2022 = model.percent_change("small_values", 2022)
        assert abs(result_2022 - (-0.25)) < 1e-10


class TestCumulativePercentChange:
    """Test cases for the cumulative_percent_change method."""
    
    @pytest.fixture
    def sample_model_for_cumulative_percent_change(self) -> Model:
        """Create a sample model with predictable values for cumulative percent change testing."""
        return Model(
            line_items=[
            LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0}),
            LineItem(name="expense", category="expense", values={2020: 50.0, 2021: 60.0, 2022: 75.0, 2023: 100.0}),
            LineItem(name="zero_start", category="balance", values={2020: 0.0, 2021: 10.0, 2022: 20.0, 2023: 30.0}),
            LineItem(name="growth_rate", category="assumption", values={2020: 0.05, 2021: 0.10, 2022: 0.15}),
            LineItem(name="none_values", category="assumption", values={2020: 100.0, 2021: None, 2022: 150.0}),
            LineItem(name="valid_assumption", category="assumption", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )
    
    def test_cumulative_percent_change_basic_calculation(self, sample_model_for_cumulative_percent_change: Model):
        """Test basic cumulative percent change calculation."""
        model = sample_model_for_cumulative_percent_change
        
        # Revenue: 100 -> 120 = 20% increase = 0.2
        assert model.cumulative_percent_change("revenue", 2021) == 0.2
        
        # Revenue: 100 -> 150 = 50% increase = 0.5
        assert model.cumulative_percent_change("revenue", 2022) == 0.5
        
        # Revenue: 100 -> 80 = -20% decrease = -0.2
        assert model.cumulative_percent_change("revenue", 2023) == -0.2
    
    def test_cumulative_percent_change_expense_increase(self, sample_model_for_cumulative_percent_change: Model):
        """Test cumulative percent change for increasing expenses."""
        model = sample_model_for_cumulative_percent_change
        
        # Expense: 50 -> 60 = 20% increase = 0.2
        assert model.cumulative_percent_change("expense", 2021) == 0.2
        
        # Expense: 50 -> 75 = 50% increase = 0.5
        assert model.cumulative_percent_change("expense", 2022) == 0.5
        
        # Expense: 50 -> 100 = 100% increase = 1.0
        assert model.cumulative_percent_change("expense", 2023) == 1.0
    
    def test_cumulative_percent_change_returns_none(self, sample_model_for_cumulative_percent_change: Model):
        """Test that first year returns None (no change from itself)."""
        model = sample_model_for_cumulative_percent_change
        
        # First year should always return 0
        assert model.cumulative_percent_change("revenue", 2020) == 0
        assert model.cumulative_percent_change("expense", 2020) == 0
        assert model.cumulative_percent_change("zero_start", 2020) == 0

    def test_cumulative_percent_change_with_zero_first_value(self, sample_model_for_cumulative_percent_change: Model):
        """Test cumulative percent change when first year value is zero (should return None)."""
        model = sample_model_for_cumulative_percent_change
        
        # zero_start: 0 -> 10, can't calculate percent change from zero
        assert model.cumulative_percent_change("zero_start", 2021) is None
        
        # zero_start: 0 -> 20, can't calculate percent change from zero
        assert model.cumulative_percent_change("zero_start", 2022) is None
    
    def test_cumulative_percent_change_with_none_values(self, sample_model_for_cumulative_percent_change: Model):
        """Test cumulative percent change when assumption values contain None."""
        model = sample_model_for_cumulative_percent_change
        
        # Should return None when the current value is None
        assert model.cumulative_percent_change("none_values", 2021) is None
        
        # Should return valid result when both base and current values are not None
        # none_values: 100.0 (2020) -> 150.0 (2022) = 50% increase = 0.5
        assert model.cumulative_percent_change("none_values", 2022) == 0.5
    
    def test_cumulative_percent_change_invalid_name(self, sample_model_for_cumulative_percent_change: Model):
        """Test cumulative percent change with invalid item name."""
        model = sample_model_for_cumulative_percent_change
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_percent_change("nonexistent_item", 2021)
        assert "not found in defined names" in str(excinfo.value)
    
    def test_cumulative_percent_change_invalid_year(self, sample_model_for_cumulative_percent_change: Model):
        """Test cumulative percent change with invalid year."""
        model = sample_model_for_cumulative_percent_change
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_percent_change("revenue", 2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
    
    def test_cumulative_percent_change_rejects_assumptions_with_none(self, sample_model_for_cumulative_percent_change: Model):
        """Test that cumulative_percent_change returns None for assumptions with None values."""
        model = sample_model_for_cumulative_percent_change
        
        # growth_rate has None value for 2023 (not in values dict)
        # Should return None instead of raising ValueError
        assert model.cumulative_percent_change("growth_rate", 2023) is None
        
        # none_values has explicit None in 2021 - should return None
        assert model.cumulative_percent_change("none_values", 2021) is None
        
        # But 2022 should work fine since both 2020 and 2022 have values
        assert model.cumulative_percent_change("none_values", 2022) == 0.5
    
    def test_cumulative_percent_change_accepts_valid_assumptions(self, sample_model_for_cumulative_percent_change: Model):
        """Test that cumulative_percent_change works for assumptions with all non-None values."""
        model = sample_model_for_cumulative_percent_change
        
        # valid_assumption has values for all years: 100 -> 120 = 20% increase = 0.2
        assert model.cumulative_percent_change("valid_assumption", 2021) == 0.2
        
        # valid_assumption: 100 -> 150 = 50% increase = 0.5
        assert model.cumulative_percent_change("valid_assumption", 2022) == 0.5
        
        # valid_assumption: 100 -> 80 = -20% decrease = -0.2
        assert model.cumulative_percent_change("valid_assumption", 2023) == -0.2
    
    def test_cumulative_percent_change_with_category_totals(self):
        """Test cumulative percent change with category total values."""
        model = Model(
            line_items=[
                LineItem(name="rev1", category="revenue", values={2020: 60.0, 2021: 80.0, 2022: 100.0}),
                LineItem(name="rev2", category="revenue", values={2020: 40.0, 2021: 50.0, 2022: 60.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        expected = (80 + 50) / (60 + 40) - 1
        assert model.cumulative_percent_change("total_revenue", 2021) == pytest.approx(expected)

        expected = (100 + 60) / (60 + 40) - 1
        assert model.cumulative_percent_change("total_revenue", 2022) == pytest.approx(expected)

    def test_cumulative_percent_change_edge_case_precision(self):
        """Test cumulative percent change with very small numbers for precision."""
        model = Model(
            line_items=[
                LineItem(name="small_values", category="revenue", values={2020: 0.001, 2021: 0.002, 2022: 0.0015})
            ],
            years=[2020, 2021, 2022]
        )
        
        expected = (0.002 / 0.001) - 1
        result_2021 = model.cumulative_percent_change("small_values", 2021)
        assert abs(result_2021 - expected) < 1e-10

        expected = (0.0015 / 0.001) - 1
        result_2022 = model.cumulative_percent_change("small_values", 2022)
        assert abs(result_2022 - expected) < 1e-10

    def test_cumulative_percent_change_to_zero(self):
        """Test cumulative percent change when current value becomes zero."""
        model = Model(
            line_items=[
                LineItem(name="declining_item", category="revenue", values={2020: 100.0, 2021: 50.0, 2022: 0.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # declining_item: 100 -> 50 = -50% decrease = -0.5
        assert model.cumulative_percent_change("declining_item", 2021) == -0.5
        
        # declining_item: 100 -> 0 = -100% decrease = -1.0
        assert model.cumulative_percent_change("declining_item", 2022) == -1.0
    
    def test_cumulative_percent_change_consistency_check(self):
        """Test that cumulative_percent_change calculations are consistent over multiple years."""
        model = Model(
            line_items=[
                LineItem(name="consistent_growth", category="revenue", values={2020: 100.0, 2021: 110.0, 2022: 120.0, 2023: 130.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )
        
        # Check that each year shows cumulative growth from first year
        assert model.cumulative_percent_change("consistent_growth", 2021) == 0.1  # 10% growth
        assert model.cumulative_percent_change("consistent_growth", 2022) == 0.2  # 20% growth
        assert model.cumulative_percent_change("consistent_growth", 2023) == 0.3  # 30% growth
    
    def test_cumulative_percent_change_assumption_validation_all_years(self):
        """Test that assumption validation checks all years, not just the requested year."""
        model = Model(
            line_items=[
                LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 140.0}),
                LineItem(name="partial_assumption", category="assumption", values={2020: 100.0, 2021: 120.0})  # Missing 2022
            ],
            years=[2020, 2021, 2022]
        )
        
        # Now that the function returns None instead of raising ValueError,
        # we should get None when trying to access a year with None value
        assert model.cumulative_percent_change("partial_assumption", 2021) == 0.2  # 100->120 = 20%
        assert model.cumulative_percent_change("partial_assumption", 2022) is None  # 2022 value is None

    # Tests for start_year parameter functionality
    
    @pytest.fixture
    def sample_model_for_start_year_tests(self) -> Model:
        """Create a sample model for testing start_year parameter functionality."""
        return Model(
            line_items=[
            LineItem(name="revenue", category="revenue", values={
                2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 180.0, 2024: 200.0
            }),
            LineItem(name="expense", category="expense", values={
                2020: 50.0, 2021: 60.0, 2022: 75.0, 2023: 90.0, 2024: 100.0
            }),
            LineItem(name="growth_rate", category="assumption", values={
                2020: 0.05, 2021: 0.10, 2022: 0.15, 2023: 0.20, 2024: 0.25
            })
            ],
            years=[2020, 2021, 2022, 2023, 2024]
        )
    
    def test_cumulative_percent_change_with_start_year_basic(self, sample_model_for_start_year_tests):
        """Test basic cumulative percent change calculation with custom start_year."""
        model = sample_model_for_start_year_tests
        
        # Using 2021 as start year: revenue 120 -> 150 = 25% increase = 0.25
        assert model.cumulative_percent_change("revenue", 2022, start_year=2021) == 0.25
        
        # Using 2021 as start year: revenue 120 -> 180 = 50% increase = 0.5
        assert model.cumulative_percent_change("revenue", 2023, start_year=2021) == 0.5
        
        # Using 2022 as start year: revenue 150 -> 200 = 33.33% increase
        result = model.cumulative_percent_change("revenue", 2024, start_year=2022)
        assert abs(result - (200.0 - 150.0) / 150.0) < 1e-10
    
    def test_cumulative_percent_change_start_year_same_as_target_year(self, sample_model_for_start_year_tests):
        """Test that using start_year same as target year returns 0."""
        model = sample_model_for_start_year_tests

        # When start_year equals target year, should return 0
        assert model.cumulative_percent_change("revenue", 2022, start_year=2022) == 0
        assert model.cumulative_percent_change("expense", 2023, start_year=2023) == 0
        assert model.cumulative_percent_change("growth_rate", 2021, start_year=2021) == 0
    
    def test_cumulative_percent_change_start_year_vs_default(self, sample_model_for_start_year_tests):
        """Test that start_year=None behaves same as not providing start_year (default behavior)."""
        model = sample_model_for_start_year_tests
        
        # These should be equivalent
        default_result = model.cumulative_percent_change("revenue", 2023)
        explicit_none_result = model.cumulative_percent_change("revenue", 2023, start_year=None)
        first_year_result = model.cumulative_percent_change("revenue", 2023, start_year=2020)
        
        assert default_result == explicit_none_result
        assert default_result == first_year_result
    
    def test_cumulative_percent_change_different_start_years(self, sample_model_for_start_year_tests):
        """Test cumulative percent change with different start years for the same target year."""
        model = sample_model_for_start_year_tests
        
        # All targeting 2024, but different start years
        from_2020 = model.cumulative_percent_change("revenue", 2024, start_year=2020)  # 100 -> 200 = 100% = 1.0
        from_2021 = model.cumulative_percent_change("revenue", 2024, start_year=2021)  # 120 -> 200 = 66.67%
        from_2022 = model.cumulative_percent_change("revenue", 2024, start_year=2022)  # 150 -> 200 = 33.33%
        from_2023 = model.cumulative_percent_change("revenue", 2024, start_year=2023)  # 180 -> 200 = 11.11%
        
        assert from_2020 == 1.0
        assert abs(from_2021 - (200.0 - 120.0) / 120.0) < 1e-10
        assert abs(from_2022 - (200.0 - 150.0) / 150.0) < 1e-10
        assert abs(from_2023 - (200.0 - 180.0) / 180.0) < 1e-10
        
        # Verify they're all different (since start values are different)
        assert from_2020 > from_2021 > from_2022 > from_2023
    
    def test_cumulative_percent_change_start_year_invalid(self, sample_model_for_start_year_tests):
        """Test cumulative percent change with invalid start_year."""
        model = sample_model_for_start_year_tests
        
        # Test with start_year not in model years
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_percent_change("revenue", 2023, start_year=2019)
        assert "Start year 2019 not found in model years" in str(excinfo.value)
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_percent_change("revenue", 2023, start_year=2025)
        assert "Start year 2025 not found in model years" in str(excinfo.value)
    
    def test_cumulative_percent_change_start_year_with_zero_value(self, sample_model_for_start_year_tests):
        """Test cumulative percent change when start_year has zero value."""
        # Create model with zero value in middle year
        model = Model(
            line_items=[
                LineItem(name="zero_middle", category="revenue", values={
                    2020: 100.0, 2021: 0.0, 2022: 150.0, 2023: 200.0
                })
            ],
            years=[2020, 2021, 2022, 2023]
        )
        
        # Using start_year with zero value should return None
        assert model.cumulative_percent_change("zero_middle", 2022, start_year=2021) is None
        assert model.cumulative_percent_change("zero_middle", 2023, start_year=2021) is None
        
        # But using start_year with non-zero value should work
        # 100 -> 150 = 50% increase
        assert model.cumulative_percent_change("zero_middle", 2022, start_year=2020) == 0.5
    
    def test_cumulative_percent_change_start_year_with_assumptions(self, sample_model_for_start_year_tests):
        """Test cumulative percent change with start_year for assumptions."""
        model = sample_model_for_start_year_tests
        
        # growth_rate: 0.10 -> 0.20 = 100% increase = 1.0
        assert model.cumulative_percent_change("growth_rate", 2023, start_year=2021) == 1.0
        
        # growth_rate: 0.15 -> 0.25 = 66.67% increase
        result = model.cumulative_percent_change("growth_rate", 2024, start_year=2022)
        assert abs(result - (0.25 - 0.15) / 0.15) < 1e-10
    
    def test_cumulative_percent_change_start_year_backward_calculation(self, sample_model_for_start_year_tests):
        """Test cumulative percent change with start_year later than target year."""
        model = sample_model_for_start_year_tests
        
        # Target year before start year: revenue from 180 (2023) to 150 (2022) = -16.67%
        result = model.cumulative_percent_change("revenue", 2022, start_year=2023)
        expected = (150.0 - 180.0) / 180.0  # -30/180 = -0.1667
        assert abs(result - expected) < 1e-10
        
        # Verify it's negative (going backward in time with increasing values)
        assert result < 0
    
    def test_cumulative_percent_change_start_year_with_none_values(self):
        """Test cumulative percent change start_year with assumptions containing None values."""
        # Model with None values in assumptions
        model = Model(
            line_items=[
                LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 140.0}),
                LineItem(name="partial_assumption", category="assumption", values={2020: 100.0, 2021: None, 2022: 140.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # Should return None for years with None values
        assert model.cumulative_percent_change("partial_assumption", 2021, start_year=2020) is None
        
        # But should work fine for line items
        assert model.cumulative_percent_change("revenue", 2022, start_year=2021) == (140.0 - 120.0) / 120.0
    
    def test_cumulative_percent_change_start_year_consistency(self, sample_model_for_start_year_tests):
        """Test that chaining cumulative percent changes gives consistent results."""
        model = sample_model_for_start_year_tests
        
        # Calculate 2020->2022 and 2022->2024, then verify they combine correctly
        change_2020_to_2022 = model.cumulative_percent_change("revenue", 2022, start_year=2020)  # 100->150 = 0.5
        change_2022_to_2024 = model.cumulative_percent_change("revenue", 2024, start_year=2022)  # 150->200 = 0.333...
        
        # Direct calculation 2020->2024
        change_2020_to_2024 = model.cumulative_percent_change("revenue", 2024, start_year=2020)  # 100->200 = 1.0
        
        # Verify the relationship: (1 + change1) * (1 + change2) - 1 = total_change
        combined_change = (1 + change_2020_to_2022) * (1 + change_2022_to_2024) - 1
        assert abs(combined_change - change_2020_to_2024) < 1e-10


class TestCumulativeChange:
    """Test cases for the cumulative_change method."""

    @pytest.fixture
    def sample_model_for_cumulative_change(self):
        """Create a sample model with predictable values for cumulative change testing."""
        return Model(
            line_items=[
            LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0}),
            LineItem(name="expense", category="expense", values={2020: 50.0, 2021: 60.0, 2022: 75.0, 2023: 100.0}),
            LineItem(name="zero_start", category="balance", values={2020: 0.0, 2021: 10.0, 2022: 20.0, 2023: 30.0}),
            LineItem(name="growth_rate", category="assumption", values={2020: 0.05, 2021: 0.10, 2022: 0.15}),
            LineItem(name="none_values", category="assumption", values={2020: 100.0, 2021: None, 2022: 150.0}),
            LineItem(name="valid_assumption", category="assumption", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )

    def test_cumulative_change_basic_calculation(self, sample_model_for_cumulative_change):
        """Test basic cumulative change calculation."""
        model = sample_model_for_cumulative_change
        
        # Revenue: 100 -> 120 = +20 absolute change
        assert model.cumulative_change("revenue", 2021) == 20.0
        
        # Revenue: 100 -> 150 = +50 absolute change
        assert model.cumulative_change("revenue", 2022) == 50.0
        
        # Revenue: 100 -> 80 = -20 absolute change
        assert model.cumulative_change("revenue", 2023) == -20.0
    
    def test_cumulative_change_expense_increase(self, sample_model_for_cumulative_change):
        """Test cumulative change for increasing expenses."""
        model = sample_model_for_cumulative_change
        
        # Expense: 50 -> 60 = +10 absolute change
        assert model.cumulative_change("expense", 2021) == 10.0
        
        # Expense: 50 -> 75 = +25 absolute change
        assert model.cumulative_change("expense", 2022) == 25.0
        
        # Expense: 50 -> 100 = +50 absolute change
        assert model.cumulative_change("expense", 2023) == 50.0
    
    def test_cumulative_change_base_year_returns_zero(self, sample_model_for_cumulative_change):
        """Test that base year returns 0 (no change from itself)."""
        model = sample_model_for_cumulative_change
        
        # Base year should always return 0
        assert model.cumulative_change("revenue", 2020) == 0
        assert model.cumulative_change("expense", 2020) == 0
        assert model.cumulative_change("zero_start", 2020) == 0

    def test_cumulative_change_with_zero_start_value(self, sample_model_for_cumulative_change):
        """Test cumulative change when base year value is zero."""
        model = sample_model_for_cumulative_change
        
        # zero_start: 0 -> 10 = +10 absolute change
        assert model.cumulative_change("zero_start", 2021) == 10.0
        
        # zero_start: 0 -> 20 = +20 absolute change
        assert model.cumulative_change("zero_start", 2022) == 20.0
        
        # zero_start: 0 -> 30 = +30 absolute change
        assert model.cumulative_change("zero_start", 2023) == 30.0
    
    def test_cumulative_change_invalid_name(self, sample_model_for_cumulative_change):
        """Test cumulative change with invalid item name."""
        model = sample_model_for_cumulative_change
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_change("nonexistent_item", 2021)
        assert "not found in defined names" in str(excinfo.value)

    def test_cumulative_change_invalid_year(self, sample_model_for_cumulative_change):
        """Test cumulative change with invalid year."""
        model = sample_model_for_cumulative_change
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_change("revenue", 2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)
    
    def test_cumulative_change_invalid_start_year(self, sample_model_for_cumulative_change):
        """Test cumulative change with invalid start year."""
        model = sample_model_for_cumulative_change
        
        with pytest.raises(KeyError) as excinfo:
            model.cumulative_change("revenue", 2021, start_year=2019)
        assert "Start year 2019 not found in model years" in str(excinfo.value)
    
    def test_cumulative_change_with_category_totals(self):
        """Test cumulative change with category total values."""
        model = Model(
            line_items=[
                LineItem(name="rev1", category="revenue", values={2020: 60.0, 2021: 80.0, 2022: 100.0}),
                LineItem(name="rev2", category="revenue", values={2020: 40.0, 2021: 50.0, 2022: 60.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # total_revenue: 100 -> 130 = +30 absolute change
        assert model.cumulative_change("total_revenue", 2021) == 30.0
        
        # total_revenue: 100 -> 160 = +60 absolute change
        assert model.cumulative_change("total_revenue", 2022) == 60.0
    
    def test_cumulative_change_edge_case_precision(self):
        """Test cumulative change with very small numbers for precision."""
        model = Model(
            line_items=[
                LineItem(name="small_values", category="revenue", values={2020: 0.001, 2021: 0.002, 2022: 0.0015})
            ],
            years=[2020, 2021, 2022]
        )
        
        # 0.001 -> 0.002 = +0.001 absolute change
        result_2021 = model.cumulative_change("small_values", 2021)
        assert abs(result_2021 - 0.001) < 1e-10
        
        # 0.001 -> 0.0015 = +0.0005 absolute change
        result_2022 = model.cumulative_change("small_values", 2022)
        assert abs(result_2022 - 0.0005) < 1e-10
    
    def test_cumulative_change_to_zero(self):
        """Test cumulative change when current value becomes zero."""
        model = Model(
            line_items=[
                LineItem(name="declining_item", category="revenue", values={2020: 100.0, 2021: 50.0, 2022: 0.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # declining_item: 100 -> 50 = -50 absolute change
        assert model.cumulative_change("declining_item", 2021) == -50.0
        
        # declining_item: 100 -> 0 = -100 absolute change
        assert model.cumulative_change("declining_item", 2022) == -100.0
    
    def test_cumulative_change_from_zero(self):
        """Test cumulative change when base value is zero."""
        model = Model(
            line_items=[
                LineItem(name="growing_from_zero", category="revenue", values={2020: 0.0, 2021: 25.0, 2022: 100.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # growing_from_zero: 0 -> 25 = +25 absolute change
        assert model.cumulative_change("growing_from_zero", 2021) == 25.0
        
        # growing_from_zero: 0 -> 100 = +100 absolute change
        assert model.cumulative_change("growing_from_zero", 2022) == 100.0
    
    def test_cumulative_change_with_negative_values(self):
        """Test cumulative change with negative values."""
        model = Model(
            line_items=[
                LineItem(name="negative_values", category="other", values={2020: -10.0, 2021: -5.0, 2022: 5.0, 2023: -20.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )
        
        # negative_values: -10 -> -5 = +5 absolute change
        assert model.cumulative_change("negative_values", 2021) == 5.0
        
        # negative_values: -10 -> 5 = +15 absolute change
        assert model.cumulative_change("negative_values", 2022) == 15.0
        
        # negative_values: -10 -> -20 = -10 absolute change
        assert model.cumulative_change("negative_values", 2023) == -10.0
    
    def test_cumulative_change_with_custom_start_year(self, sample_model_for_cumulative_change):
        """Test cumulative change with custom start year."""
        model = sample_model_for_cumulative_change
        
        # Revenue from 2021 -> 2022: 120 -> 150 = +30 absolute change
        assert model.cumulative_change("revenue", 2022, start_year=2021) == 30.0
        
        # Revenue from 2021 -> 2023: 120 -> 80 = -40 absolute change
        assert model.cumulative_change("revenue", 2023, start_year=2021) == -40.0
        
        # Expense from 2022 -> 2023: 75 -> 100 = +25 absolute change
        assert model.cumulative_change("expense", 2023, start_year=2022) == 25.0
    
    def test_cumulative_change_same_as_start_year(self, sample_model_for_cumulative_change):
        """Test cumulative change when target year equals start year."""
        model = sample_model_for_cumulative_change
        
        # Same year should always return 0
        assert model.cumulative_change("revenue", 2021, start_year=2021) == 0
        assert model.cumulative_change("expense", 2022, start_year=2022) == 0
        assert model.cumulative_change("zero_start", 2023, start_year=2023) == 0
    
    def test_cumulative_change_with_none_base_value(self):
        """Test cumulative change when base value is None."""
        model = Model(
            line_items=[
            LineItem(name="test_item", category="revenue", values={2020: 100.0, 2021: 150.0, 2022: 200.0}),
            LineItem(name="partial_assumption", category="other", values={2021: 20.0, 2022: 30.0})  # 2020 will be None
            ],
            years=[2020, 2021, 2022]
        )
        
        # For assumptions with None base values, should return None
        result = model.cumulative_change("partial_assumption", 2021)
        assert result is None
    
    def test_cumulative_change_large_numbers(self):
        """Test cumulative change with large numbers."""
        model = Model(
            line_items=[
                LineItem(name="large_values", category="revenue", values={2020: 1000000.0, 2021: 1500000.0, 2022: 2000000.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # large_values: 1,000,000 -> 1,500,000 = +500,000 absolute change
        assert model.cumulative_change("large_values", 2021) == 500000.0
        
        # large_values: 1,000,000 -> 2,000,000 = +1,000,000 absolute change
        assert model.cumulative_change("large_values", 2022) == 1000000.0
    
    def test_cumulative_change_additivity_property(self):
        """Test that cumulative changes are additive across different periods."""
        model = Model(
            line_items=[
                LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 180.0, 2024: 200.0})
            ],
            years=[2020, 2021, 2022, 2023, 2024]
        )
        
        # Calculate changes for different periods
        change_2020_to_2022 = model.cumulative_change("revenue", 2022, start_year=2020)  # 100->150 = 50
        change_2022_to_2024 = model.cumulative_change("revenue", 2024, start_year=2022)  # 150->200 = 50
        
        # Direct calculation 2020->2024
        change_2020_to_2024 = model.cumulative_change("revenue", 2024, start_year=2020)  # 100->200 = 100
        
        # Verify additivity: change1 + change2 = total_change
        assert change_2020_to_2022 + change_2022_to_2024 == change_2020_to_2024
        assert change_2020_to_2024 == 100.0

class TestIndexToYear:
    """"""

    @pytest.fixture
    def sample_model_for_index_to_year(self) -> Model:
        """Create a sample model with predictable values for index_to_year testing."""
        return Model(
            line_items=[
            LineItem(name="revenue", category="revenue", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0}),
            LineItem(name="expense", category="expense", values={2020: 50.0, 2021: 60.0, 2022: 75.0, 2023: 100.0}),
            LineItem(name="zero_start", category="balance", values={2020: 0.0, 2021: 10.0, 2022: 20.0, 2023: 30.0}),
            LineItem(name="growth_rate", category="assumption", values={2020: 0.05, 2021: 0.10, 2022: 0.15}),
            LineItem(name="none_values", category="assumption", values={2020: 100.0, 2021: None, 2022: 150.0}),
            LineItem(name="valid_assumption", category="assumption", values={2020: 100.0, 2021: 120.0, 2022: 150.0, 2023: 80.0})
            ],
            years=[2020, 2021, 2022, 2023]
        )

    def test_basic_index_to_year(self, sample_model_for_index_to_year):
        """Test basic index_to_year functionality with line items."""
        model = sample_model_for_index_to_year
        
        # Test base year returns 100
        assert model.index_to_year("revenue", 2020) == 100.0
        
        # Test indexed values
        # Revenue: 2020: 100 -> 2021: 120 = 120/100 * 100 = 120
        assert model.index_to_year("revenue", 2021) == 120.0
        
        # Revenue: 2020: 100 -> 2022: 150 = 150/100 * 100 = 150
        assert model.index_to_year("revenue", 2022) == 150.0
        
        # Revenue: 2020: 100 -> 2023: 80 = 80/100 * 100 = 80
        assert model.index_to_year("revenue", 2023) == 80.0

    def test_index_to_year_with_custom_start_year(self, sample_model_for_index_to_year):
        """Test index_to_year with custom start year."""
        model = sample_model_for_index_to_year
        
        # Using 2021 as start year for revenue (120 as base)
        assert model.index_to_year("revenue", 2021, start_year=2021) == 100.0
        # 2022: 150/120 * 100 = 125
        assert model.index_to_year("revenue", 2022, start_year=2021) == 125.0
        # 2023: 80/120 * 100 = 66.67 (approximately)
        indexed_2023 = model.index_to_year("revenue", 2023, start_year=2021)
        assert abs(indexed_2023 - 66.67) < 0.01

    def test_index_to_year_zero_base_value(self, sample_model_for_index_to_year):
        """Test index_to_year when base year value is zero."""
        model = sample_model_for_index_to_year
        
        # zero_start has 0 in 2020, so indexed calculation should return None
        assert model.index_to_year("zero_start", 2021) is None
        assert model.index_to_year("zero_start", 2022) is None

    def test_index_to_year_with_assumptions_valid(self, sample_model_for_index_to_year):
        """Test index_to_year with valid assumptions (no None values)."""
        model = sample_model_for_index_to_year
        
        # Test with valid_assumption which has no None values
        assert model.index_to_year("valid_assumption", 2020) == 100.0
        assert model.index_to_year("valid_assumption", 2021) == 120.0
        assert model.index_to_year("valid_assumption", 2022) == 150.0
        assert model.index_to_year("valid_assumption", 2023) == 80.0

    def test_index_to_year_with_assumptions_none_values(self, sample_model_for_index_to_year):
        """Test that index_to_year raises error for assumptions with None values."""
        model = sample_model_for_index_to_year
        

        assert model.index_to_year("none_values", 2020) == 100.0
        assert model.index_to_year("none_values", 2021) is None # Should return None due to None value
        assert model.index_to_year("none_values", 2022) == 150.0

    def test_index_to_year_invalid_name(self, sample_model_for_index_to_year):
        """Test index_to_year with invalid item name."""
        model = sample_model_for_index_to_year
        
        with pytest.raises(KeyError) as excinfo:
            model.index_to_year("invalid_name", 2020)
        assert "'invalid_name' not found in" in str(excinfo.value)

    def test_index_to_year_invalid_year(self, sample_model_for_index_to_year):
        """Test index_to_year with invalid year."""
        model = sample_model_for_index_to_year
        
        with pytest.raises(KeyError) as excinfo:
            model.index_to_year("revenue", 2025)
        assert "Year 2025 not found in model years" in str(excinfo.value)

    def test_index_to_year_invalid_start_year(self, sample_model_for_index_to_year):
        """Test index_to_year with invalid start year."""
        model = sample_model_for_index_to_year
        
        with pytest.raises(KeyError) as excinfo:
            model.index_to_year("revenue", 2021, start_year=2025)
        assert "Start year 2025 not found in model years" in str(excinfo.value)

    def test_index_to_year_percentage_calculations(self, sample_model_for_index_to_year):
        """Test that index_to_year calculations are correct for various scenarios."""
        model = sample_model_for_index_to_year
        
        # Expense: 2020: 50 -> 2021: 60 = 60/50 * 100 = 120
        assert model.index_to_year("expense", 2021) == 120.0
        
        # Expense: 2020: 50 -> 2022: 75 = 75/50 * 100 = 150
        assert model.index_to_year("expense", 2022) == 150.0
        
        # Expense: 2020: 50 -> 2023: 100 = 100/50 * 100 = 200
        assert model.index_to_year("expense", 2023) == 200.0

    def test_index_to_year_with_none_current_value(self):
        """Test index_to_year when current value is None."""
        model = Model(
            line_items=[
            LineItem(name="test_item", category="revenue", values={2020: 100.0, 2021: 150.0, 2022: 200.0}),
            LineItem(name="partial_assumption", category="assumption", values={2020: 10.0, 2021: None, 2022: 20.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        result = model.index_to_year("partial_assumption", 2021)
        assert result is None

    def test_index_to_year_fractional_results(self, sample_model_for_index_to_year):
        """Test index_to_year with fractional results."""
        model = Model(
            line_items=[
                LineItem(name="fractional", category="revenue", values={2020: 300.0, 2021: 100.0, 2022: 450.0})
            ],
            years=[2020, 2021, 2022]
        )
        
        # 2021: 100/300 * 100 = 33.33...
        indexed_2021 = model.index_to_year("fractional", 2021)
        assert abs(indexed_2021 - 33.33) < 0.01
        
        # 2022: 450/300 * 100 = 150
        assert model.index_to_year("fractional", 2022) == 150.0


class TestModelWithConstraints:
    """Test that Model works correctly with constraints."""
    
    @pytest.fixture
    def sample_model_with_constraints(self) -> Model:
        """Create a sample model with constraints for testing."""
        line_items = [
            LineItem(
                name="revenue",
                category="income",
                values={2023: 100000, 2024: 120000}
            ),
            LineItem(
                name="expenses",
                category="costs",
                values={2023: 50000, 2024: 60000}
            )
        ]
        
        categories = [
            Category(name="income", label="Income"),
            Category(name="costs", label="Costs")
        ]
        
        return Model(
            line_items=line_items,
            years=[2023, 2024],
            categories=categories
        )
    
    def test_model_initialization_with_constraints(self, sample_model_with_constraints):
        """Test that model can be initialized with constraints."""
        from pyproforma.models.constraint import Constraint
        
        constraints = [
            Constraint(
                name="min_revenue",
                line_item_name="revenue",
                target=80000.0,
                operator="gt"
            ),
            Constraint(
                name="max_expenses",
                line_item_name="expenses",
                target=70000.0,
                operator="le"
            )
        ]
        
        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints
        )
        
        assert len(model.constraints) == 2
        assert model.constraints[0].name == "min_revenue"
        assert model.constraints[1].name == "max_expenses"
        
        # Test that model still functions normally
        assert model.get_value("revenue", 2023) == 100000
        assert model.get_value("expenses", 2024) == 60000
    
    def test_constraints_preserved_during_copy(self, sample_model_with_constraints):
        """Test that constraints are preserved when copying a model."""
        from pyproforma.models.constraint import Constraint
        
        constraints = [
            Constraint(
                name="revenue_constraint",
                line_item_name="revenue",
                target=50000.0,
                operator="gt"
            )
        ]
        
        original_model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints
        )
        
        copied_model = original_model.copy()
        
        # Check that constraints are copied
        assert len(copied_model.constraints) == 1
        assert copied_model.constraints[0].name == "revenue_constraint"
        
        # Check that they are independent objects
        assert original_model.constraints[0] is not copied_model.constraints[0]
    
    def test_constraints_in_serialization(self, sample_model_with_constraints):
        """Test that constraints are included in serialization."""
        from pyproforma.models.constraint import Constraint
        
        constraints = [
            Constraint(
                name="test_constraint",
                line_item_name="revenue",
                target=90000.0,
                operator="ge"
            )
        ]
        
        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints
        )
        
        # Test to_dict
        model_dict = model.to_dict()
        assert 'constraints' in model_dict
        assert len(model_dict['constraints']) == 1
        assert model_dict['constraints'][0]['name'] == 'test_constraint'
        
        # Test from_dict
        reconstructed_model = Model.from_dict(model_dict)
        assert len(reconstructed_model.constraints) == 1
        assert reconstructed_model.constraints[0].name == 'test_constraint'
        
        # Test to_yaml
        yaml_str = model.to_yaml()
        assert 'constraints:' in yaml_str
        assert 'test_constraint' in yaml_str
        
        # Test from_yaml
        yaml_model = Model.from_yaml(yaml_str=yaml_str)

        assert len(yaml_model.constraints) == 1
        assert yaml_model.constraints[0].name == 'test_constraint'
    
    def test_model_functions_with_many_constraints(self, sample_model_with_constraints):
        """Test that model functions correctly with many constraints."""
        from pyproforma.models.constraint import Constraint
        
        constraints = [
            Constraint(f"constraint_{i}", "revenue", 1000.0 * i, "gt")
            for i in range(10)
        ]
        
        model = Model(
            line_items=sample_model_with_constraints._line_item_definitions,
            years=sample_model_with_constraints.years,
            categories=sample_model_with_constraints._category_definitions,
            constraints=constraints
        )
        
        # Test that model still functions normally
        assert len(model.constraints) == 10
        assert model.get_value("revenue", 2023) == 100000
        assert model.get_value("expenses", 2024) == 60000
        
        # Test that all constraints are there
        constraint_names = [c.name for c in model.constraints]
        for i in range(10):
            assert f"constraint_{i}" in constraint_names

