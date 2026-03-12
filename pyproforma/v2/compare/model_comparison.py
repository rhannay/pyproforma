"""
ModelComparison class for comparing two or more v2 ProformaModel instances.
"""

from typing import TYPE_CHECKING, Optional, Union

from pyproforma.table import Cell, Format, Table

if TYPE_CHECKING:
    from pyproforma.v2.proforma_model import ProformaModel


class ModelComparison:
    """
    Compares two or more v2 ProformaModel instances across common line items and periods.

    The first model is the baseline. Differences are calculated as compare - base.
    Common items are the intersection of line_item_names (in base declaration order).
    Common periods are the sorted intersection of periods across all models.

    If all models are the same class, assumption_diff() is also available.

    Args:
        base: The baseline ProformaModel instance.
        *others: One or more comparison ProformaModel instances.
        labels: Display labels for all models including base.
            Defaults to ["Model 1", "Model 2", ...].

    Raises:
        ValueError: If fewer than 2 models, no common periods, or no common items.
        TypeError: If labels length doesn't match model count.

    Examples:
        >>> cmp = ModelComparison(base, optimistic, labels=["Base", "Optimistic"])
        >>> cmp.difference("revenue", 2024)
        20000.0
        >>> cmp.table(["revenue", "expenses", "profit"])
    """

    def __init__(
        self,
        base: "ProformaModel",
        *others: "ProformaModel",
        labels: Optional[list[str]] = None,
    ):
        models = [base] + list(others)
        if len(models) < 2:
            raise ValueError("ModelComparison requires at least 2 models.")

        # Common periods — sorted intersection
        common_periods_set = set(models[0].periods)
        for m in models[1:]:
            common_periods_set &= set(m.periods)
        if not common_periods_set:
            raise ValueError(
                "Models have no common periods. "
                f"Base periods: {models[0].periods}"
            )
        self.common_periods: list[int] = sorted(common_periods_set)

        # Common items — intersection, preserving base declaration order
        common_names_set = set(models[0].line_item_names)
        for m in models[1:]:
            common_names_set &= set(m.line_item_names)
        if not common_names_set:
            raise ValueError(
                "Models have no common line items. "
                f"Base line items: {models[0].line_item_names}"
            )
        self.common_items: list[str] = [
            n for n in models[0].line_item_names if n in common_names_set
        ]

        # Structural metadata
        base_names = set(models[0].line_item_names)
        other_names: set[str] = set()
        for m in models[1:]:
            other_names |= set(m.line_item_names)
        self.base_only_items: list[str] = sorted(base_names - other_names)
        self.compare_only_items: list[str] = sorted(other_names - base_names)

        # Labels
        if labels is None:
            self.labels: list[str] = [f"Model {i + 1}" for i in range(len(models))]
        else:
            if len(labels) != len(models):
                raise TypeError(
                    f"labels length ({len(labels)}) must match model count ({len(models)})"
                )
            self.labels = list(labels)

        self.models = models
        self._same_class = all(type(m) is type(models[0]) for m in models[1:])

    @property
    def base(self) -> "ProformaModel":
        """The baseline model (first model passed to the constructor)."""
        return self.models[0]

    def _validate_item(self, name: str) -> None:
        if name not in self.common_items:
            raise ValueError(
                f"'{name}' is not in common_items. "
                f"Common items: {', '.join(self.common_items)}"
            )

    def difference(
        self, item_name: str, period: Optional[int] = None
    ) -> Union[float, dict]:
        """
        Absolute difference (compare - base) for a line item.

        Return type depends on model count and whether a period is specified:
        - 2 models + period  → float
        - 2 models, no period → {period: float}
        - 3+ models + period  → {label: float}
        - 3+ models, no period → {label: {period: float}}

        Args:
            item_name: Name of the line item (must be in common_items).
            period: Specific period, or None for all common periods.

        Returns:
            float or dict.
        """
        self._validate_item(item_name)
        two_model = len(self.models) == 2

        if period is not None:
            base_val = self.base.get_value(item_name, period)
            if two_model:
                return self.models[1].get_value(item_name, period) - base_val
            return {
                label: self.models[i].get_value(item_name, period) - base_val
                for i, label in enumerate(self.labels[1:], start=1)
            }
        else:
            if two_model:
                return {
                    p: self.models[1].get_value(item_name, p)
                    - self.base.get_value(item_name, p)
                    for p in self.common_periods
                }
            return {
                label: {
                    p: self.models[i].get_value(item_name, p)
                    - self.base.get_value(item_name, p)
                    for p in self.common_periods
                }
                for i, label in enumerate(self.labels[1:], start=1)
            }

    def percent_difference(
        self, item_name: str, period: Optional[int] = None
    ) -> Union[float, None, dict]:
        """
        Percent difference ((compare - base) / base) for a line item.

        Returns None where the base value is zero.
        Same return-type rules as difference().

        Args:
            item_name: Name of the line item (must be in common_items).
            period: Specific period, or None for all common periods.

        Returns:
            float, None, or dict.
        """
        self._validate_item(item_name)
        two_model = len(self.models) == 2

        def _pct(compare_val: float, base_val: float) -> Optional[float]:
            if base_val == 0:
                return None
            return (compare_val - base_val) / base_val

        if period is not None:
            base_val = self.base.get_value(item_name, period)
            if two_model:
                return _pct(self.models[1].get_value(item_name, period), base_val)
            return {
                label: _pct(self.models[i].get_value(item_name, period), base_val)
                for i, label in enumerate(self.labels[1:], start=1)
            }
        else:
            if two_model:
                return {
                    p: _pct(
                        self.models[1].get_value(item_name, p),
                        self.base.get_value(item_name, p),
                    )
                    for p in self.common_periods
                }
            return {
                label: {
                    p: _pct(
                        self.models[i].get_value(item_name, p),
                        self.base.get_value(item_name, p),
                    )
                    for p in self.common_periods
                }
                for i, label in enumerate(self.labels[1:], start=1)
            }

    def assumption_diff(self) -> dict[str, dict[str, float]]:
        """
        Compare assumption values across all models.

        Only available when all models are the same class. Returns values for
        all assumptions common to all models, keyed by assumption name then label.

        Returns:
            {assumption_name: {label: value, ...}, ...}

        Raises:
            TypeError: If models are not all the same class.
        """
        if not self._same_class:
            raise TypeError(
                "assumption_diff() requires all models to be the same class. "
                f"Found: {[type(m).__name__ for m in self.models]}"
            )

        common_assumptions = set(self.models[0].assumption_names)
        for m in self.models[1:]:
            common_assumptions &= set(m.assumption_names)

        return {
            name: {
                label: getattr(self.models[i].av, name)
                for i, label in enumerate(self.labels)
            }
            for name in self.models[0].assumption_names
            if name in common_assumptions
        }

    def table(
        self,
        item_names: Optional[list[str]] = None,
        include_difference: bool = True,
        include_percent_difference: bool = False,
    ) -> Table:
        """
        Generate a comparison table showing values for each model side by side.

        For each item the table contains:
        - A bold label row (item display label)
        - One value row per model
        - An absolute difference row per comparison model (optional, default on)
        - A percent difference row per comparison model (optional, default off)
        - A blank separator row

        Columns are the common periods.

        Args:
            item_names: Items to include. Defaults to all common_items.
            include_difference: Show absolute difference rows. Defaults to True.
            include_percent_difference: Show percent difference rows. Defaults to False.

        Returns:
            Table

        Raises:
            ValueError: If any requested item is not in common_items.
        """
        if item_names is None:
            items = self.common_items
        else:
            for name in item_names:
                self._validate_item(name)
            items = item_names

        two_model = len(self.models) == 2
        all_rows: list[list[Cell]] = []

        # Header row
        header = [Cell(value="", bold=True, align="left")]
        for period in self.common_periods:
            header.append(Cell(value=period, bold=True, align="center", value_format=None))
        all_rows.append(header)

        for item_name in items:
            item_result = self.base[item_name]
            item_label = item_result.label or item_name
            value_format = item_result.value_format

            # Item label row
            label_row = [Cell(value=item_label, bold=True, align="left")]
            label_row += [Cell(value="") for _ in self.common_periods]
            all_rows.append(label_row)

            # One value row per model
            for model, label in zip(self.models, self.labels):
                row = [Cell(value=label, align="left")]
                for period in self.common_periods:
                    row.append(Cell(value=model.get_value(item_name, period), value_format=value_format))
                all_rows.append(row)

            # Difference row(s)
            if include_difference:
                compare_pairs = list(enumerate(self.labels[1:], start=1))
                for i, label in compare_pairs:
                    diff_label = "Difference" if two_model else f"Diff: {label}"
                    diff_row = [Cell(value=diff_label, align="left")]
                    for period in self.common_periods:
                        diff = (
                            self.models[i].get_value(item_name, period)
                            - self.base.get_value(item_name, period)
                        )
                        diff_row.append(Cell(value=diff, value_format=value_format))
                    all_rows.append(diff_row)

            # Percent difference row(s)
            if include_percent_difference:
                compare_pairs = list(enumerate(self.labels[1:], start=1))
                for i, label in compare_pairs:
                    pct_label = "% Difference" if two_model else f"% Diff: {label}"
                    pct_row = [Cell(value=pct_label, align="left")]
                    for period in self.common_periods:
                        base_val = self.base.get_value(item_name, period)
                        compare_val = self.models[i].get_value(item_name, period)
                        pct = (compare_val - base_val) / base_val if base_val != 0 else None
                        pct_row.append(Cell(value=pct, value_format=Format.PERCENT_TWO_DECIMALS))
                    all_rows.append(pct_row)

            # Blank separator
            all_rows.append([Cell(value="") for _ in range(1 + len(self.common_periods))])

        return Table(cells=all_rows)

    def __repr__(self) -> str:
        return (
            f"ModelComparison("
            f"models={len(self.models)}, "
            f"common_items={len(self.common_items)}, "
            f"common_periods={self.common_periods})"
        )
