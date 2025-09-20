"""Test script to verify the name setter functionality for CategoryResults."""

from pyproforma import Model

# Create a simple model
model = Model(years=[2024, 2025])

# Add a category
model.update.add_category(name="revenue", label="Revenue Items")

# Add a line item in that category
model.update.add_line_item(
    name="sales", category="revenue", values={2024: 100000, 2025: 110000}
)

# Get the category results
category_results = model.category("revenue")

print(f"Original category name: {category_results.name}")
print(f"Line items in category: {category_results.line_item_names}")

# Test the setter
category_results.name = "sales_revenue"

print(f"New category name: {category_results.name}")
print(f"Line items still in category: {category_results.line_item_names}")

# Verify the line item category was updated in the model
sales_item = model.line_item_definition("sales")
print(f"Sales item category is now: {sales_item.category}")

# Verify we can create a new CategoryResults with the new name
new_category_results = model.category("sales_revenue")
print(f"New CategoryResults name: {new_category_results.name}")
print(f"New CategoryResults line items: {new_category_results.line_item_names}")

print("✅ Name setter test completed successfully!")
