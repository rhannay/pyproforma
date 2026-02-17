"""
Tests for reserved words validation in v2 API.
"""

import pytest

from pyproforma.v2 import Assumption, FixedLine, FormulaLine, ProformaModel
from pyproforma.v2.reserved_words import RESERVED_WORDS, validate_name


class TestReservedWordsValidation:
    """Tests for reserved words validation function."""

    def test_validate_valid_name(self):
        """Test that valid names pass validation."""
        # Should not raise
        validate_name("revenue")
        validate_name("expenses")
        validate_name("profit")
        validate_name("my_line_item")

    def test_validate_reserved_word_tags(self):
        """Test that 'tags' is reserved."""
        with pytest.raises(ValueError, match="'tags' is a reserved word"):
            validate_name("tags")

    def test_validate_reserved_word_tag(self):
        """Test that 'tag' is reserved."""
        with pytest.raises(ValueError, match="'tag' is a reserved word"):
            validate_name("tag")

    def test_validate_reserved_word_li(self):
        """Test that 'li' is reserved."""
        with pytest.raises(ValueError, match="'li' is a reserved word"):
            validate_name("li")

    def test_validate_reserved_word_av(self):
        """Test that 'av' is reserved."""
        with pytest.raises(ValueError, match="'av' is a reserved word"):
            validate_name("av")

    def test_validate_reserved_word_t(self):
        """Test that 't' is reserved."""
        with pytest.raises(ValueError, match="'t' is a reserved word"):
            validate_name("t")

    def test_validate_reserved_word_tables(self):
        """Test that 'tables' is reserved."""
        with pytest.raises(ValueError, match="'tables' is a reserved word"):
            validate_name("tables")

    def test_validate_reserved_word_periods(self):
        """Test that 'periods' is reserved."""
        with pytest.raises(ValueError, match="'periods' is a reserved word"):
            validate_name("periods")

    def test_validate_python_keywords(self):
        """Test that Python keywords are reserved."""
        with pytest.raises(ValueError, match="'class' is a reserved word"):
            validate_name("class")

        with pytest.raises(ValueError, match="'def' is a reserved word"):
            validate_name("def")

        with pytest.raises(ValueError, match="'return' is a reserved word"):
            validate_name("return")


class TestReservedWordsInModel:
    """Tests for reserved words validation in ProformaModel."""

    def test_reserved_word_line_item_tags(self):
        """Test that using 'tags' as line item name raises error."""
        with pytest.raises(ValueError, match="'tags' is a reserved word"):

            class TestModel(ProformaModel):
                tags = FixedLine(values={2024: 100})

    def test_reserved_word_line_item_li(self):
        """Test that using 'li' as line item name raises error."""
        with pytest.raises(ValueError, match="'li' is a reserved word"):

            class TestModel(ProformaModel):
                li = FixedLine(values={2024: 100})

    def test_reserved_word_line_item_av(self):
        """Test that using 'av' as line item name raises error."""
        with pytest.raises(ValueError, match="'av' is a reserved word"):

            class TestModel(ProformaModel):
                av = FormulaLine(formula=lambda a, li, t: 100)

    def test_reserved_word_assumption_t(self):
        """Test that using 't' as assumption name raises error."""
        with pytest.raises(ValueError, match="'t' is a reserved word"):

            class TestModel(ProformaModel):
                t = Assumption(value=0.21)

    def test_reserved_word_assumption_periods(self):
        """Test that using 'periods' as assumption name raises error."""
        with pytest.raises(ValueError, match="'periods' is a reserved word"):

            class TestModel(ProformaModel):
                periods = Assumption(value=0.1)

    def test_reserved_word_python_keyword(self):
        """Test that Python keywords are in the reserved words list."""
        # Verify that Python keywords are in the reserved words list
        # We can't syntactically use them as attribute names in Python,
        # but the validation function will catch them if someone tries programmatically
        assert "lambda" in RESERVED_WORDS
        assert "class" in RESERVED_WORDS
        assert "return" in RESERVED_WORDS
        assert "def" in RESERVED_WORDS

    def test_valid_names_work(self):
        """Test that valid names are not rejected."""

        class TestModel(ProformaModel):
            revenue = FixedLine(values={2024: 100})
            expenses = FormulaLine(formula=lambda a, li, t: 60)
            tax_rate = Assumption(value=0.21)

        model = TestModel(periods=[2024])
        assert model.li.revenue[2024] == 100
        assert model.li.expenses[2024] == 60
        assert model.av.tax_rate == 0.21


class TestReservedWordsList:
    """Tests for the RESERVED_WORDS constant."""

    def test_reserved_words_contains_key_words(self):
        """Test that RESERVED_WORDS contains expected words."""
        expected_words = {
            "li",
            "av",
            "tags",
            "tag",
            "tables",
            "t",
            "a",
            "periods",
            "period",
            "self",
            "class",
            "def",
            "return",
        }

        for word in expected_words:
            assert word in RESERVED_WORDS, f"'{word}' should be in RESERVED_WORDS"

    def test_reserved_words_is_set(self):
        """Test that RESERVED_WORDS is a set for efficient lookup."""
        assert isinstance(RESERVED_WORDS, set)
