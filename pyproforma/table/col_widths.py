"""Standard column widths for model-generated tables.

Tables built through the model (Tables namespace, ModelComparison, the
explorer's scenario tables) share one column-width convention so stacked
tables line up and Excel exports match. Widths are stored on the Table in
pixels; each renderer converts as needed (Excel divides by 7 for character
units, HTML emits <col style="width:Npx">).
"""

# Label / row-header column width, and each period column width, in pixels.
LABEL_COL_PX = 245
PERIOD_COL_PX = 105


def standard_col_widths(label_cols: int, n_periods: int) -> list[int]:
    """Build a col_widths list: `label_cols` label columns then `n_periods` period columns."""
    return [LABEL_COL_PX] * label_cols + [PERIOD_COL_PX] * n_periods
