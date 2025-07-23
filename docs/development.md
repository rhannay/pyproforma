# Development Guide

This guide provides information for developers who want to contribute to PyProforma.

## Setting Up Development Environment

1. Clone the repository:

   ```bash
   git clone https://github.com/rhannay/pyproforma.git
   cd pyproforma
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in development mode:

   ```bash
   pip install -e ".[dev]"
   ```

## Project Structure

The PyProforma project is organized as follows:

```
pyproforma/
├── __init__.py         # Package initialization
├── constants.py        # Package-wide constants
├── data_import.py      # Data import functionality
├── charts/             # Chart generation modules
├── models/             # Core modeling functionality
│   ├── __init__.py
│   ├── line_item.py    # Line item definition
│   ├── formula.py      # Formula processing
│   ├── constraint.py   # Model constraints
│   ├── model/          # Model implementation
│   └── ...
└── tables/             # Table generation
    ├── table_class.py  # Table definitions
    ├── excel.py        # Excel export functionality
    └── ...
```

## Running Tests

PyProforma uses pytest for testing. To run the tests:

```bash
pytest
```

To run tests with coverage information:

```bash
pytest --cov=pyproforma
```

## Code Style

PyProforma follows PEP 8 style guidelines. Before submitting a pull request, ensure your code is properly formatted.

## Building Documentation

PyProforma uses MkDocs for documentation. To build and serve the documentation locally:

```bash
mkdocs serve
```

This will start a local server at http://127.0.0.1:8000/ where you can preview the documentation.

To build the documentation site:

```bash
mkdocs build
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new git tag
4. Build the distribution packages
5. Upload to PyPI

```bash
# Update version in pyproject.toml
git add pyproject.toml
git commit -m "Bump version to x.x.x"

# Create git tag
git tag -a vx.x.x -m "Version x.x.x"
git push origin vx.x.x

# Build packages
python -m build

# Upload to PyPI
twine upload dist/pyproforma-x.x.x*
```

## Contributing

Contributions to PyProforma are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.
