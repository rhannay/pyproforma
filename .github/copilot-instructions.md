# PyProforma Coding Instructions

## Project Overview
PyProforma is a Python financial modeling framework for building pro forma statements with formulas, categories, constraints, and rich output formatting. Users create models using `LineItem` specifications (with values or formulas) organized into `Category` groups, then calculate results and render to tables/charts.

## Core Architecture

### Model Evaluation Flow
1. **Specification Phase**: Users define `LineItem` objects with `values` dicts or `formula` strings
2. **Value Matrix Generation**: `generate_value_matrix()` resolves all formulas into a complete year×variable matrix by topologically sorting dependencies
3. **Results Layer**: The value matrix is wrapped in `LineItemResults`, `CategoryResults`, etc. for exploration and output
4. **Output Generation**: `Tables` and `Charts` namespaces generate formatted HTML/Excel and Plotly visualizations

**Key files**: [pyproforma/models/model/value_matrix.py](pyproforma/models/model/value_matrix.py), [pyproforma/models/model/model.py](pyproforma/models/model/model.py)

### Formula System (AST-based)
Formulas are Python expressions evaluated safely via AST parsing. The system supports:
- **Variable references**: `"revenue - expenses"`
- **Time offsets**: `"revenue[-1] * 1.1"` (only negative offsets; positive/zero forbidden to prevent circular refs)
- **Category totals**: `"category_total:revenue"` 
- **Generator fields**: `"debt:interest"` (references fields from `Generator` components)

**Validation**: `validate_formula()` checks for undefined variables, circular refs, and invalid time offsets at model creation.  
**Evaluation**: AST nodes are walked recursively in `evaluate_formula()`, replacing Name/Subscript nodes with matrix lookups.

**Key file**: [pyproforma/models/formula.py](pyproforma/models/formula.py)

### Results vs Specifications
Critical distinction:
- **Specification classes** (`LineItem`, `Category`, `Constraint`, `Generator`): Define structure, stored in metadata dicts
- **Results classes** (`LineItemResults`, `CategoryResults`, etc.): Provide analysis methods over calculated values from the value matrix

Access via: `model.line_item("name")` returns `LineItemResults`, not the original `LineItem` spec.

## Testing Conventions

### Fixture Pattern
Use `conftest.py` fixtures for common test data:
```python
@pytest.fixture
def sample_line_item_set() -> Model:
    return Model([LineItem(...), LineItem(...)], years=[2020, 2021])
```

**Key file**: [tests/conftest.py](tests/conftest.py)

### Test Organization
- Tests mirror `pyproforma/` structure: `tests/models/`, `tests/tables/`, `tests/charts/`
- Name tests descriptively: `test_validate_formula_circular_reference()` not `test_error()`
- Use pytest class-based grouping for related tests: `class TestTableTranspose`

### Running Tests
```powershell
pytest                          # All tests
pytest tests/models/            # Specific directory
pytest -k "formula"             # Keyword filter
pytest --disable-warnings -v    # Configured defaults in pyproject.toml
```

## Development Workflows

### Local Development Setup
```powershell
# Create and activate virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows PowerShell
# source venv/bin/activate      # Linux/Mac

# Install package and dependencies
pip install -e .                # Editable install
pip install pytest pytest-cov   # Dev dependencies
```

### Code Formatting & Linting
This project uses **Ruff** for both linting and formatting:
- **Line length**: 88 characters
- **Import sorting**: Enforced via `isort` rules
- **Quote style**: Double quotes
- **Linting**: Pycodestyle (E/W), Pyflakes (F), and import sorting (I)

```powershell
ruff check .                    # Lint entire project
ruff check --fix .              # Auto-fix linting issues
ruff format .                   # Format code
```

Configuration in `[tool.ruff]` section of [pyproject.toml](pyproject.toml).

### Adding New LineItem Features
1. Update `LineItem` dataclass in [pyproforma/models/line_item.py](pyproforma/models/line_item.py)
2. Update metadata generation in [pyproforma/models/metadata/line_item.py](pyproforma/models/metadata/line_item.py)
3. Add analysis methods to `LineItemResults` in [pyproforma/models/results/line_item_results.py](pyproforma/models/results/line_item_results.py)
4. Update validation in [pyproforma/models/model/validations.py](pyproforma/models/model/validations.py)

### Creating New Generator Types
Generators produce multiple fields accessible via `"generator_name:field"` formulas:
1. Subclass `Generator` from [pyproforma/models/generator/abc_class.py](pyproforma/models/generator/abc_class.py)
2. Implement `defined_names` property (returns field names without prefix)
3. Implement `get_values(years)` returning `{field: {year: value}}`
4. Register with `@Generator.register("your_type")` decorator

See existing debt generator for reference pattern.

## Table System Specifics

### Row Configuration Pattern
Tables use a template-based system with row type classes:
- `ItemRow`: Single line item values across years
- `CategoryTotalRow`: Category sum with optional styling
- `BlankRow`: Spacing
- `CumulativeChangeRow`: Period-over-period analysis

**Define templates as**:
```python
template = [
    {"row_type": "item", "item_name": "revenue"},
    {"row_type": "blank"},
    {"row_type": "category_total", "category": "income"}
]
model.tables.from_template(template)
```

**Key files**: [pyproforma/tables/row_types.py](pyproforma/tables/row_types.py), [pyproforma/tables/table_generator.py](pyproforma/tables/table_generator.py)

### Cell Formatting
The `Cell` class stores values + styling (bold, borders, alignment, colors). `ValueFormat` controls number display:
- `"no_decimals"`: `1000` → `"1,000"`
- `"percent"`: `0.25` → `"25%"`
- `"two_decimals"`: `1000` → `"1,000.00"`

**Key file**: [pyproforma/table/table_class.py](pyproforma/table/table_class.py)

## Common Pitfalls

1. **Empty Years**: Models can exist without years for templates, but calculations/tables require `model.years` to be non-empty
2. **Circular References**: Formulas like `"profit - profit"` or `"revenue[0]"` are invalid; use `"revenue[-1]"` for lookback
3. **Value Matrix Immutability**: After calculation, the matrix is frozen; use `model.update` namespace to recalculate
4. **Category Auto-inference**: If `categories=None`, categories are auto-created from line item `category` strings
5. **Generator Field Naming**: Store as `"generator_name.field"` in matrix, access via `"generator_name:field"` in formulas

## Documentation
- User docs built with MkDocs Material: [docs/](docs/)
- API reference auto-generated from docstrings
- Examples in [examples/](examples/) demonstrate common patterns
- Notebooks in [docs/examples/](docs/examples/) for interactive guides
