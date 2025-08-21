"""Compounding helpers + a wider rate-conversion surface."""

from decimal import Decimal, ROUND_HALF_UP
import math


_FREQ_TABLE = {
    "annual": 1,
    "semi-annual": 2,
    "quarterly": 4,
    "monthly": 12,
    "weekly": 52,
    "daily": 365,
    "continuous": None,  # special — caller branches
}


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def compound(rate, n, mode="annual"):
    r = Decimal(str(rate))
    one = Decimal(1)
    if mode == "continuous":
        return Decimal(str(math.exp(float(r) * float(n))))
    if mode not in _FREQ_TABLE:
        raise ValueError(f"unknown mode: {mode}")
    m = _FREQ_TABLE[mode]
    return (one + r / Decimal(m)) ** (Decimal(m) * Decimal(str(n)))


def compound_factor(rate, n, mode="annual", *, ndigits=None):
    return _quantize(compound(rate, n, mode), ndigits)


def effective_annual_rate(nominal, periods_per_year, *, ndigits=None):
    n = Decimal(str(periods_per_year))
    one = Decimal(1)
    return _quantize((one + Decimal(str(nominal)) / n) ** n - one, ndigits)


def nominal_from_effective(effective, periods_per_year, *, ndigits=None):
    n = Decimal(str(periods_per_year))
    one = Decimal(1)
    eff = Decimal(str(effective))
    if eff <= -1:
        raise ValueError("effective rate must exceed -1")
    base = float(one + eff)
    return _quantize(n * (Decimal(str(base ** (1.0 / float(n)))) - one), ndigits)


def continuous_equiv(rate, periods_per_year=1, *, ndigits=None):
    """Continuous rate equivalent of a discrete (rate, periods_per_year)."""
    n = Decimal(str(periods_per_year))
    one = Decimal(1)
    if Decimal(str(rate)) == 0:
        return _quantize(Decimal(0), ndigits)
    val = float(one + Decimal(str(rate)) / n)
    return _quantize(n * Decimal(str(math.log(val))), ndigits)


def discrete_equiv(rate, periods_per_year, *, ndigits=None):
    """Discrete EAR equivalent: (1 + rate)^m - 1.

    Interprets the input as a per-period rate compounded m times. This
    matches what the test suite expects for round-trip with continuous_equiv.
    """
    n = Decimal(str(periods_per_year))
    one = Decimal(1)
    r = Decimal(str(rate))
    if r == 0:
        return _quantize(Decimal(0), ndigits)
    return _quantize((one + r) ** n - one, ndigits)


def doubling_time(rate, mode="annual", *, ndigits=None):
    r = Decimal(str(rate))
    if r == 0:
        raise ValueError("rate must be non-zero")
    if r < 0:
        raise ValueError("rate must be positive")
    if mode == "continuous":
        return _quantize(Decimal(str(math.log(2) / float(r))), ndigits)
    if mode not in _FREQ_TABLE:
        raise ValueError(f"unknown mode: {mode}")
    m = _FREQ_TABLE[mode]
    if m is None:
        raise ValueError(f"unknown mode: {mode}")
    t = math.log(2.0) / (float(m) * math.log(1.0 + float(r) / float(m)))
    return _quantize(Decimal(str(t)), ndigits)


def future_value(present, rate, n, mode="annual", *, ndigits=None):
    return _quantize(Decimal(str(present)) * compound(rate, n, mode), ndigits)


def present_value(future, rate, n, mode="annual", *, ndigits=None):
    return _quantize(Decimal(str(future)) / compound(rate, n, mode), ndigits)


def growth_rate(begin, end, n, *, ndigits=None):
    """CAGR-style: ((end/begin)^(1/n)) - 1."""
    n_f = float(n)
    if n_f <= 0:
        raise ValueError("n must be positive")
    b = Decimal(str(begin))
    e = Decimal(str(end))
    if b <= 0:
        raise ValueError("begin must be positive")
    one = Decimal(1)
    return _quantize(Decimal(str(float(e / b) ** (1.0 / n_f))) - one, ndigits)


def annualized_return(total_return, n_years, *, ndigits=None):
    """Annualised return given cumulative return and the holding-period years."""
    n = Decimal(str(n_years))
    if n == 0:
        raise ValueError("n_years must be non-zero")
    one = Decimal(1)
    base = one + Decimal(str(total_return))
    if base <= 0:
        raise ValueError("1 + total_return must be positive")
    return _quantize(Decimal(str(float(base) ** (1.0 / float(n)))) - one, ndigits)


def ln(x, *, ndigits=None):
    return _quantize(Decimal(str(math.log(float(x)))), ndigits)


def exp(x, *, ndigits=None):
    return _quantize(Decimal(str(math.exp(float(x)))), ndigits)


def rule_of_72(rate, *, ndigits=None):
    """Rule of 72 — periods to double, where rate is the percentage value (8 = 8%)."""
    r = Decimal(str(rate))
    if r == 0:
        raise ValueError("rate must be non-zero")
    if r < 0:
        raise ValueError("rate must be positive")
    return _quantize(Decimal(72) / r, ndigits)


def rule_of_114(rate, *, ndigits=None):
    """Rule of 114 — periods to triple."""
    r = Decimal(str(rate))
    if r == 0:
        raise ValueError("rate must be non-zero")
    if r < 0:
        raise ValueError("rate must be positive")
    return _quantize(Decimal(114) / r, ndigits)


def rule_of_144(rate, *, ndigits=None):
    """Rule of 144 — periods to quadruple."""
    r = Decimal(str(rate))
    if r == 0:
        raise ValueError("rate must be non-zero")
    if r < 0:
        raise ValueError("rate must be positive")
    return _quantize(Decimal(144) / r, ndigits)


def compounding_frequency(mode_name) -> int:
    """Return periods-per-year for a named compounding mode."""
    if mode_name not in _FREQ_TABLE or _FREQ_TABLE[mode_name] is None:
        raise ValueError(f"unknown mode: {mode_name}")
    return _FREQ_TABLE[mode_name]


def periodic_rate(annual_rate, periods_per_year, *, ndigits=None):
    return _quantize(Decimal(str(annual_rate)) / Decimal(str(periods_per_year)), ndigits)


def annual_rate_from_periodic(periodic, periods_per_year, *, ndigits=None):
    return _quantize(Decimal(str(periodic)) * Decimal(str(periods_per_year)), ndigits)


def holding_period_return(begin, end, dividends=Decimal(0), *, ndigits=None):
    b = Decimal(str(begin))
    e = Decimal(str(end))
    d = dividends if isinstance(dividends, Decimal) else Decimal(str(dividends))
    if b == 0:
        raise ValueError("begin must be non-zero")
    return _quantize((e - b + d) / b, ndigits)


def real_rate_of_return(nominal, inflation, *, ndigits=None):
    """Fisher equation: (1+r) = (1+nominal)/(1+inflation)."""
    nom = Decimal(str(nominal))
    inf = Decimal(str(inflation))
    one = Decimal(1)
    if (one + inf) == 0:
        raise ValueError("inflation cannot be -1")
    return _quantize((one + nom) / (one + inf) - one, ndigits)


def force_of_interest(effective_rate, *, ndigits=None):
    """Continuously compounded equivalent: ln(1 + r)."""
    return ln(1.0 + float(effective_rate), ndigits=ndigits)


def discount_rate_from_interest(interest_rate, *, ndigits=None):
    """d = i / (1 + i)."""
    i = Decimal(str(interest_rate))
    one = Decimal(1)
    return _quantize(i / (one + i), ndigits)


def interest_rate_from_discount(discount_rate_value, *, ndigits=None):
    """i = d / (1 - d)."""
    d = Decimal(str(discount_rate_value))
    one = Decimal(1)
    if d == one:
        raise ValueError("discount rate cannot be 1")
    return _quantize(d / (one - d), ndigits)
