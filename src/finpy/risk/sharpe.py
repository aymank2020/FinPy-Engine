from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math
from statistics import NormalDist


_EULER_MASCHERONI = 0.5772156649015329


def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    std_dev = math.sqrt(variance)
    if std_dev == 0:
        return Decimal(0)
    excess = mean_ret - risk_free_rate
    result = Decimal(str(excess)) / Decimal(str(std_dev))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def adjusted_sharpe(returns: list[float], risk_free_rate: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 3:
        raise ValueError("Need at least 3 returns for adjusted Sharpe")
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return Decimal(0)
    std_dev = math.sqrt(variance)
    excess = mean_ret - risk_free_rate
    sr = excess / std_dev
    skewness = sum((r - mean_ret) ** 3 for r in returns) / n
    skewness = skewness / (std_dev ** 3)
    excess_kurtosis = sum((r - mean_ret) ** 4 for r in returns) / n
    excess_kurtosis = excess_kurtosis / (std_dev ** 4) - 3.0
    adj = sr * (1 + skewness / 6 - excess_kurtosis / 24)
    result = Decimal(str(adj))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _sharpe_ratio_value(returns: list[float], risk_free_rate: float) -> float:
    n = len(returns)
    mean_ret = sum(returns) / n
    variance = sum((r - mean_ret) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std_dev = math.sqrt(variance)
    return (mean_ret - risk_free_rate) / std_dev


def probabilistic_sharpe(returns: list[float], risk_free_rate: float = 0.0, target_sharpe: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 3:
        raise ValueError("Need at least 3 returns for probabilistic Sharpe")
    n = len(returns)
    sr = _sharpe_ratio_value(returns, risk_free_rate)
    if periods_per_year is not None:
        sr *= math.sqrt(periods_per_year)
    skewness = _compute_skewness_stat(returns)
    excess_kurtosis = _compute_kurtosis_stat(returns)
    se_estimate = 1 + 0.5 * sr * sr
    se_estimate += -skewness * sr + (excess_kurtosis - 3) * sr * sr / 4
    se = math.sqrt(se_estimate / n)
    if se == 0:
        if sr > target_sharpe:
            return Decimal(1)
        return Decimal(0)
    z_stat = (sr - target_sharpe) / se
    prob = 0.5 * (1 + math.erf(z_stat / math.sqrt(2)))
    result = Decimal(str(prob))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _compute_skewness_stat(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    return sum((r - mean) ** 3 for r in returns) / (n * std ** 3)


def _compute_kurtosis_stat(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    return sum((r - mean) ** 4 for r in returns) / (n * std ** 4)


def deflated_sharpe_ratio(returns: list[float], risk_free_rate: float = 0.0, num_trials: int = 1, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    """Return the legacy Sharpe score minus an estimated search penalty.

    The result has Sharpe units, not probability units. The penalty retains
    this API's sampling-variance heuristic for the supplied returns; it does
    not estimate variance across trials or implement the 2014 DSR probability.
    With one trial, the expected maximum under a zero-mean null is zero.
    Annualization and moment estimates retain their existing conventions.
    """
    if len(returns) < 4:
        raise ValueError("Need at least 4 returns for deflated Sharpe")
    if isinstance(num_trials, bool) or not isinstance(num_trials, int) or num_trials < 1:
        raise ValueError("num_trials must be a positive integer")
    if periods_per_year is not None and (
        isinstance(periods_per_year, bool)
        or not isinstance(periods_per_year, int)
        or periods_per_year < 1
    ):
        raise ValueError("periods_per_year must be a positive integer")
    if ndigits is not None and (isinstance(ndigits, bool) or not isinstance(ndigits, int)):
        raise ValueError("ndigits must be an integer")
    try:
        finite_inputs = all(not isinstance(r, bool) and math.isfinite(r) for r in returns)
        finite_inputs = finite_inputs and not isinstance(risk_free_rate, bool) and math.isfinite(risk_free_rate)
    except (TypeError, OverflowError) as exc:
        raise ValueError("returns and risk_free_rate must be finite numbers") from exc
    if not finite_inputs:
        raise ValueError("returns and risk_free_rate must be finite numbers")
    n = len(returns)
    try:
        sr_obs = _sharpe_ratio_value(returns, risk_free_rate)
        if periods_per_year is not None:
            sr_obs *= math.sqrt(periods_per_year)
    except (TypeError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError("Legacy Sharpe score is undefined for these inputs") from exc
    if not math.isfinite(sr_obs):
        raise ValueError("Legacy Sharpe score must be finite")
    e_max_sr = 0.0
    if num_trials > 1:
        try:
            skewness = _compute_skewness_stat(returns)
            excess_kurtosis = _compute_kurtosis_stat(returns)
            var_sr = 1 + 0.5 * sr_obs * sr_obs
            var_sr += -skewness * sr_obs + (excess_kurtosis - 3) * sr_obs * sr_obs / 4
        except (TypeError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError("Legacy Sharpe variance estimate is undefined for these inputs") from exc
        if not math.isfinite(var_sr) or var_sr < 0:
            raise ValueError("Legacy Sharpe variance estimate must be finite and nonnegative")
        try:
            tail_probability = 1.0 / num_trials
        except OverflowError as exc:
            raise ValueError("num_trials exceeds the supported floating-point range") from exc
        # Q(1-p) = -Q(p) avoids rounding a small tail probability away to 1.
        e_max_sr = -(1 - _EULER_MASCHERONI) * _inverse_norm(tail_probability)
        e_max_sr -= _EULER_MASCHERONI * _inverse_norm(tail_probability / math.e)
        e_max_sr *= math.sqrt(var_sr / n)
    sr_deflated = sr_obs - e_max_sr
    result = Decimal(str(sr_deflated))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _inverse_norm(p: float) -> float:
    if not math.isfinite(p) or not 0 < p < 1:
        raise ValueError("Normal quantile probability must be finite and between 0 and 1")
    return NormalDist().inv_cdf(p)
