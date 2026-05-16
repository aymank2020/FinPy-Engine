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
    old_pmt = monthly_payment(principal, old_rate, float(years), payments_per_year=payments_per_year)
    new_pmt = monthly_payment(principal, new_rate, float(years), payments_per_year=payments_per_year)
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
    """IRR of the refinance cashflow stream: -closing_costs at t=0, +saving each period."""
    saving = _monthly_savings(principal, old_rate, new_rate, n_periods, payments_per_year)
    cc = Decimal(str(closing_costs))
    one = Decimal(1)

    def npv_at(r):
        if r == 0:
            return saving * Decimal(n_periods) - cc
        return saving * (one - (one + r) ** (-Decimal(n_periods))) / r - cc

    if saving <= 0:
        return _quantize(Decimal(0), ndigits)

    lo, hi = Decimal("-0.99") / Decimal(payments_per_year), Decimal("5") / Decimal(payments_per_year)
    f_lo, f_hi = npv_at(lo), npv_at(hi)
    if f_lo * f_hi > 0:
        return _quantize(Decimal(0), ndigits)
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = npv_at(mid)
        if abs(f_mid) < tol:
            return _quantize(mid * Decimal(payments_per_year), ndigits)
        if f_lo * f_mid < 0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid
    return _quantize((lo + hi) / 2 * Decimal(payments_per_year), ndigits)


def rate_comparison(old_rate, new_rate, closing_costs, monthly_savings) -> dict:
    """Quick comparison summary across the two rates and savings stream."""
    old_r = Decimal(str(old_rate))
    new_r = Decimal(str(new_rate))
    cc = Decimal(str(closing_costs))
    s = Decimal(str(monthly_savings))
    breakeven = cc / s if s > 0 else Decimal(0)
    return {
        "rate_drop": old_r - new_r,
        "monthly_savings": s,
        "closing_costs": cc,
        "breakeven_months": breakeven,
    }
