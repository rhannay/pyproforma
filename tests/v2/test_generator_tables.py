"""
Test that generated fields work with the v2 system.

Note: Generated fields (e.g., debt_principal) are accessible via model.li but not
via model[] subscript notation, as they are internal to the generator. To display
generated fields in tables, users should create FormulaLine wrappers.
"""

import pytest

from pyproforma.v2 import (
    Assumption,
    DebtLine,
    FixedLine,
    FormulaLine,
    ProformaModel,
)


def test_generated_fields_accessible_via_li():
    """Test that generated fields are accessible via model.li."""

    class DebtModel(ProformaModel):
        interest_rate = Assumption(value=0.05)
        term = Assumption(value=10)

        par_amounts = FixedLine(values={2024: 100000, 2025: 0})

        debt = DebtLine(
            par_amount_name="par_amounts",
            interest_rate_name="interest_rate",
            term_name="term",
        )

    model = DebtModel(periods=[2024, 2025])

    # Generated fields are accessible via model.li
    assert model.li.debt_principal[2024] > 0
    assert model.li.debt_interest[2024] > 0
    assert model.li.debt_debt_outstanding[2024] > 0
    assert model.li.debt_proceeds[2024] == 100000


def test_generated_fields_in_formulas_and_tables():
    """Test using generated fields in formulas which can then be displayed in tables."""

    class DebtModel(ProformaModel):
        interest_rate = Assumption(value=0.05)
        term = Assumption(value=10)

        par_amounts = FixedLine(values={2024: 100000, 2025: 0})

        debt = DebtLine(
            par_amount_name="par_amounts",
            interest_rate_name="interest_rate",
            term_name="term",
        )

        # Create formula wrappers for table display
        principal = FormulaLine(
            formula=lambda a, li, t: li.debt_principal[t],
            label="Principal Payment",
        )

        interest = FormulaLine(
            formula=lambda a, li, t: li.debt_interest[t],
            label="Interest Payment",
        )

        total_debt_service = FormulaLine(
            formula=lambda a, li, t: li.debt_principal[t] + li.debt_interest[t],
            label="Total Debt Service",
        )

    model = DebtModel(periods=[2024, 2025])

    # Now these formula line items can be used in tables
    table = model.tables.line_items(
        line_items=["principal", "interest", "total_debt_service"]
    )
    assert table is not None

    # Can also use from_template
    template = [
        {"row_type": "label", "label": "Debt Schedule", "bold": True},
        {"row_type": "item", "name": "principal"},
        {"row_type": "item", "name": "interest"},
        {"row_type": "blank"},
        {"row_type": "item", "name": "total_debt_service"},
    ]

    debt_table = model.tables.from_template(template)
    assert debt_table is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
