import re


def validate_name(name):
    """Validate that a name contains only letters, numbers, underscores, or hyphens.

    Args:
        name (str): The name to validate

    Raises:
        ValueError: If the name contains invalid characters
    """
    if not re.match(r"^[A-Za-z0-9_-]+$", name):
        raise ValueError(
            "Name must only contain letters, numbers, underscores, "
            "or hyphens (no spaces or special characters)."
        )
