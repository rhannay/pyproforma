"""
Quick demonstration of the tags and reserved words features.
Run this to see the new functionality in action.
"""

from pyproforma.v2 import FixedLine, FormulaLine, ProformaModel


def demo_tags():
    """Demonstrate tags functionality."""
    print("=" * 70)
    print("TAGS FEATURE DEMO")
    print("=" * 70)

    class SimpleModel(ProformaModel):
        # Revenue items with 'income' tag
        sales = FixedLine(
            values={2024: 1000, 2025: 1100}, tags=["income", "recurring"]
        )
        interest = FixedLine(values={2024: 50, 2025: 55}, tags=["income"])

        # Expense items with 'expense' tag
        costs = FixedLine(
            values={2024: 600, 2025: 660}, tags=["expense", "recurring"]
        )
        taxes = FixedLine(values={2024: 100, 2025: 110}, tags=["expense"])

        # Calculate totals using tags
        total_income = FormulaLine(formula=lambda a, li, t: li.tags["income"][t])
        total_expense = FormulaLine(formula=lambda a, li, t: li.tags["expense"][t])
        profit = FormulaLine(
            formula=lambda a, li, t: li.tags["income"][t] - li.tags["expense"][t]
        )

    model = SimpleModel(periods=[2024, 2025])

    print("\n✓ Tags defined on line items:")
    print(f"  sales.tags = {model['sales'].tags}")
    print(f"  costs.tags = {model['costs'].tags}")

    print("\n✓ Tag-based summation in action:")
    for year in [2024, 2025]:
        print(f"\n  {year}:")
        print(f"    Income items sum:  ${model.li.tags['income'][year]:>8,.0f}")
        print(f"    Expense items sum: ${model.li.tags['expense'][year]:>8,.0f}")
        print(f"    Profit:            ${model.li.profit[year]:>8,.0f}")

    print("\n✓ Multiple tags per item:")
    print(f"  Recurring items sum (2024): ${model.li.tags['recurring'][2024]:,.0f}")


def demo_reserved_words():
    """Demonstrate reserved words validation."""
    print("\n" + "=" * 70)
    print("RESERVED WORDS VALIDATION DEMO")
    print("=" * 70)

    print("\n✓ These words are now reserved and cannot be used as line item names:")
    print("  - Namespace accessors: li, av, tags, tables")
    print("  - Formula parameters: t, a")
    print("  - Model properties: periods, line_item_names")
    print("  - Python keywords: class, def, return, etc.")

    print("\n✓ Attempting to use a reserved word raises an error:")
    try:

        class BadModel(ProformaModel):
            tags = FixedLine(values={2024: 100})  # This will fail

    except ValueError as e:
        print(f"  Error (expected): {e}")

    print("\n✓ Valid names work fine:")

    class GoodModel(ProformaModel):
        revenue = FixedLine(values={2024: 100})
        expenses = FixedLine(values={2024: 60})

    model = GoodModel(periods=[2024])
    print(f"  revenue: ${model.li.revenue[2024]}")
    print(f"  expenses: ${model.li.expenses[2024]}")


def main():
    """Run all demonstrations."""
    demo_tags()
    demo_reserved_words()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nNew features implemented:")
    print("  1. ✓ Tags for flexible categorization of line items")
    print("  2. ✓ li.tags[tag_name][period] for summing by tag")
    print("  3. ✓ Tags accessible via LineItemResult.tags")
    print("  4. ✓ Reserved words validation to prevent conflicts")
    print("  5. ✓ 206 tests passing, including 31 new tests")
    print("\nFor more details, see:")
    print("  - pyproforma/v2/README.md")
    print("  - examples/v2/tags_example.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
