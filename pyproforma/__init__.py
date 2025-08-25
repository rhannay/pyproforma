from .models import Category, Constraint, LineItem, Model

# Bringing in row types for easy table generation
from .tables import row_types

# Version information
try:
    from importlib.metadata import version
    __version__ = version("pyproforma")
except ImportError:
    # Fallback for older Python versions
    try:
        from importlib_metadata import version
        __version__ = version("pyproforma")
    except ImportError:
        __version__ = "unknown"
