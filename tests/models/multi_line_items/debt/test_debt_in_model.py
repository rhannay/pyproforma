from pyproforma.models.multi_line_item.debt import Debt
from pyproforma.models.model.model import Model
from pyproforma.models.line_item import LineItem
from .utils import _get_p_i, _is_close
import pytest
import math


class TestDebtParamsFromValueMatrix:
    """
    Tests for Debt line item generator integration with the Model.
    
    These tests verify that Debt instances can reference values from other line items in the model
    and that their calculated values are correctly integrated into the model's value matrix.
    """
    
    def test_debt_par_amounts_from_value_matrix(self):
        """
        Test debt where par_amount is a string reference to a value in the model.
        
        This test creates a Model with a line item 'par_amount' and a Debt line item generator
        that references this line item for its par_amount. It then verifies that the model
        correctly calculates principal, interest, and bond proceeds values for each year.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a debt generator that references the par_amount line item
        debt = Debt(
            name='test_from_matrix',
            par_amount='par_amount',  # Reference to the line item we'll create
            interest_rate=0.05,
            term=30
        )
        
        # Create a model with line items and the debt generator
        model = Model(
            line_items=[
                # Create line items for the par_amount values in each year
                LineItem(
                    name="par_amount",
                    category="debt_params",
                    values={
                        2020: 1_000_000,
                        2021: 1_500_000, 
                        2022: 0  # No new issuance in 2022
                    }
                )
            ],
            years=years,
            multi_line_items=[debt]  # Add the debt generator directly to the model
        )
        
        # Test first year (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(model.value('test_from_matrix.principal', 2020), p1)
        assert _is_close(model.value('test_from_matrix.interest', 2020), i1)
        assert model.value('test_from_matrix.bond_proceeds', 2020) == 1_000_000
        
        # Test second year (2021) - both issuances exist
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(model.value('test_from_matrix.principal', 2021), p1 + p2)
        assert _is_close(model.value('test_from_matrix.interest', 2021), i1 + i2)
        assert model.value('test_from_matrix.bond_proceeds', 2021) == 1_500_000
        
        # Test third year (2022) - both previous issuances exist but no new bond proceeds
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2022)
        # Total values should be sum of both issuances, with no new bond proceeds
        assert _is_close(model.value('test_from_matrix.principal', 2022), p1 + p2)
        assert _is_close(model.value('test_from_matrix.interest', 2022), i1 + i2)
        assert model.value('test_from_matrix.bond_proceeds', 2022) == 0
        
    def test_all_debt_params_from_value_matrix(self):
        """
        Test debt where all parameters (par_amount, interest_rate, term) are string references.
        
        This test creates a Model with line items for 'par_amount', 'interest_rate', and 'term',
        then adds a Debt line item generator that references all three line items. It verifies
        that the model correctly calculates debt values considering the different parameters
        for each issuance year.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a debt object with all parameters as string references to line items
        debt = Debt(
            name='test_all_params',
            par_amount='par_amount',       # String reference to the line item
            interest_rate='interest_rate', # String reference to the line item
            term='term'                    # String reference to the line item
        )
        
        # Create a model with line items and the debt generator
        model = Model(
            line_items=[
                # Create line items for the par_amount values
                LineItem(
                    name="par_amount",
                    category="debt_params",
                    values={
                        2020: 1_000_000,
                        2021: 1_500_000,
                        2022: 0  # No new issuance
                    }
                ),
                # Create line items for interest_rate values
                LineItem(
                    name="interest_rate",
                    category="debt_params",
                    values={
                        2020: 0.05,
                        2021: 0.06,  # Different rate for 2021 issuance
                        2022: 0.07   # Not used since par_amount is 0
                    }
                ),
                # Create line items for term values
                LineItem(
                    name="term",
                    category="debt_params",
                    values={
                        2020: 30,
                        2021: 25,  # Different term for 2021 issuance
                        2022: 20   # Not used since par_amount is 0
                    }
                )
            ],
            years=years,
            multi_line_items=[debt]  # Add the debt generator directly to the model
        )
        
        # Test first year (2020) - only first issuance exists
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(model.value('test_all_params.principal', 2020), p1)
        assert _is_close(model.value('test_all_params.interest', 2020), i1)
        assert model.value('test_all_params.bond_proceeds', 2020) == 1_000_000
        
        # Test second year (2021) - both issuances exist
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance (2021) - note the different rate and term
        p2, i2 = _get_p_i(i=0.06, p=1_500_000, t=25, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(model.value('test_all_params.principal', 2021), p1 + p2)
        assert _is_close(model.value('test_all_params.interest', 2021), i1 + i2)
        assert model.value('test_all_params.bond_proceeds', 2021) == 1_500_000
        
        # Test third year (2022) - both previous issuances exist but no new bond proceeds
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.06, p=1_500_000, t=25, sy=2021, y=2022)
        # Total values should be sum of both issuances, with no new bond proceeds
        assert _is_close(model.value('test_all_params.principal', 2022), p1 + p2)
        assert _is_close(model.value('test_all_params.interest', 2022), i1 + i2)
        assert model.value('test_all_params.bond_proceeds', 2022) == 0

    def test_debt_par_amounts_from_value_matrix_multi_layer(self):
        """
        Test debt where par_amount is a string reference to a multi-layered chain of formulas in the model.
        
        This test creates a Model with a line item 'par_amount' and then multiple layers of LineItems
        with formulas that reference each other (par_amount_2 references par_amount, par_amount_3 references
        par_amount_2, etc.). The Debt line item generator references the last LineItem in the chain (par_amount_4).
        
        This tests the model's ability to correctly resolve multi-level dependencies during value matrix iterations
        and calculate debt values accurately. Initially, the debt cannot be calculated because the chain of values
        needs to be resolved through multiple iterations of the value matrix calculation.
        """
        # Define years for our model
        years = [2020, 2021, 2022]
        
        # Create a debt generator that references the last layer in our formula chain
        debt = Debt(
            name='test_from_matrix',
            par_amount='par_amount_4',  # Reference to the final line item in the chain
            interest_rate=0.05,
            term=30
        )
        
        # Create a model with line items and the debt generator
        model = Model(
            line_items=[
                # Base line item with actual values
                LineItem(
                    name="par_amount",
                    category="debt_params",
                    values={
                        2020: 1_000_000,
                        2021: 1_500_000, 
                        2022: 0  # No new issuance in 2022
                    }
                ),
                # First formula layer - references the base value
                LineItem(
                    name="par_amount_2",
                    category="debt_params",
                    formula="par_amount"  # Formula that simply returns par_amount's value
                ),
                # Second formula layer - references the first formula layer
                LineItem(
                    name="par_amount_3",
                    category="debt_params",
                    formula="par_amount_2"  # Formula that references the first formula layer
                ),
                # Third formula layer - references the second formula layer
                LineItem(
                    name="par_amount_4",
                    category="debt_params",
                    formula="par_amount_3"  # Formula that references the second formula layer
                )
            ],
            years=years,
            multi_line_items=[debt]  # Add the debt generator directly to the model
        )
        
        # Verify the chain of reference values are calculated correctly
        assert model.value('par_amount', 2020) == 1_000_000
        assert model.value('par_amount_2', 2020) == 1_000_000
        assert model.value('par_amount_3', 2020) == 1_000_000
        assert model.value('par_amount_4', 2020) == 1_000_000
        
        assert model.value('par_amount', 2021) == 1_500_000
        assert model.value('par_amount_2', 2021) == 1_500_000
        assert model.value('par_amount_3', 2021) == 1_500_000
        assert model.value('par_amount_4', 2021) == 1_500_000
        
        assert model.value('par_amount', 2022) == 0
        assert model.value('par_amount_2', 2022) == 0
        assert model.value('par_amount_3', 2022) == 0
        assert model.value('par_amount_4', 2022) == 0
        
        # Test first year (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2020)
        assert _is_close(model.value('test_from_matrix.principal', 2020), p1)
        assert _is_close(model.value('test_from_matrix.interest', 2020), i1)
        assert model.value('test_from_matrix.bond_proceeds', 2020) == 1_000_000
        
        # Test second year (2021) - both issuances exist
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2021)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2021)
        # Total values should be sum of both issuances
        assert _is_close(model.value('test_from_matrix.principal', 2021), p1 + p2)
        assert _is_close(model.value('test_from_matrix.interest', 2021), i1 + i2)
        assert model.value('test_from_matrix.bond_proceeds', 2021) == 1_500_000
        
        # Test third year (2022) - both previous issuances exist but no new bond proceeds
        # Values from first issuance (2020)
        p1, i1 = _get_p_i(i=0.05, p=1_000_000, t=30, sy=2020, y=2022)
        # Values from second issuance (2021)
        p2, i2 = _get_p_i(i=0.05, p=1_500_000, t=30, sy=2021, y=2022)
        # Total values should be sum of both issuances, with no new bond proceeds
        assert _is_close(model.value('test_from_matrix.principal', 2022), p1 + p2)
        assert _is_close(model.value('test_from_matrix.interest', 2022), i1 + i2)
        assert model.value('test_from_matrix.bond_proceeds', 2022) == 0
