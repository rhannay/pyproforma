from typing import Literal

# Reserved category names that cannot be used by users
RESERVED_CATEGORY_NAMES = ["category_totals"]

# Valid column types for tables
VALID_COLS = ["label", "name", "category"]

# Type alias for valid column types (based on VALID_COLS constant)
# Note: Using explicit Literal since dynamic Literal is not supported at runtime
ColumnType = Literal["label", "name", "category"]

# Constraint operator symbols mapping
CONSTRAINT_OPERATOR_SYMBOLS = {
    "eq": "=",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
    "ne": "!=",
}
