from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


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
    if len(returns) < 4:
        raise ValueError("Need at least 4 returns for deflated Sharpe")
    if num_trials < 1:
        raise ValueError("num_trials must be at least 1")
    n = len(returns)
    sr_obs = _sharpe_ratio_value(returns, risk_free_rate)
    if periods_per_year is not None:
        sr_obs *= math.sqrt(periods_per_year)
    skewness = _compute_skewness_stat(returns)
    excess_kurtosis = _compute_kurtosis_stat(returns)
    var_sr = 1 + 0.5 * sr_obs * sr_obs
    var_sr += -skewness * sr_obs + (excess_kurtosis - 3) * sr_obs * sr_obs / 4
    e_max_sr = (1 - math.euler_gamma) * _inverse_norm(1 - 1.0 / num_trials) + math.euler_gamma * _inverse_norm(1 - 1.0 / (num_trials * math.e))
    e_max_sr *= math.sqrt(var_sr / n)
    sr_deflated = sr_obs - e_max_sr
    result = Decimal(str(sr_deflated))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _inverse_norm(p: float) -> float:
    return math.sqrt(2) * _inverse_erf(2 * p - 1)


def _inverse_erf(x: float) -> float:
    if abs(x) >= 1:
        return math.copysign(float('inf'), x)
    sign = 1 if x >= 0 else -1
    x = abs(x)
    if x <= 0.7:
        a, b, c, d = 0.886226899, -1.645349621, 0.914624893, -0.140543331
        w = x * x
        y = x * (((d * w + c) * w + b) * w + a)
    else:
        a, b, c, d = 1.641345311, 2.429788304, -1.550491497, 1.0
        w = -math.log(1 - x)
        y = (((d * w + c) * w + b) * w + a) * math.sqrt(w)
    return sign * y
