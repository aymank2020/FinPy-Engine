"""Present-value primitives.

Implements textbook variants of present value: standard (end / begin) annuity,
perpetuities (level, due, growing, with delay), deferred and continuous-
compounding variants, and a generic uneven-cashflow PV. The mix exists because
real callers ask for these by name; centralising them here keeps callers thin.
"""

from decimal import Decimal, ROUND_HALF_UP
from math import exp


def _quantize(value: Decimal, ndigits) -> Decimal:
    if ndigits is None:
        return value
    return value.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def present_value(rate, nper, pmt, fv=0.0, when="end", *, ndigits=None) -> Decimal:
    r = Decimal(str(rate))
    n = Decimal(str(nper))
    p = Decimal(str(pmt))
    fv_dec = Decimal(str(fv))
    one = Decimal(1)
    if r == 0:
        pv = p * n + fv_dec
    else:
        factor = (one + r) ** n
        if when == "begin":
            pv = p * (one + r) * (one - (one + r) ** (-n)) / r + fv_dec / factor
        else:
            pv = p * (one - (one + r) ** (-n)) / r + fv_dec / factor
    return _quantize(pv, ndigits)


def annuity_due(rate, nper, pmt, *, ndigits=None) -> Decimal:
    """Annuity due â€” payments at the START of each period."""
    r = Decimal(str(rate))
    n = Decimal(str(nper))
    p = Decimal(str(pmt))
    one = Decimal(1)
    if p == 0:
        return _quantize(Decimal(0), ndigits)
    if r == 0:
        pv = p * n
    else:
        pv = p * (one + r) * (one - (one + r) ** (-n)) / r
    return _quantize(pv, ndigits)


def perpetuity(rate, pmt, *, ndigits=None) -> Decimal:
    """Level perpetuity â€” pmt / rate."""
    r = Decimal(str(rate))
    p = Decimal(str(pmt))
    if r == 0:
        raise ValueError("perpetuity is undefined for rate=0")
    return _quantize(p / r, ndigits)


def perpetuity_due(rate, pmt, *, ndigits=None) -> Decimal:
    """Perpetuity due â€” first payment at t=0; equals pmt + pmt/rate."""
    r = Decimal(str(rate))
    p = Decimal(str(pmt))
    if r == 0:
        raise ValueError("perpetuity_due is undefined for rate=0")
    return _quantize(p + p / r, ndigits)


def growing_perpetuity(rate, growth, pmt, *, ndigits=None) -> Decimal:
    """Growing perpetuity (Gordon model) â€” pmt / (rate - growth)."""
    r = Decimal(str(rate))
    g = Decimal(str(growth))
    p = Decimal(str(pmt))
    if r <= g:
        raise ValueError("rate must exceed growth for growing_perpetuity to converge")
    return _quantize(p / (r - g), ndigits)


def growing_annuity(rate, growth, nper, pmt, when="end", *, ndigits=None) -> Decimal:
    """Growing annuity â€” finite-horizon analogue of growing perpetuity."""
    r = Decimal(str(rate))
    g = Decimal(str(growth))
    n = Decimal(str(nper))
    p = Decimal(str(pmt))
    one = Decimal(1)
    if r == g:
        pv = p * n / (one + r)
    else:
        pv = p / (r - g) * (one - ((one + g) / (one + r)) ** n)
    if when not in {"end", "begin"}:
        raise ValueError("when must be end or begin")
    if when == "begin":
        pv *= one + r
    return _quantize(pv, ndigits)


def pv_of_uneven_cashflows(rate, flows, *, ndigits=None) -> Decimal:
    """PV of arbitrary timed cashflows.

    `flows` is iterable of (amount, t) pairs OR plain Decimals indexed by period.
    """
    r = Decimal(str(rate))
    one = Decimal(1)
    total = Decimal(0)
    flows = list(flows)
    for i, entry in enumerate(flows):
        if isinstance(entry, tuple):
            amount, t = entry
            amt = Decimal(str(amount))
            t_dec = Decimal(str(t))
        else:
            amt = Decimal(str(entry))
            t_dec = Decimal(i + 1)
        total += amt / (one + r) ** t_dec
    return _quantize(total, ndigits)


def pv_continuous_compounding(rate, t, pmt, *, ndigits=None) -> Decimal:
    """PV of a single payment under continuous compounding: pmt * e^(-rate*t)."""
    factor = Decimal(str(exp(-float(rate) * float(t))))
    pv = Decimal(str(pmt)) * factor
    return _quantize(pv, ndigits)


def pv_of_perpetuity_with_delay(rate, pmt, delay, *, ndigits=None) -> Decimal:
    """Perpetuity that starts after `delay` periods."""
    r = Decimal(str(rate))
    p = Decimal(str(pmt))
    d = Decimal(str(delay))
    one = Decimal(1)
    if r == 0:
        raise ValueError("delayed perpetuity is undefined for rate=0")
    pv = (p / r) / (one + r) ** d
    return _quantize(pv, ndigits)


def pv_of_annuity_continuous(rate, t, pmt, *, ndigits=None) -> Decimal:
    """Continuous-flow annuity: pmt * (1 - e^(-rate*t)) / rate."""
    if float(rate) == 0:
        return _quantize(Decimal(str(pmt)) * Decimal(str(t)), ndigits)
    factor = (1.0 - exp(-float(rate) * float(t))) / float(rate)
    pv = Decimal(str(pmt)) * Decimal(str(factor))
    return _quantize(pv, ndigits)


def pv_of_deferred_annuity(rate, nper, pmt, defer, when="end", *, ndigits=None) -> Decimal:
    """Discount an ordinary or due annuity back by defer periods."""
    if when not in {"end", "begin"}:
        raise ValueError("when must be end or begin")
    r, d = Decimal(str(rate)), Decimal(str(defer))
    value = present_value(r, nper, pmt, when=when)
    return _quantize(value / (Decimal(1) + r) ** d, ndigits)


def pv_of_growing_perpetuity_with_delay(rate, growth, pmt, delay, *, ndigits=None) -> Decimal:
    """Growing perpetuity that begins after `delay` periods."""
    r = Decimal(str(rate))
    g = Decimal(str(growth))
    p = Decimal(str(pmt))
    d = Decimal(str(delay))
    one = Decimal(1)
    if r <= g:
        raise ValueError("rate must exceed growth")
    base = p / (r - g)
    return _quantize(base / (one + r) ** d, ndigits)
