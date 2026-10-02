"""Refinance analysis primitives.

Tests use:
    refinance_breakeven(principal, old_rate, new_rate, closing_costs, n_periods, *, ndigits) -> Decimal months
    refinance_total_savings(...) -> Decimal
    refinance_npv(..., discount_rate=...) -> Decimal
    refinance_irr(...) -> Decimal
    rate_comparison(old_rate, new_rate, closing_costs, monthly_savings) -> dict-like
"""

from decimal import Decimal, ROUND_HALF_UP

from finpy.loans.schedule import monthly_payment


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year=12) -> Decimal:
    years = Decimal(n_periods) / Decimal(payments_per_year)
    old_pmt = monthly_payment(principal, old_rate, years, payments_per_year=payments_per_year)
    new_pmt = monthly_payment(principal, new_rate, years, payments_per_year=payments_per_year)
    return old_pmt - new_pmt


def refinance_breakeven(principal, old_rate, new_rate, closing_costs, n_periods, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Months until cumulative savings exceed closing costs."""
    saving = _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year)
    cc = Decimal(str(closing_costs))
    if saving <= 0:
        return _quantize(Decimal(0), ndigits)
    if cc == 0:
        return _quantize(Decimal(0), ndigits)
    months = cc / saving
    return _quantize(months, ndigits)


def refinance_total_savings(principal, old_rate, new_rate, closing_costs, n_periods, *, payments_per_year=12, ndigits=None) -> Decimal:
    """Total dollar savings over the remaining term, net of closing costs."""
    saving = _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year)
    if saving <= 0:
        return _quantize(Decimal(0), ndigits)
    total = saving * Decimal(n_periods) - Decimal(str(closing_costs))
    if total < 0:
        return _quantize(Decimal(0), ndigits)
    return _quantize(total, ndigits)


def refinance_npv(principal, old_rate, new_rate, closing_costs, n_periods, *, discount_rate=None, payments_per_year=12, ndigits=None) -> Decimal:
    """NPV of the refinance: PV(monthly savings) - closing_costs."""
    saving = _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year)
    cc = Decimal(str(closing_costs))
    if discount_rate is None:
        discount_rate = float(new_rate)
    r = Decimal(str(discount_rate)) / Decimal(str(payments_per_year))
    one = Decimal(1)
    if r == 0:
        pv_savings = saving * Decimal(n_periods)
    else:
        pv_savings = saving * (one - (one + r) ** (-Decimal(n_periods))) / r
    return _quantize(pv_savings - cc, ndigits)


def refinance_irr(principal, old_rate, new_rate, closing_costs, n_periods, *, payments_per_year=12, ndigits=None, max_iter=200, tol=Decimal("1e-8")) -> Decimal:
    """Nominal annual IRR of upfront costs and constant end-period savings.

    Returns zero for non-positive savings (legacy sentinel). Positive savings
    require positive closing costs, since no finite IRR exists with zero cost.
    """
    saving = _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year)
    cc = Decimal(str(closing_costs))
    if saving <= 0:
        return _quantize(Decimal(0), ndigits)
    if cc <= 0 or n_periods <= 0 or max_iter <= 0 or tol <= 0:
        raise ValueError("costs, periods, iterations and tolerance must be positive")
    one = Decimal(1)
    frequency = Decimal(str(payments_per_year))

    def npv_at(rate):
        if rate == 0:
            return saving * Decimal(n_periods) - cc
        return saving * (one - (one + rate) ** (-Decimal(n_periods))) / rate - cc

    at_zero = npv_at(Decimal(0))
    if at_zero == 0:
        return _quantize(Decimal(0), ndigits)
    if at_zero > 0:
        lo, hi = Decimal(0), one
        for _ in range(max_iter):
            if npv_at(hi) < 0:
                break
            hi *= 2
        else:
            raise ValueError("could not bracket refinance IRR")
    else:
        lo, hi = Decimal("-0.5"), Decimal(0)
        for _ in range(max_iter):
            if npv_at(lo) > 0:
                break
            lo = (lo - one) / 2
            if lo == -one:
                raise ValueError("could not bracket refinance IRR")
        else:
            raise ValueError("could not bracket refinance IRR")
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        value = npv_at(mid)
        if abs(value) < tol:
            return _quantize(mid * frequency, ndigits)
        if value > 0:
            lo = mid
        else:
            hi = mid
    raise ValueError("refinance IRR did not converge")


def rate_comparison(old_rate, new_rate, closing_costs, monthly_savings, *, ndigits=None) -> dict:
    """Undiscounted savings net of costs; retains original summary fields."""
    old_r, new_r = Decimal(str(old_rate)), Decimal(str(new_rate))
    costs, saving = Decimal(str(closing_costs)), Decimal(str(monthly_savings))
    out = {
        "rate_drop": old_r - new_r,
        "monthly_savings": saving,
        "closing_costs": costs,
        "breakeven_months": costs / saving if saving > 0 else Decimal(0),
        "one_year_savings": saving * 12 - costs,
        "five_year_savings": saving * 60 - costs,
    }
    return {key: _quantize(value, ndigits) for key, value in out.items()}
