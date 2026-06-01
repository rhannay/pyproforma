from pyproforma import (
    FixedLine,
    FormulaLine,
    Format,
    ProformaModel,
)


class CoffeeShopModel(ProformaModel):
    # --- Revenue ---
    coffee_sales = FixedLine(
        values={2024: 280_000, 2025: 308_000, 2026: 339_000},
        label="Coffee Sales",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    food_sales = FixedLine(
        values={2024: 95_000, 2025: 105_000, 2026: 116_000},
        label="Food Sales",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    merchandise_sales = FixedLine(
        values={2024: 25_000, 2025: 27_000, 2026: 30_000},
        label="Merchandise",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # --- COGS assumptions ---
    coffee_cogs_rate = FixedLine(value=0.35, label="Coffee COGS Rate", value_format=Format.PERCENT_ONE_DECIMAL, tags=["assumption"])
    food_cogs_rate = FixedLine(value=0.45, label="Food COGS Rate", value_format=Format.PERCENT_ONE_DECIMAL, tags=["assumption"])

    # --- Cost of Goods Sold ---
    coffee_cogs = FormulaLine(
        formula=lambda li, t: li.coffee_sales[t] * li.coffee_cogs_rate,
        label="Coffee COGS",
        tags=["cogs"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    food_cogs = FormulaLine(
        formula=lambda li, t: li.food_sales[t] * li.food_cogs_rate,
        label="Food COGS",
        tags=["cogs"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # --- Revenue & gross profit subtotals ---
    total_revenue = FormulaLine(
        formula=lambda li, t: li.tag["revenue"][t],
        label="Total Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_cogs = FormulaLine(
        formula=lambda li, t: li.tag["cogs"][t],
        label="Total COGS",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    gross_profit = FormulaLine(
        formula=lambda li, t: li.total_revenue[t] - li.total_cogs[t],
        label="Gross Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    gross_margin = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] / li.total_revenue[t],
        label="Gross Margin",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )

    # --- Operating Expenses ---
    rent = FixedLine(
        values={2024: 48_000, 2025: 49_440, 2026: 50_923},
        label="Rent",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    labor = FixedLine(
        values={2024: 110_000, 2025: 118_000, 2026: 127_000},
        label="Labor",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    utilities = FixedLine(
        values={2024: 12_000, 2025: 12_600, 2026: 13_230},
        label="Utilities",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    marketing = FixedLine(
        values={2024: 15_000, 2025: 17_000, 2026: 19_000},
        label="Marketing",
        tags=["opex"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # --- Operating profit ---
    total_opex = FormulaLine(
        formula=lambda li, t: li.tag["opex"][t],
        label="Total Operating Expenses",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    operating_profit = FormulaLine(
        formula=lambda li, t: li.gross_profit[t] - li.total_opex[t],
        label="Operating Profit",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    operating_margin = FormulaLine(
        formula=lambda li, t: li.operating_profit[t] / li.total_revenue[t],
        label="Operating Margin",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )


model = CoffeeShopModel(periods=[2024, 2025, 2026])
