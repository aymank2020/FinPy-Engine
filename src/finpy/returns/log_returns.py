"""Return-series statistics.

Despite the file name, this module also hosts the simple-return and the suite
of summary statistics tests expect: cumulative, geometric, arithmetic means,
variance/std, skewness, kurtosis, semivariance/downside std, plus annualised
flavours and ratio metrics (information ratio, gain/loss).

Why one file? The return-series statistics conceptually move together —
splitting them across many small files would create a forest of one-function
modules that duplicate imports and validation. I kept them here for that.
"""

from decimal import Decimal, ROUND_HALF_UP


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def _to_decimal_list(values):
    out = []
    for v in values:
        out.append(v if isinstance(v, Decimal) else Decimal(str(v)))
    return out


def log_returns(prices, *, ndigits=None):
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    results = []
    for i in range(1, len(prices)):
        r = Decimal(str(prices[i])) / Decimal(str(prices[i - 1]))
        val = r.ln()
        results.append(_quantize(val, ndigits))
    return results


def simple_returns(prices, *, ndigits=None):
    """Period-over-period simple returns: (P_t - P_{t-1}) / P_{t-1}."""
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    out = []
    for i in range(1, len(prices)):
        prev = Decimal(str(prices[i - 1]))
        curr = Decimal(str(prices[i]))
        out.append(_quantize((curr - prev) / prev, ndigits))
    return out


def cumulative_return(prices, *, ndigits=None):
    """Total return from first to last price as a decimal."""
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    first = Decimal(str(prices[0]))
    last = Decimal(str(prices[-1]))
    return _quantize((last - first) / first, ndigits)


def total_return(returns, *, ndigits=None):
    """Compound the period returns into one cumulative figure."""
    if not returns:
        raise ValueError("Returns list is empty")
    one = Decimal(1)
    acc = one
    for r in _to_decimal_list(returns):
        acc *= one + r
    return _quantize(acc - one, ndigits)


def arithmetic_mean(values, *, ndigits=None):
    if not values:
        raise ValueError("values is empty")
    vs = _to_decimal_list(values)
    return _quantize(sum(vs) / Decimal(len(vs)), ndigits)


def geometric_mean(returns, *, ndigits=None):
    """Geometric mean of period returns: ((prod(1+r))^(1/n)) - 1."""
    if not returns:
        raise ValueError("returns is empty")
    rs = _to_decimal_list(returns)
    one = Decimal(1)
    acc = one
    for r in rs:
        if (one + r) <= 0:
            raise ValueError("non-positive 1+r encountered in geometric_mean")
        acc *= one + r
    n = Decimal(len(rs))
    root = acc ** (one / n)
    return _quantize(root - one, ndigits)


def variance(values, *, ddof=1, ndigits=None):
    if len(values) < 2:
        raise ValueError("variance needs at least 2 values")
    vs = _to_decimal_list(values)
    m = sum(vs) / Decimal(len(vs))
    sq = sum((v - m) ** 2 for v in vs)
    if ddof < 0 or ddof >= len(vs):
        raise ValueError("ddof must satisfy 0 <= ddof < sample size")
    denom = Decimal(len(vs) - ddof)
    return _quantize(sq / denom, ndigits)


def std(values, *, ddof=1, ndigits=None):
    var = variance(values, ddof=ddof)
    sd = var.sqrt()
    return _quantize(sd, ndigits)


def skewness(values, *, ndigits=None):
    if len(values) < 3:
        raise ValueError("skewness needs at least 3 values")
    vs = _to_decimal_list(values)
    n = Decimal(len(vs))
    m = sum(vs) / n
    sd = Decimal(str(float(sum((v - m) ** 2 for v in vs) / n) ** 0.5))
    if sd == 0:
        return _quantize(Decimal(0), ndigits)
    s = sum(((v - m) / sd) ** 3 for v in vs) / n
    return _quantize(s, ndigits)


def kurtosis(values, *, ndigits=None, excess=True):
    if len(values) < 4:
        raise ValueError("kurtosis needs at least 4 values")
    vs = _to_decimal_list(values)
    n = Decimal(len(vs))
    m = sum(vs) / n
    var = sum((v - m) ** 2 for v in vs) / n
    if var == 0:
        return _quantize(Decimal(0), ndigits)
    k = sum((v - m) ** 4 for v in vs) / n / (var ** 2)
    if excess:
        k -= Decimal(3)
    return _quantize(k, ndigits)


def semivariance(returns, target=Decimal(0), *, ndigits=None):
    """Lower-partial variance vs target — average of squared shortfalls."""
    if not returns:
        raise ValueError("returns is empty")
    rs = _to_decimal_list(returns)
    tgt = target if isinstance(target, Decimal) else Decimal(str(target))
    shortfalls = [(r - tgt) ** 2 for r in rs if r < tgt]
    if not shortfalls:
        return _quantize(Decimal(0), ndigits)
    return _quantize(sum(shortfalls) / Decimal(len(rs)), ndigits)


def downside_std(returns, target=Decimal(0), *, ndigits=None):
    sv = semivariance(returns, target)
    return _quantize(sv.sqrt(), ndigits)


def annualized_return(returns, periods_per_year, *, ndigits=None):
    """Annualize period-return samples, or a scalar total return over years.

    The sequence form uses observations per year; the scalar form uses the
    second argument as elapsed years, matching core.compounding.annualized_return.
    """
    if isinstance(returns, (Decimal, int, float, str)):
        from finpy.core.compounding import annualized_return as annualize_total
        return annualize_total(returns, periods_per_year, ndigits=ndigits)
    if not returns:
        raise ValueError("returns is empty")
    frequency = Decimal(str(periods_per_year))
    if frequency <= 0:
        raise ValueError("periods_per_year must be positive")
    g = geometric_mean(returns)
    ann = (Decimal(1) + g) ** frequency - Decimal(1)
    return _quantize(ann, ndigits)


def annualized_volatility(returns, periods_per_year, *, ndigits=None):
    if len(returns) < 2:
        raise ValueError("volatility needs at least 2 returns")
    rs = _to_decimal_list(returns)
    if all(r == rs[0] for r in rs):
        return _quantize(Decimal(0), ndigits)
    s = std(rs)
    ann = s * Decimal(str(float(periods_per_year) ** 0.5))
    return _quantize(ann, ndigits)


def annualized_std(returns, periods_per_year, *, ndigits=None):
    return annualized_volatility(returns, periods_per_year, ndigits=ndigits)


def information_ratio(portfolio, benchmark, *, ndigits=None):
    if len(portfolio) != len(benchmark) or len(portfolio) < 2:
        raise ValueError("portfolio and benchmark must align and have length >= 2")
    p = _to_decimal_list(portfolio)
    b = _to_decimal_list(benchmark)
    active = [pi - bi for pi, bi in zip(p, b)]
    avg = sum(active) / Decimal(len(active))
    sd = std(active)
    if sd == 0:
        return _quantize(Decimal(0), ndigits)
    return _quantize(avg / sd, ndigits)


def tracking_error(portfolio, benchmark, *, ndigits=None):
    if len(portfolio) != len(benchmark) or len(portfolio) < 2:
        raise ValueError("portfolio and benchmark must align and have length >= 2")
    p = _to_decimal_list(portfolio)
    b = _to_decimal_list(benchmark)
    active = [pi - bi for pi, bi in zip(p, b)]
    return _quantize(std(active), ndigits)


def gain_loss_ratio(returns, *, ndigits=None):
    if not returns:
        raise ValueError("returns is empty")
    rs = _to_decimal_list(returns)
    gains = sum(r for r in rs if r > 0)
    losses = sum(-r for r in rs if r < 0)
    if losses == 0:
        return _quantize(Decimal("Infinity") if gains > 0 else Decimal(0), ndigits)
    return _quantize(gains / losses, ndigits)
