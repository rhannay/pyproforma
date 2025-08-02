# PyProforma: Revenues and Expenses Financial Model Example

This notebook demonstrates how to use the `pyproforma` library to build a comprehensive financial model with multiple revenue streams and expense categories. We'll create line items, organize them into categories, and generate summary tables and visualizations.

## Overview

We'll build a 3-year financial model (2024-2026) that includes:
- **Multiple Revenue Streams**: Product sales, service revenue, licensing fees
- **Multiple Expense Categories**: Cost of goods sold, operating expenses, marketing
- **Automatic Calculations**: Formulas linking expenses to revenues
- **Summary Tables**: Professional financial statement formatting
- **Interactive Charts**: Visual representation of financial data

## 1. Import Required Libraries

First, let's import the necessary components from pyproforma and other supporting libraries.


```python
# Core pyproforma imports
from pyproforma import Model, LineItem, Category

# Additional imports for data manipulation and display
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display, HTML

print("✅ Libraries imported successfully")
```

## 2. Define Model Parameters

Let's set up the basic parameters for our financial model.


```python
# Define the years for our model
MODEL_YEARS = [2024, 2025, 2026]

print(f"📅 Model will cover years: {MODEL_YEARS}")
print(f"📊 Total planning horizon: {len(MODEL_YEARS)} years")
```

## 3. Create Revenue Line Items

We'll create multiple revenue streams with different growth patterns and calculation methods.


```python
# Product Sales Revenue - Base values with 15% annual growth
product_sales = LineItem(
    name="product_sales",
    label="Product Sales",
    category="revenue",
    values={2024: 1_500_000},  # Starting value
    formula="product_sales[-1] * 1.15",  # 15% year-over-year growth
    value_format="no_decimals"
)

# Service Revenue - More conservative 10% growth
service_revenue = LineItem(
    name="service_revenue",
    label="Service Revenue",
    category="revenue",
    values={2024: 800_000},
    formula="service_revenue[-1] * 1.10",  # 10% year-over-year growth
    value_format="no_decimals"
)

# Licensing Fees - Percentage of product sales
licensing_fees = LineItem(
    name="licensing_fees",
    label="Licensing Fees",
    category="revenue",
    formula="product_sales * 0.05",  # 5% of product sales
    value_format="no_decimals"
)

# Subscription Revenue - Growing subscriber base
subscription_revenue = LineItem(
    name="subscription_revenue",
    label="Subscription Revenue",
    category="revenue",
    values={2024: 300_000},
    formula="subscription_revenue[-1] * 1.25",  # 25% growth (aggressive)
    value_format="no_decimals"
)

revenue_items = [product_sales, service_revenue, licensing_fees, subscription_revenue]

print("✅ Revenue line items created:")
for item in revenue_items:
    print(f"   • {item.label}")
```

## 4. Create Expense Line Items

Now let's create various expense categories that scale with our revenue or have independent growth patterns.


```python
# Cost of Goods Sold - Percentage of product sales
cost_of_goods_sold = LineItem(
    name="cost_of_goods_sold",
    label="Cost of Goods Sold",
    category="expenses",
    formula="product_sales * 0.35",  # 35% of product sales
    value_format="no_decimals"
)

# Service Delivery Costs - Percentage of service revenue
service_costs = LineItem(
    name="service_costs",
    label="Service Delivery Costs",
    category="expenses",
    formula="service_revenue * 0.45",  # 45% of service revenue
    value_format="no_decimals"
)

# Sales & Marketing - Percentage of total revenue
sales_marketing = LineItem(
    name="sales_marketing",
    label="Sales & Marketing",
    category="expenses",
    values={2024: 400_000},
    formula="sales_marketing[-1] * 1.12",  # 12% annual growth
    value_format="no_decimals"
)

# Research & Development - Fixed budget with inflation
research_development = LineItem(
    name="research_development",
    label="Research & Development",
    category="expenses",
    values={2024: 350_000},
    formula="research_development[-1] * 1.08",  # 8% annual growth
    value_format="no_decimals"
)

# General & Administrative - Semi-fixed costs
general_admin = LineItem(
    name="general_admin",
    label="General & Administrative",
    category="expenses",
    values={2024: 250_000},
    formula="general_admin[-1] * 1.06",  # 6% annual growth
    value_format="no_decimals"
)

# Rent & Facilities - Fixed with annual increases
rent_facilities = LineItem(
    name="rent_facilities",
    label="Rent & Facilities",
    category="expenses",
    values={2024: 120_000},
    formula="rent_facilities[-1] * 1.04",  # 4% annual growth
    value_format="no_decimals"
)

expense_items = [cost_of_goods_sold, service_costs, sales_marketing, 
                research_development, general_admin, rent_facilities]

print("✅ Expense line items created:")
for item in expense_items:
    print(f"   • {item.label}")
```

## 5. Create Calculated Line Items

Let's add some calculated line items for financial analysis.


```python
# Gross Profit - Revenue minus direct costs
gross_profit = LineItem(
    name="gross_profit",
    label="Gross Profit",
    category="calculated",
    formula="(product_sales + service_revenue + licensing_fees + subscription_revenue) - (cost_of_goods_sold + service_costs)",
    value_format="no_decimals"
)

# Operating Expenses - Total of operating expense categories
operating_expenses = LineItem(
    name="operating_expenses",
    label="Total Operating Expenses",
    category="calculated",
    formula="sales_marketing + research_development + general_admin + rent_facilities",
    value_format="no_decimals"
)

# EBITDA - Earnings before interest, taxes, depreciation, amortization
ebitda = LineItem(
    name="ebitda",
    label="EBITDA",
    category="calculated",
    formula="gross_profit - operating_expenses",
    value_format="no_decimals"
)

# Gross Margin - Gross profit as percentage of revenue
gross_margin = LineItem(
    name="gross_margin",
    label="Gross Margin %",
    category="ratios",
    formula="gross_profit / (product_sales + service_revenue + licensing_fees + subscription_revenue)",
    value_format="percent_one_decimal"
)

# EBITDA Margin - EBITDA as percentage of revenue
ebitda_margin = LineItem(
    name="ebitda_margin",
    label="EBITDA Margin %",
    category="ratios",
    formula="ebitda / (product_sales + service_revenue + licensing_fees + subscription_revenue)",
    value_format="percent_one_decimal"
)

calculated_items = [gross_profit, operating_expenses, ebitda, gross_margin, ebitda_margin]

print("✅ Calculated line items created:")
for item in calculated_items:
    print(f"   • {item.label}")
```

## 6. Define Categories

Let's organize our line items into logical categories for better reporting.


```python
# Define categories for organizing our financial model
categories = [
    Category(
        name="revenue",
        label="Revenue Streams",
        include_total=True  # Automatically calculate total revenue
    ),
    Category(
        name="expenses",
        label="Operating Expenses",
        include_total=True  # Automatically calculate total expenses
    ),
    Category(
        name="calculated",
        label="Calculated Metrics",
        include_total=False  # No total needed for calculated items
    ),
    Category(
        name="ratios",
        label="Financial Ratios",
        include_total=False  # No total needed for ratios
    )
]

print("✅ Categories defined:")
for category in categories:
    total_text = "(with totals)" if category.include_total else "(no totals)"
    print(f"   • {category.label} {total_text}")
```

## 7. Build the Financial Model

Now let's combine all our line items and categories into a comprehensive financial model.


```python
# Combine all line items
all_line_items = revenue_items + expense_items + calculated_items

# Create the financial model
financial_model = Model(
    line_items=all_line_items,
    categories=categories,
    years=MODEL_YEARS
)

print(f"✅ Financial model created successfully!")
print(f"📊 Total line items: {len(all_line_items)}")
print(f"📁 Categories: {len(categories)}")
print(f"📅 Years covered: {MODEL_YEARS}")

# Let's verify the model by checking a few key values
print("\n🔍 Sample calculations:")
print(f"Product Sales 2024: ${financial_model.get_value('product_sales', 2024):,.0f}")
print(f"Total Revenue 2024: ${financial_model.category('revenue').totals()[2024]:,.0f}")
print(f"EBITDA 2024: ${financial_model.get_value('ebitda', 2024):,.0f}")
```

## 8. Generate Summary Tables

Let's create professional financial statement tables using the built-in table methods.


```python
# Generate comprehensive income statement using the all() method
income_statement = financial_model.tables.all()

print("📋 Pro Forma Income Statement (Complete Model)")
print("="*60)

# Display the table as a pandas DataFrame for better formatting
df = income_statement.to_dataframe()
display(df)
```

## 9. Revenue Breakdown Analysis

Let's create a detailed view of our revenue components using category tables.


```python
# Create a focused revenue analysis table
revenue_table = financial_model.tables.category('revenue')
revenue_df = revenue_table.to_dataframe()

print("💰 Revenue Stream Analysis")
print("="*40)
display(revenue_df)

# Calculate year-over-year growth rates
print("\n📈 Year-over-Year Growth Rates:")
for year in [2025, 2026]:
    prev_year = year - 1
    total_revenue_growth = financial_model.percent_change('revenue', year)
    product_growth = financial_model.percent_change('product_sales', year)
    service_growth = financial_model.percent_change('service_revenue', year)
    
    print(f"{year}: Total Revenue +{total_revenue_growth:.1%}, Product Sales +{product_growth:.1%}, Service Revenue +{service_growth:.1%}")
```

## 10. Expense Analysis

Let's analyze our expense structure.


```python
# Create expense analysis table
expense_table = financial_model.tables.category('expenses')
expense_df = expense_table.to_dataframe()

print("💸 Expense Analysis")
print("="*30)
display(expense_df)
```

## 11. Create Interactive Charts

Now let's visualize our financial data with interactive charts.


```python
# Revenue Streams Chart - Line chart showing growth of different revenue streams
revenue_chart = financial_model.charts.items(
    ["product_sales", "service_revenue", "licensing_fees", "subscription_revenue"],
)

print("📊 Revenue Streams Growth Chart:")
revenue_chart.show()
```


```python
# Total Revenue vs Total Expenses - Bar chart comparison
revenue_vs_expenses_chart = financial_model.charts.items(
    ["revenue", "expenses"],  # These are category totals
)

print("⚖️ Revenue vs Expenses Chart:")
revenue_vs_expenses_chart.show()
```


```python
# Profitability Metrics - Line chart showing margins and EBITDA
profitability_chart = financial_model.charts.items(
    ["gross_margin", "ebitda_margin"],
)

print("📈 Profitability Margins Chart:")
profitability_chart.show()
```


```python
# EBITDA Growth Chart
ebitda_chart = financial_model.charts.item(
    "ebitda",
    chart_type="bar",
    title="EBITDA Growth Projection"
)

print("💼 EBITDA Growth Chart:")
ebitda_chart.show()
```

## 12. Advanced Analysis and Insights

Let's perform some advanced analysis on our financial model.


```python
# Key Financial Metrics Summary
print("🎯 KEY FINANCIAL METRICS SUMMARY")
print("="*50)

for year in MODEL_YEARS:
    total_revenue = financial_model.category('revenue').totals()[year]
    total_expenses = financial_model.category('expenses').totals()[year]
    ebitda_value = financial_model.get_value('ebitda', year)
    gross_margin_value = financial_model.get_value('gross_margin', year)
    ebitda_margin_value = financial_model.get_value('ebitda_margin', year)
    
    print(f"\n📅 {year}:")
    print(f"   Total Revenue:    ${total_revenue:,.0f}")
    print(f"   Total Expenses:   ${total_expenses:,.0f}")
    print(f"   EBITDA:          ${ebitda_value:,.0f}")
    print(f"   Gross Margin:     {gross_margin_value:.1%}")
    print(f"   EBITDA Margin:    {ebitda_margin_value:.1%}")

# Calculate compound annual growth rates (CAGR)
print("\n📊 COMPOUND ANNUAL GROWTH RATES (CAGR 2024-2026):")
print("-"*55)

def calculate_cagr(start_value, end_value, years):
    return (end_value / start_value) ** (1/years) - 1

revenue_2024 = financial_model.category('revenue').totals()[2024]
revenue_2026 = financial_model.category('revenue').totals()[2026]
ebitda_2024 = financial_model.get_value('ebitda', 2024)
ebitda_2026 = financial_model.get_value('ebitda', 2026)

revenue_cagr = calculate_cagr(revenue_2024, revenue_2026, 2)
ebitda_cagr = calculate_cagr(ebitda_2024, ebitda_2026, 2)

print(f"Revenue CAGR:       {revenue_cagr:.1%}")
print(f"EBITDA CAGR:        {ebitda_cagr:.1%}")
```

## 13. Revenue Mix Analysis

Let's analyze how our revenue mix changes over time.


```python
# Calculate revenue mix percentages
print("🥧 REVENUE MIX ANALYSIS")
print("="*40)

revenue_items_names = ["product_sales", "service_revenue", "licensing_fees", "subscription_revenue"]
revenue_items_labels = ["Product Sales", "Service Revenue", "Licensing Fees", "Subscription Revenue"]

for year in MODEL_YEARS:
    total_revenue = financial_model.category('revenue').totals()[year]
    print(f"\n📅 {year} Revenue Mix:")
    
    for name, label in zip(revenue_items_names, revenue_items_labels):
        value = financial_model.get_value(name, year)
        percentage = value / total_revenue
        print(f"   {label:20s}: ${value:8,.0f} ({percentage:5.1%})")
    
    print(f"   {'Total Revenue':20s}: ${total_revenue:8,.0f} (100.0%)")
```

## 14. Individual Line Item Analysis

Let's look at detailed analysis for specific line items.


```python
# Analyze a specific line item in detail
product_sales_table = financial_model.tables.line_item('product_sales')
product_sales_df = product_sales_table.to_dataframe()

print("🔍 Product Sales Detailed Analysis")
print("="*40)
display(product_sales_df)
```

## 15. Export Options

Finally, let's demonstrate how to export our model and tables for external use.


```python
# Export the income statement to Excel
try:
    income_statement.to_excel("financial_model_income_statement.xlsx")
    print("✅ Income statement exported to: financial_model_income_statement.xlsx")
except Exception as e:
    print(f"⚠️ Could not export to Excel: {e}")

# Export the model data as a pandas DataFrame
model_df = financial_model.to_dataframe()
print("\n📋 Complete Model Data (first 10 rows):")
display(model_df.head(10))

# Save model configuration as YAML for later use
try:
    financial_model.save_yaml("financial_model.yaml")
    print("\n✅ Model configuration saved to: financial_model.yaml")
except Exception as e:
    print(f"\n⚠️ Could not save YAML: {e}")

print("\n🎉 Financial model analysis complete!")
```

## Summary

This notebook demonstrated the key features of the `pyproforma` library:

### ✅ What We Built
- **Multi-stream Revenue Model**: 4 different revenue sources with varying growth rates
- **Comprehensive Expense Structure**: 6 expense categories with different calculation methods
- **Automated Calculations**: Formulas linking expenses to revenues and calculating derived metrics
- **Professional Tables**: Formatted financial statements with proper categorization
- **Interactive Visualizations**: Charts showing trends, comparisons, and profitability metrics

### 🔧 Key PyProforma Features Used
- `LineItem`: Individual financial line items with values and formulas
- `Category`: Organizing line items into logical groups with automatic totals
- `Model`: Comprehensive financial model with automatic dependency resolution
- `Tables`: Professional table generation using:
  - `tables.all()`: Complete model overview
  - `tables.category()`: Category-specific tables
  - `tables.line_item()`: Individual line item analysis
- `Charts`: Interactive Plotly-based visualizations
- **Export Options**: Excel, YAML, and DataFrame formats

### 🚀 Next Steps
You can extend this model by:
- Adding more sophisticated formulas and constraints
- Including cash flow and balance sheet items
- Adding scenario analysis and sensitivity testing
- Incorporating debt and financing models
- Building interactive dashboards with the visualization components

For more information, visit the [PyProforma documentation](https://github.com/rhannay/pyproforma).
