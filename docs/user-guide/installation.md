# Installation

## Requirements

PyProforma requires Python 3.9 or higher and the following dependencies:

- pandas >= 1.3.0
- openpyxl >= 3.0.0
- numexpr >= 2.7.0
- jinja2 >= 3.0.0
- plotly >= 5.0.0
- PyYAML >= 6.0.0

## Installation from PyPI

The recommended way to install PyProforma is via pip:

```bash
pip install pyproforma
```

This will install PyProforma and all its required dependencies.

## Installing from Source

If you prefer to install from source:

```bash
git clone https://github.com/rhannay/pyproforma.git
cd pyproforma
pip install -e .
```

## Verifying Installation

To verify that PyProforma is installed correctly, you can import it in Python:

```python
import pyproforma
print(pyproforma.__version__)
```

This should print the current version of PyProforma.
