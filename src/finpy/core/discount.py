"""Discounting + a grab-bag of yield-curve helpers.

The original file had two functions; tests expect a wider surface (yields,
duration, convexity, forward rates, factors). They live together here because
they all hinge on the same compounding-mode plumbing.
"""

from decimal import Decimal, ROUND_HALF_UP


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def discount_factor(rate, t, mode="annual", *, ndigits=None) -> Decimal:
    r = Decimal(str(rate))
    one = Decimal(1)
    n = Decimal(str(t))
    if mode == "annual":
        if r <= -one:
            raise ValueError("annual rate must exceed -1")
        result = (one + r) ** (-n)
    elif mode == "semi-annual":
        if r <= -2:
            raise ValueError("semi-annual rate must exceed -2")
        result = (one + r / 2) ** (-2 * n)
    elif mode == "continuous":
        from math import exp
        result = Decimal(str(exp(-float(r) * float(n))))
    else:
        raise ValueError(f"unknown mode: {mode}")
    return _quantize(result, ndigits)


def present_value_of_flow(amount, t, rate, mode="annual", *, ndigits=None) -> Decimal:
    return _quantize(Decimal(str(amount)) * discount_factor(rate, t, mode), ndigits)


def present_value(amount, t, rate=None, mode="annual", *, ndigits=None) -> Decimal:
    """Discount cash-flow pairs, or a single amount with an explicit rate.

    ``present_value(flows, rate)`` aggregates (amount, time) pairs. The
    existing ``present_value(amount, time, rate)`` form remains supported.
    """
    if rate is not None:
        return present_value_of_flow(amount, t, rate, mode, ndigits=ndigits)
    total = sum(
        (present_value_of_flow(value, when, t, mode) for value, when in amount),
        Decimal(0),
    )
    return _quantize(total, ndigits)


def future_value_of_flow(amount, t, rate, mode="annual", *, ndigits=None) -> Decimal:
    """Compound `amount` forward by t periods at `rate`."""
    r = Decimal(str(rate))
    one = Decimal(1)
    n = Decimal(str(t))
    if mode == "annual":
        factor = (one + r) ** n
    elif mode == "semi-annual":
        factor = (one + r / 2) ** (2 * n)
    elif mode == "continuous":
        from math import exp
        factor = Decimal(str(exp(float(r) * float(n))))
    else:
        raise ValueError(f"unknown mode: {mode}")
    return _quantize(Decimal(str(amount)) * factor, ndigits)


def discount_yield(price, face, days, *, ndigits=None) -> Decimal:
    """T-bill discount yield: ((F-P)/F) * (360/days)."""
    p = Decimal(str(price))
    f = Decimal(str(face))
    if days <= 0:
        raise ValueError("days must be positive")
    if p <= 0:
        raise ValueError("price must be positive")
    return _quantize((f - p) / f * Decimal(360) / Decimal(days), ndigits)


def money_market_yield(discount_yield_value, days, *, ndigits=None) -> Decimal:
    """Convert a discount yield to a 360-day money-market yield."""
    if days <= 0:
        raise ValueError("days must be positive")
    dy = Decimal(str(discount_yield_value))
    bd = Decimal(str(days))
    return _quantize(dy * (Decimal(360) / (Decimal(360) - dy * bd)), ndigits)


def bond_equivalent_yield(price, face, days, *, ndigits=None) -> Decimal:
    """Treasury BEY: ((F-P)/P) * (365/days)."""
    p = Decimal(str(price))
    f = Decimal(str(face))
    if days <= 0:
        raise ValueError("days must be positive")
    if p <= 0:
        raise ValueError("price must be positive")
    return _quantize((f - p) / p * Decimal(365) / Decimal(days), ndigits)


def yield_to_maturity(price, face, coupon, periods, *, ndigits=None, tol=Decimal("1e-8"), max_iter=200) -> Decimal:
    """Solve for YTM given price, face, periodic coupon, and periods."""
    p = Decimal(str(price))
    f = Decimal(str(face))
    c = Decimal(str(coupon))
    n = int(periods)
    if p <= 0:
        raise ValueError("price must be positive")
    if n <= 0:
        raise ValueError("periods must be positive")

    def npv_at(r):
        one = Decimal(1)
        if (one + r) <= 0:
            raise ValueError("rate too negative")
        total = Decimal(0)
        for i in range(1, n + 1):
            total += c / (one + r) ** Decimal(i)
        total += f / (one + r) ** Decimal(n)
        return total - p

    lo, hi = Decimal("-0.5"), Decimal("2.0")
    f_lo, f_hi = npv_at(lo), npv_at(hi)
    if f_lo * f_hi > 0:
        return _quantize((lo + hi) / 2, ndigits)
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = npv_at(mid)
        if abs(f_mid) < tol:
            return _quantize(mid, ndigits)
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return _quantize((lo + hi) / 2, ndigits)


def current_yield(coupon, price, *, ndigits=None) -> Decimal:
    p = Decimal(str(price))
    if p <= 0:
        raise ValueError("price must be positive")
    return _quantize(Decimal(str(coupon)) / p, ndigits)


def macaulay_duration(flows, ytm, *, ndigits=None) -> Decimal:
    """Macaulay duration over a list of (cashflow, t) tuples."""
    if not flows:
        raise ValueError("flows is empty")
    r = Decimal(str(ytm))
    one = Decimal(1)
    total_pv = Decimal(0)
    weighted = Decimal(0)
    for cf, t in flows:
        cf_d = Decimal(str(cf))
        t_d = Decimal(str(t))
        pv = cf_d / (one + r) ** t_d
        total_pv += pv
        weighted += t_d * pv
    if total_pv == 0:
        raise ValueError("total PV is zero")
    return _quantize(weighted / total_pv, ndigits)


def modified_duration(flows, ytm, *, ndigits=None) -> Decimal:
    mac = macaulay_duration(flows, ytm)
    one = Decimal(1)
    r = Decimal(str(ytm))
    return _quantize(mac / (one + r), ndigits)


def convexity(flows, ytm, *, ndigits=None) -> Decimal:
    if not flows:
        raise ValueError("flows is empty")
    r = Decimal(str(ytm))
    one = Decimal(1)
    total_pv = Decimal(0)
    weighted = Decimal(0)
    for cf, t in flows:
        cf_d = Decimal(str(cf))
        t_d = Decimal(str(t))
        pv = cf_d / (one + r) ** t_d
        total_pv += pv
        weighted += t_d * (t_d + one) * pv
    if total_pv == 0:
        raise ValueError("total PV is zero")
    return _quantize(weighted / total_pv / (one + r) ** 2, ndigits)


def zero_coupon_rate(price, t, *, mode="annual", face=Decimal(1), ndigits=None) -> Decimal:
    """Implied spot rate from a zero-coupon bond price."""
    p = Decimal(str(price))
    t_d = Decimal(str(t))
    if p <= 0:
        raise ValueError("price must be positive")
    if t_d <= 0:
        raise ValueError("t must be positive")
    one = Decimal(1)
    if mode == "annual":
        r = Decimal(str(float(face / p) ** (1.0 / float(t_d)))) - one
    elif mode == "continuous":
        from math import log
        r = -Decimal(str(log(float(p / face)))) / t_d
    else:
        raise ValueError(f"unknown mode: {mode}")
    return _quantize(r, ndigits)


def forward_rate(rate_a, rate_b, t_a, t_b, *, ndigits=None) -> Decimal:
    """Forward rate from t_a to t_b implied by spot rates rate_a, rate_b."""
    if t_b <= t_a:
        raise ValueError("t_b must exceed t_a")
    r_a = Decimal(str(rate_a))
    r_b = Decimal(str(rate_b))
    one = Decimal(1)
    base = (one + r_b) ** Decimal(str(t_b)) / (one + r_a) ** Decimal(str(t_a))
    pow_exp = 1.0 / float(t_b - t_a)
    fwd = Decimal(str(float(base) ** pow_exp)) - one
    return _quantize(fwd, ndigits)


def annuity_factor(rate, nper, *, mode="ordinary", ndigits=None) -> Decimal:
    """Present-value annuity factor: (1 - (1+r)^-n) / r."""
    r = Decimal(str(rate))
    n = Decimal(str(nper))
    one = Decimal(1)
    if r == 0:
        return _quantize(n, ndigits)
    if mode == "ordinary":
        af = (one - (one + r) ** (-n)) / r
    elif mode == "due":
        af = (one - (one + r) ** (-n)) / r * (one + r)
    else:
        raise ValueError(f"unknown mode: {mode}")
    return _quantize(af, ndigits)


def sinking_factor(rate, nper, *, ndigits=None) -> Decimal:
    """Sinking-fund factor: r / ((1+r)^n - 1)."""
    r = Decimal(str(rate))
    n = Decimal(str(nper))
    one = Decimal(1)
    if r == 0:
        return _quantize(one / n, ndigits)
    return _quantize(r / ((one + r) ** n - one), ndigits)


def capital_recovery_factor(rate, nper, *, ndigits=None) -> Decimal:
    """Capital-recovery factor: r * (1+r)^n / ((1+r)^n - 1)."""
    r = Decimal(str(rate))
    n = Decimal(str(nper))
    one = Decimal(1)
    if r == 0:
        return _quantize(one / n, ndigits)
    return _quantize(r * (one + r) ** n / ((one + r) ** n - one), ndigits)
