import math

from pyproforma.models.generator import Debt


def _get_p_i(i, p, t, sy, y):
    ds_schedule = Debt.generate_debt_service_schedule(
        interest_rate=i,
        par_amount=p,
        term=t,
        start_year=sy,
    )
    for row in ds_schedule:
        if row["year"] == y:
            return row["principal"], row["interest"]


def _is_close(a, b, rel_tol=1e-9, abs_tol=0.0):
    """Compare two float values for approximate equality."""
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
