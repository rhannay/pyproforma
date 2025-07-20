from pyproforma.models.line_item_generator.short_term_debt import ShortTermDebt
from pyproforma.models.model.model import Model
from pyproforma.models.line_item import LineItem
from .utils import _is_close
import pytest


class TestShortTermDebtInModel:
    """
    Tests for ShortTermDebt line item generator integration with the Model.
    
    These tests verify that ShortTermDebt instances can reference values from other line items 
    in the model and that their calculated values are correctly integrated into the model's value matrix.
    """
    
    def test_short_term_debt_fixed_parameters_in_model(self):
        """
        Test short-term debt with fixed parameters integrated into a model.
        
        This test creates a Model with a ShortTermDebt line item generator using fixed parameters
        and verifies that the model correctly calculates debt outstanding, draws, principal, and 
        interest values for each year.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a short-term debt generator with fixed parameters
        std = ShortTermDebt(
            name='credit_line',
            draws={2020: 500000, 2021: 300000},
            paydown={2021: 200000, 2022: 600000},
            begin_balance=1000000,
            interest_rate=0.05
        )
        
        # Create a model with the short-term debt generator
        model = Model(
            line_items=[],  # No additional line items needed for fixed parameters
            years=years,
            line_item_generators=[std]
        )
        
        # Test year 2020 values (draw only)
        assert model.get_value('credit_line.debt_outstanding', 2020) == 1500000  # 1M + 500k
        assert model.get_value('credit_line.draw', 2020) == 500000
        assert model.get_value('credit_line.principal', 2020) == 0.0
        assert _is_close(model.get_value('credit_line.interest', 2020), 50000)  # 1M * 0.05
        
        # Test year 2021 values (draw and paydown)
        assert model.get_value('credit_line.debt_outstanding', 2021) == 1600000  # 1.5M + 300k - 200k
        assert model.get_value('credit_line.draw', 2021) == 300000
        assert model.get_value('credit_line.principal', 2021) == 200000
        assert _is_close(model.get_value('credit_line.interest', 2021), 75000)  # 1.5M * 0.05
        
        # Test year 2022 values (paydown only)
        assert model.get_value('credit_line.debt_outstanding', 2022) == 1000000  # 1.6M - 600k
        assert model.get_value('credit_line.draw', 2022) == 0.0
        assert model.get_value('credit_line.principal', 2022) == 600000
        assert _is_close(model.get_value('credit_line.interest', 2022), 80000)  # 1.6M * 0.05

    def test_short_term_debt_dynamic_interest_rate_in_model(self):
        """
        Test short-term debt where interest_rate is a string reference to a value in the model.
        
        This test creates a Model with a line item 'prime_rate' and a ShortTermDebt line item generator
        that references this line item for its interest_rate. It verifies that the model correctly
        calculates interest values using the dynamic rate for each year.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a short-term debt generator that references the prime_rate line item
        std = ShortTermDebt(
            name='variable_debt',
            draws={},
            paydown={},
            begin_balance=1000000,
            interest_rate='prime_rate',  # Reference to the line item we'll create
        )
        
        # Create a model with line items and the debt generator
        model = Model(
            line_items=[
                # Create line items for the interest rate values in each year
                LineItem(
                    name="prime_rate",
                    category="rates",
                    values={
                        2020: 0.03,    # 3% in 2020
                        2021: 0.045,   # 4.5% in 2021
                        2022: 0.02     # 2% in 2022
                    }
                )
            ],
            years=years,
            line_item_generators=[std]
        )
        
        # Test debt outstanding remains constant (no draws/paydowns)
        assert model.get_value('variable_debt.debt_outstanding', 2020) == 1000000
        assert model.get_value('variable_debt.debt_outstanding', 2021) == 1000000
        assert model.get_value('variable_debt.debt_outstanding', 2022) == 1000000
        
        # Test interest calculations with varying rates
        assert _is_close(model.get_value('variable_debt.interest', 2020), 30000)   # 1M * 0.03
        assert _is_close(model.get_value('variable_debt.interest', 2021), 45000)   # 1M * 0.045
        assert _is_close(model.get_value('variable_debt.interest', 2022), 20000)   # 1M * 0.02
        
        # Test no draws or paydowns
        assert model.get_value('variable_debt.draw', 2020) == 0.0
        assert model.get_value('variable_debt.draw', 2021) == 0.0
        assert model.get_value('variable_debt.draw', 2022) == 0.0
        assert model.get_value('variable_debt.principal', 2020) == 0.0
        assert model.get_value('variable_debt.principal', 2021) == 0.0
        assert model.get_value('variable_debt.principal', 2022) == 0.0

    def test_short_term_debt_dynamic_draws_and_paydown_in_model(self):
        """
        Test short-term debt where draws and paydown are string references to values in the model.
        
        This test creates a Model with line items for draws and paydowns, and a ShortTermDebt line 
        item generator that references these line items. It verifies that the model correctly
        calculates all debt-related values using the dynamic parameters.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a short-term debt generator that references other line items
        std = ShortTermDebt(
            name='flexible_debt',
            draws='annual_draws',      # Reference to line item
            paydown='annual_paydown',  # Reference to line item
            begin_balance=750000,      # Fixed value
            interest_rate=0.04
        )
        
        # Create a model with line items and the debt generator
        model = Model(
            line_items=[
                LineItem(
                    name="initial_debt",
                    category="debt_params",
                    values={
                        2020: 750000,  # Initial debt balance
                        2021: 750000,  # Should be the same across years
                        2022: 750000
                    }
                ),
                LineItem(
                    name="annual_draws",
                    category="debt_activity",
                    values={
                        2020: 250000,  # Draw 250k in 2020
                        2021: 100000,  # Draw 100k in 2021
                        2022: 0        # No draw in 2022
                    }
                ),
                LineItem(
                    name="annual_paydown",
                    category="debt_activity",
                    values={
                        2020: 0,       # No paydown in 2020
                        2021: 150000,  # Pay down 150k in 2021
                        2022: 800000   # Pay down 800k in 2022
                    }
                )
            ],
            years=years,
            line_item_generators=[std]
        )
        
        # Test debt outstanding calculations
        assert model.get_value('flexible_debt.debt_outstanding', 2020) == 1000000  # 750k + 250k
        assert model.get_value('flexible_debt.debt_outstanding', 2021) == 950000   # 1M + 100k - 150k
        assert model.get_value('flexible_debt.debt_outstanding', 2022) == 150000   # 950k + 0 - 800k
        
        # Test draw values match the line items
        assert model.get_value('flexible_debt.draw', 2020) == 250000
        assert model.get_value('flexible_debt.draw', 2021) == 100000
        assert model.get_value('flexible_debt.draw', 2022) == 0
        
        # Test principal (paydown) values match the line items
        assert model.get_value('flexible_debt.principal', 2020) == 0
        assert model.get_value('flexible_debt.principal', 2021) == 150000
        assert model.get_value('flexible_debt.principal', 2022) == 800000
        
        # Test interest calculations (4% rate on beginning balance)
        assert _is_close(model.get_value('flexible_debt.interest', 2020), 30000)   # 750k * 0.04
        assert _is_close(model.get_value('flexible_debt.interest', 2021), 40000)   # 1M * 0.04
        assert _is_close(model.get_value('flexible_debt.interest', 2022), 38000)   # 950k * 0.04

    def test_short_term_debt_defined_names_in_model(self):
        """
        Test that ShortTermDebt defined_names are properly accessible in the model.
        """
        # Create a simple short-term debt generator
        std = ShortTermDebt(
            name='test_debt',
            draws={},
            paydown={},
            begin_balance=100000,
            interest_rate=0.05
        )
        
        # Create a model with the generator
        model = Model(
            line_items=[],
            years=[2020, 2021],
            line_item_generators=[std]
        )
        
        # Test that all defined names are in the model and accessible
        expected_names = [
            'test_debt.debt_outstanding',
            'test_debt.draw',
            'test_debt.principal',
            'test_debt.interest'
        ]
        
        for name in expected_names:
            # Test that we can get values for all years
            assert model.get_value(name, 2020) is not None
            assert model.get_value(name, 2021) is not None