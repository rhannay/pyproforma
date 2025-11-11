"""
Unit tests for TwoModelCompare class.
"""


from pyproforma import LineItem, Model, TwoModelCompare


class TestTwoModelCompareInit:
    """Test initialization of TwoModelCompare."""

    def test_init_with_two_models(self):
        """Test initialization with two models."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100, 2021: 150},
                )
            ],
            years=[2020, 2021],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120, 2021: 160},
                )
            ],
            years=[2020, 2021],
        )

        comparison = TwoModelCompare(model1, model2)

        assert comparison.base_model == model1
        assert comparison.compare_model == model2
        assert comparison.common_years == [2020, 2021]
        assert comparison.common_items == ["revenue"]


class TestTwoModelCompareMethods:
    """Test methods of TwoModelCompare."""

    def test_difference_for_year(self):
        """Test difference calculation for a specific year."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = TwoModelCompare(model1, model2)
        diff = comparison.difference("revenue", 2020)

        assert diff == 20.0

    def test_repr(self):
        """Test __repr__ method."""
        model1 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 100},
                )
            ],
            years=[2020],
        )
        model2 = Model(
            [
                LineItem(
                    name="revenue",
                    label="Revenue",
                    category="income",
                    values={2020: 120},
                )
            ],
            years=[2020],
        )

        comparison = TwoModelCompare(model1, model2)
        repr_str = repr(comparison)

        assert "TwoModelCompare" in repr_str
        assert "1 common items" in repr_str
        assert "1 common years" in repr_str


class TestTwoModelCompareAccessibility:
    """Test that TwoModelCompare is accessible from main package."""

    def test_two_model_compare_accessible_from_main_package(self):
        """Test that TwoModelCompare is accessible from main pyproforma package."""
        from pyproforma import TwoModelCompare as TMC

        assert TMC is not None
        assert TMC == TwoModelCompare
