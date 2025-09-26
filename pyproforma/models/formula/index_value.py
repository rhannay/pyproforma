class IndexValue:
    """
    A class that holds a value and a dictionary for indexed access.

    When accessed directly, returns the value.
    When accessed with an index (like [-1] or ['a']), returns the corresponding
    element from the dict.

    Args:
        value: The primary value to return when accessed directly
        index_dict: Dictionary containing indexed values

    Examples:
        >>> iv = IndexValue("main_value", {-1: "last", "a": "first"})
        >>> str(iv)  # Returns "main_value"
        >>> iv[-1]   # Returns "last"
        >>> iv["a"]  # Returns "first"
    """

    def __init__(self, value, index_dict=None):
        """
        Initialize IndexValue with a value and optional index dictionary.

        Args:
            value: The primary value
            index_dict: Dictionary for indexed access (defaults to empty dict if None)
        """
        self.value = value
        self.index_dict = index_dict if index_dict is not None else {}

    def __getitem__(self, key):
        """
        Return element from index_dict when accessed with an index.

        Args:
            key: The key to look up in the index dictionary

        Returns:
            The value from index_dict corresponding to the key

        Raises:
            KeyError: If the key is not found in the index dictionary
        """
        return self.index_dict[key]

    def __str__(self):
        """Return the primary value as a string."""
        return str(self.value)

    def __repr__(self):
        """Return a detailed representation of the IndexValue."""
        return f"IndexValue(value={self.value!r}, index_dict={self.index_dict!r})"

    def __eq__(self, other):
        """Check equality based on the primary value."""
        if isinstance(other, IndexValue):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        """Make IndexValue hashable based on the primary value."""
        return hash(self.value)

    def __float__(self):
        """Convert to float."""
        return float(self.value)

    def __int__(self):
        """Convert to int."""
        return int(self.value)

    def __bool__(self):
        """Convert to boolean."""
        return bool(self.value)

    def __lt__(self, other):
        """Less than comparison."""
        if isinstance(other, IndexValue):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        """Less than or equal comparison."""
        if isinstance(other, IndexValue):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        """Greater than comparison."""
        if isinstance(other, IndexValue):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other):
        """Greater than or equal comparison."""
        if isinstance(other, IndexValue):
            return self.value >= other.value
        return self.value >= other

    def __add__(self, other):
        """Addition."""
        if isinstance(other, IndexValue):
            return self.value + other.value
        return self.value + other

    def __radd__(self, other):
        """Reverse addition."""
        return other + self.value

    def __sub__(self, other):
        """Subtraction."""
        if isinstance(other, IndexValue):
            return self.value - other.value
        return self.value - other

    def __rsub__(self, other):
        """Reverse subtraction."""
        return other - self.value

    def __mul__(self, other):
        """Multiplication."""
        if isinstance(other, IndexValue):
            return self.value * other.value
        return self.value * other

    def __rmul__(self, other):
        """Reverse multiplication."""
        return other * self.value

    def __truediv__(self, other):
        """Division."""
        if isinstance(other, IndexValue):
            return self.value / other.value
        return self.value / other

    def __rtruediv__(self, other):
        """Reverse division."""
        return other / self.value

    def __floordiv__(self, other):
        """Floor division."""
        if isinstance(other, IndexValue):
            return self.value // other.value
        return self.value // other

    def __rfloordiv__(self, other):
        """Reverse floor division."""
        return other // self.value

    def __mod__(self, other):
        """Modulo."""
        if isinstance(other, IndexValue):
            return self.value % other.value
        return self.value % other

    def __rmod__(self, other):
        """Reverse modulo."""
        return other % self.value

    def __pow__(self, other):
        """Power."""
        if isinstance(other, IndexValue):
            return self.value**other.value
        return self.value**other

    def __rpow__(self, other):
        """Reverse power."""
        return other**self.value

    def __neg__(self):
        """Negation."""
        return -self.value

    def __pos__(self):
        """Positive."""
        return +self.value

    def __abs__(self):
        """Absolute value."""
        return abs(self.value)
