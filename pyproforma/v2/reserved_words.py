"""
Reserved words that cannot be used as line item or assumption names.

These words are reserved because they are used internally by the ProformaModel
system or would create conflicts with namespaces, properties, or methods.
"""

# Reserved words that cannot be used as line item or assumption names
RESERVED_WORDS = {
    # Namespace accessors
    "li",  # LineItemValues namespace
    "av",  # AssumptionValues namespace
    "tags",  # Tags namespace accessor
    "tag",  # Singular form of tags
    "tables",  # Tables namespace
    
    # Formula parameters
    "t",  # Period/time parameter in formulas
    "a",  # Assumption values parameter in formulas
    
    # Model properties and methods
    "periods",  # Model periods list
    "period",  # Singular form
    "line_item_names",  # Model property
    "assumption_names",  # Model property
    "get_value",  # Model method
    
    # Python/common reserved words to prevent confusion
    "self",
    "class",
    "def",
    "return",
    "import",
    "from",
    "as",
    "for",
    "while",
    "if",
    "else",
    "elif",
    "try",
    "except",
    "finally",
    "with",
    "lambda",
    "yield",
    "global",
    "nonlocal",
    "assert",
    "pass",
    "break",
    "continue",
    "raise",
    "del",
    "True",
    "False",
    "None",
    "and",
    "or",
    "not",
    "is",
    "in",
}


def validate_name(name: str) -> None:
    """
    Validate that a line item or assumption name is not a reserved word.

    Args:
        name (str): The name to validate

    Raises:
        ValueError: If the name is a reserved word

    Examples:
        >>> validate_name("revenue")  # OK
        >>> validate_name("tags")  # Raises ValueError
        >>> validate_name("li")  # Raises ValueError
    """
    if name in RESERVED_WORDS:
        raise ValueError(
            f"'{name}' is a reserved word and cannot be used as a line item or "
            f"assumption name. Reserved words include namespace accessors (li, av, "
            f"tags, tables), formula parameters (t, a), model properties (periods), "
            f"and Python keywords."
        )
