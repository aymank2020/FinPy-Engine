"""Historical VaR + tail-risk extensions.

Tests expect the wider VaR family beyond the simple historical_var:
    historical_cvar(returns, confidence) -> Decimal
    historical_var_multiple_periods(returns, confidence_levels) -> dict
    var_backtest(returns, var_estimates, confidence) -> dict
    cvar_backtest(returns, cvar_estimates, confidence) -> dict
    expected_shortfall(returns, confidence) -> Decimal      (= historical_cvar)
    marginal_var(portfolio, asset, confidence) -> Decimal
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


def historical_var(returns, confidence_level=0.95, *, ndigits=None) -> Decimal:
    if not returns:
        raise ValueError("Returns list is empty")
    sorted_returns = sorted(_to_decimal_list(returns))
    index = int((1 - float(confidence_level)) * len(sorted_returns))
    if index >= len(sorted_returns):
        index = len(sorted_returns) - 1
    if index < 0:
        index = 0
    result = abs(sorted_returns[index])
    return _quantize(result, ndigits)


def historical_cvar(returns, confidence_level=0.95, *, ndigits=None) -> Decimal:
    """CVaR / Expected Shortfall — average loss in the tail past the VaR."""
    if not returns:
        raise ValueError("Returns list is empty")
    rs = sorted(_to_decimal_list(returns))
    cutoff = int((1 - float(confidence_level)) * len(rs))
    if cutoff < 1:
        cutoff = 1
    tail = rs[:cutoff]
    avg = sum(tail) / Decimal(len(tail))
    return _quantize(abs(avg), ndigits)


def expected_shortfall(returns, confidence_level=0.95, *, ndigits=None) -> Decimal:
    """Synonym for historical_cvar — what risk people mean by ES."""
    return historical_cvar(returns, confidence_level, ndigits=ndigits)


def historical_var_multiple_periods(returns, confidence_levels, *, ndigits=None) -> dict:
    """Compute historical VaR at several confidence levels in one pass."""
    if not returns:
        raise ValueError("returns is empty")
    if not confidence_levels:
        raise ValueError("confidence_levels is empty")
    out = {}
    for c in confidence_levels:
        c_f = float(c)
        if not (0 < c_f < 1):
            raise ValueError(f"confidence level must be in (0,1); got {c}")
        out[c] = historical_var(returns, c_f, ndigits=ndigits)
    return out


def var_backtest(actual_returns, var_estimates, confidence_level=0.95, *, ndigits=None) -> dict:
    """Number / fraction of breaches: actual loss exceeds estimated VaR."""
    if len(actual_returns) != len(var_estimates):
        raise ValueError("actual_returns and var_estimates must align")
    if len(actual_returns) < 2:
        raise ValueError("need at least 2 observations to backtest")
    actuals = _to_decimal_list(actual_returns)
    vars_ = _to_decimal_list(var_estimates)
    breaches = 0
    for a, v in zip(actuals, vars_):
        if -a > v:  # loss exceeds VaR
            breaches += 1
    n = len(actuals)
    expected = (1 - Decimal(str(confidence_level))) * Decimal(n)
    out = {
        "breaches": Decimal(breaches),
        "n": Decimal(n),
        "breach_rate": Decimal(breaches) / Decimal(n),
        "expected_breaches": expected,
    }
    if ndigits is not None:
        out = {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in out.items()}
    return out


def cvar_backtest(actual_returns, cvar_estimates, confidence_level=0.95, *, ndigits=None) -> dict:
    """Average shortfall vs estimated CVaR, restricted to tail breaches."""
    if len(actual_returns) != len(cvar_estimates):
        raise ValueError("actual_returns and cvar_estimates must align")
    if len(actual_returns) < 2:
        raise ValueError("need at least 2 observations to backtest")
    actuals = _to_decimal_list(actual_returns)
    cvars_ = _to_decimal_list(cvar_estimates)
    tail_diffs = []
    for a, c in zip(actuals, cvars_):
        if -a > c:
            tail_diffs.append(-a - c)  # excess shortfall
    avg_excess = sum(tail_diffs) / Decimal(len(tail_diffs)) if tail_diffs else Decimal(0)
    out = {
        "tail_breaches": Decimal(len(tail_diffs)),
        "avg_tail_excess": avg_excess,
    }
    if ndigits is not None:
        out = {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in out.items()}
    return out


def marginal_var(portfolio_returns, asset_returns, confidence_level=0.95, *, ndigits=None) -> Decimal:
    """Marginal VaR — sensitivity of portfolio VaR to a small position change.

    Approximation: VaR(portfolio) - VaR(portfolio - asset).
    """
    if len(portfolio_returns) != len(asset_returns):
        raise ValueError("portfolio_returns and asset_returns must align")
    if len(portfolio_returns) < 2:
        raise ValueError("need at least 2 observations")
    p = _to_decimal_list(portfolio_returns)
    a = _to_decimal_list(asset_returns)
    p_minus_a = [pi - ai for pi, ai in zip(p, a)]
    var_full = historical_var(p, confidence_level)
    var_excl = historical_var(p_minus_a, confidence_level)
    return _quantize(var_full - var_excl, ndigits)
