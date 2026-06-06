from pyproforma import (
    FixedLine,
    FormulaLine,
    Format,
    InputLine,
    ProformaModel,
    ScalarInputLine,
    ScalarLine,
    create_debt_lines,
)

PERIODS = list(range(2025, 2031))


def calc_dscr(li, t):
    if li.total_debt_service[t] > 0:
        return li.net_revenue[t] / li.total_debt_service[t]
    return 0.0


class WaterUtilityModel(ProformaModel):
    default_periods = list(range(2025, 2031))
    period_label = "Fiscal Year"
    """
    Six-year financial plan for a municipal water utility.

    Revenue bonds outstanding:
      - 2015 Series A: $25M par, 4.25%, 20-year (matures 2034)
      - 2027 Series B: $10M par, 4.50%, 20-year (issued in plan year)

    Scenario inputs (with defaults):
      - rate_increase:   annual water rate adjustment by year
      - mgd_growth_rate: annual water sales volume growth by year
      - new_bond_par:    par amount of new revenue bonds by year

    Scalar assumptions:
      - inflation_rate: general CPI (drives power sales and power/chemical O&M)
      - om_growth_rate: total O&M escalation rate

    FormulaLines that grow from a prior-period value are seeded via the
    `values` dict (e.g. `values={2025: 8.05}`). The formula lambda handles
    every period uniformly; the engine substitutes the seed value for 2025
    so the lambda never needs an `if t == 2025` guard.
    """

    # ── Scalar assumptions ────────────────────────────────────────────────────
    inflation_rate = ScalarInputLine(
        default=0.030,
        label="CPI Inflation Rate",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )
    om_growth_rate = ScalarLine(
        value=0.040,
        label="O&M Growth Rate",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )

    # ── Rate increases — scenario input with defaults ─────────────────────────
    # Increase applied to prior year's rate each period.
    # Pass rate_increase={...} at instantiation to override the default schedule.
    rate_increase = InputLine(
        default={2025: 0.050, 2026: 0.060, 2027: 0.050, 2028: 0.040, 2029: 0.040, 2030: 0.030},
        label="Rate Increase",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )

    # ── MGD volume growth — adjustable default schedule ───────────────────────
    # Annual growth in water sales volume; applied to prior-period MGD.
    # The 2025 value is unused (mgd seeds directly that year via values={2025: 8.05}).
    mgd_growth_rate = FixedLine(
        values={2025: 0.010, 2026: 0.010, 2027: 0.010, 2028: 0.010, 2029: 0.010, 2030: 0.010},
        label="MGD Growth Rate",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )

    # ── New bond par amounts — adjustable default schedule ────────────────────
    # 2027 Series B Revenue Bonds: $10M par; 0 in all other years.
    new_bond_par = FixedLine(
        values={2025: 0, 2026: 0, 2027: 10_000_000, 2028: 0, 2029: 0, 2030: 0},
        label="New Bond Proceeds",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Existing debt service (2015 Series A Revenue Bonds) ───────────────────
    # $25M par, 4.25%, 20-year; $17M outstanding at BOY 2025; annual DS ~$1.88M.
    existing_principal = FixedLine(
        values={
            2025: 1_158_000,
            2026: 1_207_000,
            2027: 1_259_000,
            2028: 1_313_000,
            2029: 1_369_000,
            2030: 1_427_000,
        },
        label="2015 Series A — Principal",
        tags=["existing_ds"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    existing_interest = FixedLine(
        values={
            2025: 723_000,
            2026: 674_000,
            2027: 622_000,
            2028: 568_000,
            2029: 512_000,
            2030: 454_000,
        },
        label="2015 Series A — Interest",
        tags=["existing_ds"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── New bond parameters ────────────────────────────────────────────────────
    new_bond_rate = ScalarInputLine(
        default=0.045,
        label="Series B Interest Rate",
        value_format=Format.PERCENT_TWO_DECIMALS,
    )
    new_bond_term = ScalarLine(
        value=20,
        label="Series B Term (Years)",
    )

    # ── New bond debt service (2027 Series B Revenue Bonds) ───────────────────
    # Annual DS ~$769K beginning 2027.
    new_bond_principal, new_bond_interest = create_debt_lines(
        par_amounts="new_bond_par",
        interest_rate="new_bond_rate",
        term="new_bond_term",
        principal_label="2027 Series B — Principal",
        interest_label="2027 Series B — Interest",
        tags=["new_ds"],
        principal_value_format=Format.CURRENCY_NO_DECIMALS,
        interest_value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Water rate (cumulative compounding from 2024 base) ────────────────────
    # Seed: $4,500/MG (2024 actual) × 1.05 = $4,725 for 2025.
    water_rate = FormulaLine(
        formula=lambda li, t: li.water_rate[t - 1] * (1 + li.rate_increase[t]),
        values={2025: 4_725},
        label="Water Rate ($/MG)",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Water sales volume ────────────────────────────────────────────────────
    # Seed: 8.05 MGD (2025 actual).
    mgd = FormulaLine(
        formula=lambda li, t: li.mgd[t - 1] * (1 + li.mgd_growth_rate[t]),
        values={2025: 8.05},
        label="Water Sales (MGD)",
        value_format=Format.TWO_DECIMALS,
    )

    # ── Revenue ───────────────────────────────────────────────────────────────
    # Seed: 8.05 MGD × 365 × $4,725/MG = $13,883,231 (2025 actual).
    # Subsequent years compound both volume (mgd_growth_rate) and price (rate_increase).
    water_sales_revenue = FormulaLine(
        formula=lambda li, t: li.water_sales_revenue[t - 1] * (1 + li.mgd_growth_rate[t]) * (1 + li.rate_increase[t]),
        values={2025: 13_883_231},
        label="Water Sales Revenue",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    # Seed: $480,000 base × 1.03 = $494,400 (2025 actual); grows at CPI thereafter.
    power_sales = FormulaLine(
        formula=lambda li, t: li.power_sales[t - 1] * (1 + li.inflation_rate),
        values={2025: 494_400},
        label="Power Sales",
        tags=["revenue"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_revenue = FormulaLine(
        formula=lambda li, t: li.tag["revenue"][t],
        label="Total Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── O&M Expenses ──────────────────────────────────────────────────────────
    # Each category is seeded at its 2025 actual value and compounded from there.
    # Power & Chemicals tracks CPI; all others track om_growth_rate.
    labor_and_benefits = FormulaLine(
        formula=lambda li, t: li.labor_and_benefits[t - 1] * (1 + li.om_growth_rate),
        values={2025: 4_056_000},   # 3,900,000 × 1.04
        label="Labor & Benefits",
        tags=["om"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    power_and_chemicals = FormulaLine(
        formula=lambda li, t: li.power_and_chemicals[t - 1] * (1 + li.inflation_rate),
        values={2025: 1_751_000},   # 1,700,000 × 1.03
        label="Power & Chemicals",
        tags=["om"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    maintenance_and_repairs = FormulaLine(
        formula=lambda li, t: li.maintenance_and_repairs[t - 1] * (1 + li.om_growth_rate),
        values={2025: 1_144_000},   # 1,100,000 × 1.04
        label="Maintenance & Repairs",
        tags=["om"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    general_and_admin = FormulaLine(
        formula=lambda li, t: li.general_and_admin[t - 1] * (1 + li.om_growth_rate),
        values={2025: 884_000},     # 850,000 × 1.04
        label="General & Administrative",
        tags=["om"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_om = FormulaLine(
        formula=lambda li, t: li.tag["om"][t],
        label="Total O&M",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Net Revenue (above-the-line) ─────────────────────────────────────────
    net_revenue = FormulaLine(
        formula=lambda li, t: li.total_revenue[t] - li.total_om[t],
        label="Net Revenue",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Debt Service ──────────────────────────────────────────────────────────
    total_existing_ds = FormulaLine(
        formula=lambda li, t: li.existing_principal[t] + li.existing_interest[t],
        label="2015 Series A Total DS",
        tags=["debt_service"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_new_ds = FormulaLine(
        formula=lambda li, t: li.new_bond_principal[t] + li.new_bond_interest[t],
        label="2027 Series B Total DS",
        tags=["debt_service"],
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_debt_service = FormulaLine(
        formula=lambda li, t: li.tag["debt_service"][t],
        label="Total Debt Service",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Below-the-line Capital ────────────────────────────────────────────────
    # Six-year capital improvement program totaling $37M.
    # The 2027 transmission main project ($12M) is the primary driver of the bond.
    capital_spending = FixedLine(
        values={
            2025: 3_500_000,
            2026: 4_500_000,
            2027: 12_000_000,
            2028: 5_000_000,
            2029: 5_000_000,
            2030: 7_000_000,
        },
        label="Capital Expenditures",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    # Capacity fees collected from new development connections.
    capacity_fees = FixedLine(
        values={
            2025: 350_000,
            2026: 450_000,
            2027: 250_000,
            2028: 500_000,
            2029: 550_000,
            2030: 600_000,
        },
        label="Capacity Fees",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Cash Balance ──────────────────────────────────────────────────────────
    # Seed: $5,000,000 beginning cash balance at BOY 2025.
    starting_cash = FormulaLine(
        formula=lambda li, t: li.ending_cash[t - 1],
        values={2025: 5_000_000},
        label="Beginning Cash Balance",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    ending_cash = FormulaLine(
        formula=lambda li, t: (
            li.starting_cash[t]
            + li.net_revenue[t]
            - li.total_debt_service[t]
            + li.new_bond_par[t]
            - li.capital_spending[t]
            + li.capacity_fees[t]
        ),
        label="Ending Cash Balance",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Principal Outstanding ─────────────────────────────────────────────────
    # End-of-year balances after that year's principal payment.
    # Seed: $17,000,000 opening balance less 2025 principal = $15,842,000.
    existing_outstanding = FormulaLine(
        formula=lambda li, t: li.existing_outstanding[t - 1] - li.existing_principal[t],
        values={2025: 15_842_000},
        label="2015 Series A Outstanding",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    # Tracks end-of-year balance: prior balance + new issuance - principal paid.
    # Seed: $0 (no new bonds outstanding before 2027).
    new_bond_outstanding = FormulaLine(
        formula=lambda li, t: li.new_bond_outstanding[t - 1] + li.new_bond_par[t] - li.new_bond_principal[t],
        values={2025: 0},
        label="2027 Series B Outstanding",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )
    total_outstanding = FormulaLine(
        formula=lambda li, t: li.existing_outstanding[t] + li.new_bond_outstanding[t],
        label="Total Principal Outstanding",
        value_format=Format.CURRENCY_NO_DECIMALS,
    )

    # ── Key Metrics ───────────────────────────────────────────────────────────
    dscr = FormulaLine(
        formula=calc_dscr,
        label="Debt Service Coverage Ratio",
        value_format=Format.TWO_DECIMALS,
    )
    days_cash_on_hand = FormulaLine(
        formula=lambda li, t: li.ending_cash[t] / (li.total_om[t] / 365),
        label="Days Cash on Hand",
        value_format=Format.NO_DECIMALS,
    )
    # Fraction of each year's capex covered by new-bond principal repayment.
    debt_funded_capital = FormulaLine(
        formula=lambda li, t: (
            li.new_bond_principal[t] / li.capital_spending[t]
            if li.capital_spending[t] > 0 else 0.0
        ),
        label="Debt-Funded Capital Ratio",
        value_format=Format.PERCENT_ONE_DECIMAL,
    )


model = WaterUtilityModel()
