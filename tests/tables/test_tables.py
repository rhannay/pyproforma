import pytest
from pyproforma.models import Model, LineItem, Category

class TestTableCreation:
    
    @pytest.fixture
    def sample_model(self):
        """Create a sample Model with line items and formulas for testing."""
        # Create line items with initial values and formulas
        revenue_sales = LineItem(
            name="revenue_sales", 
            label="Sales Revenue", 
            category="revenue", 
            values={2023: 1000000.0}, 
            formula='revenue_sales[-1] * 1.10'  # 10% growth
        )
        
        revenue_services = LineItem(
            name="revenue_services", 
            label="Service Revenue", 
            category="revenue", 
            values={2023: 500000.0}, 
            formula='revenue_services[-1] * 1.15'  # 15% growth
        )
        
        cost_of_goods = LineItem(
            name="cost_of_goods", 
            label="Cost of Goods Sold", 
            category="expense", 
            values={2023: 400000.0}, 
            formula='revenue_sales * 0.4'  # 40% of sales revenue
        )
        
        operating_expenses = LineItem(
            name="operating_expenses", 
            label="Operating Expenses", 
            category="expense", 
            values={2023: 300000.0}, 
            formula='operating_expenses[-1] * 1.05'  # 5% growth
        )
        
        # Define categories
        categories = [
            Category(name="revenue", label="Revenue"),
            Category(name="expense", label="Expenses"),
            Category(name="calculated", label="Calculated", include_total=False)
        ]
        
        # Define calculated formulas as LineItems
        gross_profit = LineItem(
            name="gross_profit", 
            label="Gross Profit", 
            category="calculated",
            formula="total_revenue - cost_of_goods"
        )
        
        net_profit = LineItem(
            name="net_profit", 
            label="Net Profit", 
            category="calculated",
            formula="total_revenue - total_expense"
        )
        
        profit_margin = LineItem(
            name="profit_margin", 
            label="Profit Margin %", 
            category="calculated",
            formula="net_profit / total_revenue * 100"
        )
        
        return Model(
            line_items=[revenue_sales, revenue_services, cost_of_goods, operating_expenses, gross_profit, net_profit, profit_margin],
            categories=categories,
            years=[2023, 2024, 2025, 2026]
        )
    
    def test_table_creation(self, sample_model: Model):
        # create all() table
        table = sample_model.tables.all()
        assert table is not None, "Table creation failed"

        table = sample_model.tables.line_items()
        assert table is not None, "Line items table creation failed"

        table = sample_model.tables.category('revenue')
        assert table is not None, "Category table creation failed"

        # Test the new item() method
        table = sample_model.tables.line_item('revenue_sales')
        assert table is not None, "Item table creation failed"
        # Verify the table has the correct structure - it now includes change calculations
        assert len(table.rows) == 4, "Item table should have 4 rows (value, % change, cumulative change, cumulative % change)"
        # Verify first cell contains the item name, second contains the label
        assert table.rows[0].cells[0].value == 'revenue_sales', "First cell should contain item name"
        assert table.rows[0].cells[1].value == 'Sales Revenue', "Second cell should contain item label"

    def test_item_table_assumption(self):
        """Test that item table creation works for an assumption (now as line item)."""
        line_items = [
            LineItem(name='growth_rate', label='Growth Rate', category='assumptions', 
                    values={2023: 0.05, 2024: 0.10, 2026: 0.07})
        ]
        
        categories = [
            Category(name='assumptions', label='Assumptions')
        ]
        
        model = Model(
            line_items=line_items,
            categories=categories,
            years=[2023, 2024, 2025, 2026, 2027]
        )
        table = model.tables.line_item('growth_rate')
        assert table is not None, "Assumption item table creation failed"
        assert len(table.rows) == 4, "Assumption item table should have 4 rows (value, % change, cumulative change, cumulative % change)"
        assert table.rows[0].cells[0].value == 'growth_rate', "First cell should contain assumption name"
        assert table.rows[0].cells[1].value == 'Growth Rate', "Second cell should contain assumption label"
        assert table.rows[0].cells[2].value == 0.05, "Third cell should contain value for 2023"
        assert table.rows[1].cells[2].value == None  # No previous value to compare against
        assert table.rows[1].cells[3].value == 1.0  # 100% change from 0.05 to 0.10





