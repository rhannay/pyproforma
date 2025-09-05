# Exceptions
from .charts import ChartGenerationError as ChartGenerationError
from .models import Category as Category
from .models import Constraint as Constraint
from .models import LineItem as LineItem
from .models import Model as Model
from .tables import TableGenerationError as TableGenerationError

# Bringing in row types for easy table generation
from .tables import row_types as row_types

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
