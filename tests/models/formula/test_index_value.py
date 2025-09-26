"""Tests for IndexValue class."""

import pytest

from pyproforma.models.formula.index_value import IndexValue


class TestIndexValue:
    """Test cases for IndexValue class."""

    def test_init_with_int_value_and_dict(self):
        """Test initialization with integer value and dictionary."""
        value = 100
        index_dict = {-1: 50, -2: 75, -3: 25}
        iv = IndexValue(value, index_dict)

        assert iv.value == 100
        assert iv.index_dict == {-1: 50, -2: 75, -3: 25}

    def test_init_with_float_value_and_dict(self):
        """Test initialization with float value and dictionary."""
        value = 100.5
        index_dict = {-1: 50.25, -2: 75.75, -3: 25.0}
        iv = IndexValue(value, index_dict)

        assert iv.value == 100.5
        assert iv.index_dict == {-1: 50.25, -2: 75.75, -3: 25.0}

    def test_init_without_dict(self):
        """Test initialization without providing index dictionary."""
        iv = IndexValue(42)

        assert iv.value == 42
        assert iv.index_dict == {}

    def test_init_with_none_dict(self):
        """Test initialization with explicit None dictionary."""
        iv = IndexValue(42, None)

        assert iv.value == 42
        assert iv.index_dict == {}

    def test_getitem_with_negative_indexes(self):
        """Test accessing values using negative indexes."""
        iv = IndexValue(100, {-1: 90, -2: 80, -3: 70})

        assert iv[-1] == 90
        assert iv[-2] == 80
        assert iv[-3] == 70

    def test_getitem_with_float_values(self):
        """Test accessing float values using negative indexes."""
        iv = IndexValue(100.0, {-1: 90.5, -2: 80.25, -3: 70.75})

        assert iv[-1] == 90.5
        assert iv[-2] == 80.25
        assert iv[-3] == 70.75

    def test_getitem_keyerror(self):
        """Test that KeyError is raised for non-existent keys."""
        iv = IndexValue(100, {-1: 90, -2: 80})

        with pytest.raises(KeyError):
            _ = iv[-3]

        with pytest.raises(KeyError):
            _ = iv[-10]

    def test_str_with_int(self):
        """Test string representation with integer value."""
        iv = IndexValue(42, {-1: 30, -2: 20})

        assert str(iv) == "42"

    def test_str_with_float(self):
        """Test string representation with float value."""
        iv = IndexValue(42.5, {-1: 30.25, -2: 20.75})

        assert str(iv) == "42.5"

    def test_repr(self):
        """Test detailed representation."""
        iv = IndexValue(100, {-1: 90, -2: 80})
        expected = "IndexValue(value=100, index_dict={-1: 90, -2: 80})"

        assert repr(iv) == expected

    def test_repr_with_float(self):
        """Test detailed representation with float values."""
        iv = IndexValue(100.5, {-1: 90.25, -2: 80.75})
        expected = "IndexValue(value=100.5, index_dict={-1: 90.25, -2: 80.75})"

        assert repr(iv) == expected

    def test_equality_same_values(self):
        """Test equality between IndexValue objects with same values."""
        iv1 = IndexValue(100, {-1: 90, -2: 80})
        iv2 = IndexValue(100, {-1: 50, -2: 60})  # Different dict, same value

        assert iv1 == iv2

    def test_equality_different_values(self):
        """Test inequality between IndexValue objects with different values."""
        iv1 = IndexValue(100, {-1: 90, -2: 80})
        iv2 = IndexValue(200, {-1: 90, -2: 80})  # Same dict, different value

        assert iv1 != iv2

    def test_equality_with_numeric_types(self):
        """Test equality with raw numeric values."""
        iv_int = IndexValue(100, {-1: 90})
        iv_float = IndexValue(100.0, {-1: 90.0})

        assert iv_int == 100
        assert iv_int == 100.0
        assert iv_float == 100
        assert iv_float == 100.0

    def test_equality_with_different_numeric_types(self):
        """Test inequality with different numeric values."""
        iv = IndexValue(100, {-1: 90})

        assert iv != 99
        assert iv != 101
        assert iv != 100.1

    def test_hash_consistency(self):
        """Test that hash is based on value and consistent."""
        iv1 = IndexValue(100, {-1: 90, -2: 80})
        iv2 = IndexValue(100, {-1: 50, -2: 60})  # Different dict, same value

        assert hash(iv1) == hash(iv2)

    def test_hash_different_values(self):
        """Test that different values produce different hashes."""
        iv1 = IndexValue(100, {-1: 90})
        iv2 = IndexValue(200, {-1: 90})

        assert hash(iv1) != hash(iv2)

    def test_hashable_in_set(self):
        """Test that IndexValue can be used in sets."""
        iv1 = IndexValue(100, {-1: 90})
        iv2 = IndexValue(100, {-2: 80})  # Same value, different dict
        iv3 = IndexValue(200, {-1: 90})

        value_set = {iv1, iv2, iv3}

        # Should only have 2 unique values (100 and 200)
        assert len(value_set) == 2
        assert iv1 in value_set
        assert iv3 in value_set

    def test_hashable_as_dict_key(self):
        """Test that IndexValue can be used as dictionary keys."""
        iv1 = IndexValue(100, {-1: 90})
        iv2 = IndexValue(200, {-1: 80})

        test_dict = {iv1: "first", iv2: "second"}

        assert test_dict[iv1] == "first"
        assert test_dict[iv2] == "second"

    def test_multiple_negative_indexes(self):
        """Test with multiple negative indexes and mixed numeric types."""
        index_dict = {-1: 100, -2: 95.5, -3: 90, -4: 85.25, -5: 80, -10: 75.0}
        iv = IndexValue(120.5, index_dict)

        assert iv[-1] == 100
        assert iv[-2] == 95.5
        assert iv[-3] == 90
        assert iv[-4] == 85.25
        assert iv[-5] == 80
        assert iv[-10] == 75.0

    def test_zero_values(self):
        """Test with zero values."""
        iv = IndexValue(0, {-1: 0, -2: 0.0})

        assert iv.value == 0
        assert iv[-1] == 0
        assert iv[-2] == 0.0
        assert str(iv) == "0"

    def test_negative_values(self):
        """
        Test with negative numeric values (not to be confused with negative indexes).
        """
        iv = IndexValue(-50, {-1: -25, -2: -30.5})

        assert iv.value == -50
        assert iv[-1] == -25
        assert iv[-2] == -30.5
        assert str(iv) == "-50"

    def test_large_negative_indexes(self):
        """Test with large negative index values."""
        iv = IndexValue(1000, {-100: 500, -1000: 250, -10000: 125.5})

        assert iv[-100] == 500
        assert iv[-1000] == 250
        assert iv[-10000] == 125.5

    def test_empty_dict_access(self):
        """Test accessing index on empty dictionary raises KeyError."""
        iv = IndexValue(100)

        with pytest.raises(KeyError):
            _ = iv[-1]

    def test_direct_value_access(self):
        """Test that IndexValue behaves like its underlying value."""
        iv = IndexValue(5.0, {-1: 3.0, -2: 2.0})

        # Direct equality comparison
        assert iv == 5.0
        assert 5.0 == iv

        # Type conversion
        assert float(iv) == 5.0
        assert int(iv) == 5

    def test_arithmetic_operations(self):
        """Test arithmetic operations with IndexValue."""
        iv1 = IndexValue(10.0, {-1: 5.0})
        iv2 = IndexValue(3.0, {-1: 1.0})

        # Addition
        assert iv1 + iv2 == 13.0
        assert iv1 + 5 == 15.0
        assert 5 + iv1 == 15.0

        # Subtraction
        assert iv1 - iv2 == 7.0
        assert iv1 - 2 == 8.0
        assert 12 - iv1 == 2.0

        # Multiplication
        assert iv1 * iv2 == 30.0
        assert iv1 * 2 == 20.0
        assert 3 * iv1 == 30.0

        # Division
        assert iv1 / iv2 == 10.0 / 3.0
        assert iv1 / 2 == 5.0
        assert 20 / iv1 == 2.0

    def test_comparison_operations(self):
        """Test comparison operations with IndexValue."""
        iv = IndexValue(10.0, {-1: 5.0})

        # Less than
        assert iv < 15
        assert 5 < iv
        assert not (iv < 5)

        # Greater than
        assert iv > 5
        assert 15 > iv
        assert not (iv > 15)

        # Less than or equal
        assert iv <= 10
        assert iv <= 15
        assert 5 <= iv

        # Greater than or equal
        assert iv >= 10
        assert iv >= 5
        assert 15 >= iv

    def test_unary_operations(self):
        """Test unary operations with IndexValue."""
        iv_positive = IndexValue(5.0, {-1: 3.0})
        iv_negative = IndexValue(-5.0, {-1: -3.0})

        # Negation
        assert -iv_positive == -5.0
        assert -iv_negative == 5.0

        # Positive
        assert +iv_positive == 5.0
        assert +iv_negative == -5.0

        # Absolute value
        assert abs(iv_positive) == 5.0
        assert abs(iv_negative) == 5.0

    def test_boolean_conversion(self):
        """Test boolean conversion of IndexValue."""
        iv_zero = IndexValue(0, {-1: 5})
        iv_nonzero = IndexValue(5.0, {-1: 3.0})

        assert not bool(iv_zero)
        assert bool(iv_nonzero)

        # Test in conditional context
        if iv_nonzero:
            result = "truthy"
        else:
            result = "falsy"
        assert result == "truthy"

        if iv_zero:
            result = "truthy"
        else:
            result = "falsy"
        assert result == "falsy"

    def test_power_operations(self):
        """Test power operations with IndexValue."""
        iv = IndexValue(2.0, {-1: 1.0})

        # Power
        assert iv**3 == 8.0
        assert 3**iv == 9.0

        # With IndexValue
        iv2 = IndexValue(3.0, {-1: 2.0})
        assert iv**iv2 == 8.0

    def test_modulo_operations(self):
        """Test modulo operations with IndexValue."""
        iv = IndexValue(10.0, {-1: 5.0})

        assert iv % 3 == 1.0
        assert 13 % iv == 3.0

        iv2 = IndexValue(3.0, {-1: 1.0})
        assert iv % iv2 == 1.0

    def test_floor_division(self):
        """Test floor division with IndexValue."""
        iv = IndexValue(10.0, {-1: 5.0})

        assert iv // 3 == 3.0
        assert 25 // iv == 2.0

        iv2 = IndexValue(3.0, {-1: 1.0})
        assert iv // iv2 == 3.0
