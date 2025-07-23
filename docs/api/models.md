# Models API

The Models API is the core of PyProforma, providing classes for creating and manipulating financial models.

## Model Class

The `Model` class is the main entry point for creating financial models.

```python
from pyproforma import Model
```

### Creating a Model

```python
model = Model(periods=5)  # Create a model with 5 periods
```

### Methods

#### add_line_item

Add a line item to the model.

```python
model.add_line_item(name, values=None, metadata=None)
```

**Parameters:**

- `name` (str): The name of the line item
- `values` (list, optional): Initial values for the line item
- `metadata` (dict, optional): Additional metadata for the line item

**Example:**

```python
model.add_line_item("revenue", [100, 120, 140, 160, 180])
```

#### add_formula

Add a formula to the model.

```python
model.add_formula(name, formula_string, metadata=None)
```

**Parameters:**

- `name` (str): The name of the line item to create from this formula
- `formula_string` (str): The formula expression
- `metadata` (dict, optional): Additional metadata for the line item

**Example:**

```python
model.add_formula("profit", "revenue - expenses")
```

#### add_constraint

Add a constraint to the model.

```python
model.add_constraint(constraint)
```

**Parameters:**

- `constraint` (Constraint): A constraint object

**Example:**

```python
from pyproforma import Constraint

constraint = Constraint("profit > 0", "Profit must be positive")
model.add_constraint(constraint)
```

#### calculate

Calculate the model and return the results.

```python
results = model.calculate()
```

**Returns:**

- `Results`: A results object containing all calculated values

## LineItem Class

The `LineItem` class represents a time series of values in a financial model.

```python
from pyproforma import LineItem
```

### Creating a LineItem

```python
line_item = LineItem(name, values=None, metadata=None)
```

**Parameters:**

- `name` (str): The name of the line item
- `values` (list, optional): Values for each period
- `metadata` (dict, optional): Additional metadata

### Methods

#### set_values

Set values for the line item.

```python
line_item.set_values([100, 120, 140])
```

#### get_values

Get the current values of the line item.

```python
values = line_item.get_values()
```

## Formula Class

The `Formula` class represents a calculation rule in a financial model.

```python
from pyproforma import Formula
```

### Creating a Formula

```python
formula = Formula(name, formula_string, metadata=None)
```

**Parameters:**

- `name` (str): The name of the line item this formula produces
- `formula_string` (str): The formula expression
- `metadata` (dict, optional): Additional metadata

## Results Class

The `Results` class contains the calculated values from a model.

```python
# After calculating a model
results = model.calculate()
```

### Methods

#### get_value

Get the calculated values for a line item.

```python
profit_values = results.get_value("profit")
```

#### get_all_values

Get all calculated values as a dictionary.

```python
all_values = results.get_all_values()
```

#### to_dataframe

Convert results to a pandas DataFrame.

```python
df = results.to_dataframe()
```
