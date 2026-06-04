"""
FormulaLine class for calculated line items.
"""

import inspect
from typing import TYPE_CHECKING, Callable, Union

from pyproforma.table import NumberFormatSpec

from .line_item import LineItem

if TYPE_CHECKING:
    from pyproforma.model_namespace import ModelNamespace


# ---------------------------------------------------------------------------
# Precedent recording infrastructure
# ---------------------------------------------------------------------------

class _DummyValue:
    """Numeric mock that survives any operation a formula might perform."""

    def __getitem__(self, key): return self
    def __add__(self, other): return self
    def __radd__(self, other): return self
    def __sub__(self, other): return self
    def __rsub__(self, other): return self
    def __mul__(self, other): return self
    def __rmul__(self, other): return self
    def __truediv__(self, other): return self
    def __rtruediv__(self, other): return self
    def __floordiv__(self, other): return self
    def __rfloordiv__(self, other): return self
    def __pow__(self, other): return self
    def __neg__(self): return self
    def __pos__(self): return self
    def __abs__(self): return self
    def __float__(self): return 1.0
    def __int__(self): return 1
    def __bool__(self): return True
    def __gt__(self, other): return True
    def __lt__(self, other): return False
    def __ge__(self, other): return True
    def __le__(self, other): return False
    def __eq__(self, other): return False
    def __ne__(self, other): return True


class _TagRecorder:
    """Returned by recorder.tag — captures the tag name from the subscript."""

    def __init__(self, seen: set, refs: list):
        self._seen = seen
        self._refs = refs

    def __getitem__(self, tag_name):
        if isinstance(tag_name, str) and tag_name not in self._seen:
            self._seen.add(tag_name)
            self._refs.append(tag_name)
        return _DummyValue()


class _PrecedentRecorder:
    """
    Drop-in replacement for ModelNamespace that records which names are accessed.

    Pass as the `li` argument when calling a formula with a dummy period value.
    After the call, read ._items for direct line item refs and ._tags for tag refs.

    Limitation: formulas that branch on the period value (e.g. `if t > 2025`)
    will only trace the branch taken with t=0.
    """

    def __init__(self):
        self._items: list[str] = []
        self._items_seen: set[str] = set()
        self._tags: list[str] = []
        self._tags_seen: set[str] = set()

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        if name == "tag":
            return _TagRecorder(self._tags_seen, self._tags)
        if name not in self._items_seen:
            self._items_seen.add(name)
            self._items.append(name)
        return _DummyValue()


def _trace_formula(formula: Callable) -> tuple[list[str], list[str]]:
    """Run formula with a recording proxy and return (line_item_refs, tag_refs)."""
    recorder = _PrecedentRecorder()
    try:
        formula(recorder, 0)
    except Exception:
        pass
    return recorder._items, recorder._tags


# ---------------------------------------------------------------------------
# FormulaLine
# ---------------------------------------------------------------------------

class FormulaLine(LineItem):
    """
    A line item with values calculated from a formula.

    The formula receives two parameters:
    - li (ModelNamespace): Unified access to line items (li.revenue[t]) and
      scalar constants (li.tax_rate).
    - t (int): Current period being calculated.

    Examples:
        >>> profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
        >>> expenses = FormulaLine(formula=lambda li, t: li.revenue[t] * li.expense_ratio)
        >>> total = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
    """

    def __init__(
        self,
        formula: "Callable[[ModelNamespace, int], float] | None" = None,
        values: dict[int, float] | None = None,
        label: str | None = None,
        tags: list[str] | None = None,
        value_format: Union[str, NumberFormatSpec, dict, None] = None,
    ):
        super().__init__(label=label, tags=tags, value_format=value_format)
        self.formula = formula
        self.values = values or {}

    @property
    def precedents(self) -> list[str] | None:
        """Names of line items and scalars directly referenced by this formula.

        Uses a recording proxy rather than bytecode inspection, so it works
        across Python versions and correctly excludes tag references.
        Tag-based references are available via tag_references.

        Returns None if no formula is set.

        Examples:
            >>> profit = FormulaLine(formula=lambda li, t: li.revenue[t] - li.expenses[t])
            >>> profit.precedents
            ['revenue', 'expenses']

            >>> total = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
            >>> total.precedents
            []
            >>> total.tag_references
            ['revenue']
        """
        if self.formula is None:
            return None
        items, _ = _trace_formula(self.formula)
        return items

    @property
    def tag_references(self) -> list[str] | None:
        """Tag names used in this formula via li.tag["name"][t].

        Returns None if no formula is set, empty list if formula uses no tags.

        Examples:
            >>> total = FormulaLine(formula=lambda li, t: li.tag["revenue"][t])
            >>> total.tag_references
            ['revenue']
        """
        if self.formula is None:
            return None
        _, tags = _trace_formula(self.formula)
        return tags

    @property
    def formula_source(self) -> str | None:
        """Source code of the formula function, or None if unavailable."""
        if self.formula is None:
            return None
        try:
            source = inspect.getsource(self.formula).strip()
        except OSError:
            return None

        if self.formula.__name__ == "<lambda>":
            idx = source.find("lambda")
            if idx != -1:
                source = source[idx:]
                source = source.rstrip(" ,")
                while source.endswith(")") and source.count("(") < source.count(")"):
                    source = source[:-1].rstrip(" ,")
        return source

    def eval(self, ns: "ModelNamespace", t: int) -> float:
        """Evaluate the formula for a specific period."""
        if self.formula is None:
            raise ValueError(f"No formula defined for '{self.name}'")
        return self.formula(ns, t)

    def get_value(self, period: int) -> float | None:
        if period in self.values:
            return self.values[period]
        return None

    def __repr__(self):
        parts = [f"formula={self.formula!r}"]
        if self.values:
            parts.append(f"values={self.values}")
        if self.label:
            parts.append(f"label={self.label!r}")
        return f"FormulaLine({', '.join(parts)})"
