from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


def parametric_var(mean: float, std: float, confidence_level: float = 0.95, *, ndigits: Optional[int] = None) -> Decimal:
    z_scores = {0.90: 1.2816, 0.95: 1.6449, 0.99: 2.3263}
    z = z_scores.get(confidence_level)
    if z is None:
        p = confidence_level
        z = math.sqrt(2) * _inverse_erf(2 * p - 1)
    result = abs(Decimal(str(mean)) - Decimal(str(z)) * Decimal(str(std)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


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


def parametric_var_portfolio(weights: list[float], cov_matrix: list[list[float]], confidence_level: float = 0.95, *, ndigits: Optional[int] = None) -> Decimal:
    n_assets = len(weights)
    if n_assets == 0:
        raise ValueError("Weights list is empty")
    if len(cov_matrix) != n_assets:
        raise ValueError("Covariance matrix must match number of assets")
    for row in cov_matrix:
        if len(row) != n_assets:
            raise ValueError("Covariance matrix must be square")
    portfolio_variance = Decimal(0)
    for i in range(n_assets):
        for j in range(n_assets):
            portfolio_variance += Decimal(str(weights[i])) * Decimal(str(weights[j])) * Decimal(str(cov_matrix[i][j]))
    portfolio_std = float(portfolio_variance.sqrt())
    z_scores = {0.90: 1.2816, 0.95: 1.6449, 0.99: 2.3263}
    z = z_scores.get(confidence_level)
    if z is None:
        p = confidence_level
        z = math.sqrt(2) * _inverse_erf(2 * p - 1)
    result = Decimal(str(z)) * Decimal(str(portfolio_std))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def _compute_skewness(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    skew = sum((r - mean) ** 3 for r in returns) / n
    skew = skew / (std ** 3)
    return skew


def _compute_kurtosis(returns: list[float]) -> float:
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return 0.0
    std = math.sqrt(variance)
    kurt = sum((r - mean) ** 4 for r in returns) / n
    kurt = kurt / (std ** 4) - 3.0
    return kurt


def cornish_fisher_var(mean: float, std: float, skewness: float, kurtosis: float, confidence_level: float = 0.95, *, ndigits: Optional[int] = None) -> Decimal:
    z_scores = {0.90: 1.2816, 0.95: 1.6449, 0.99: 2.3263}
    z = z_scores.get(confidence_level)
    if z is None:
        p = confidence_level
        z = math.sqrt(2) * _inverse_erf(2 * p - 1)
    z_cf = z + (z * z - 1) * skewness / 6 + (z * z * z - 3 * z) * kurtosis / 24 - (2 * z * z * z - 5 * z) * skewness * skewness / 36
    result = abs(Decimal(str(mean)) - Decimal(str(z_cf)) * Decimal(str(std)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def modified_var(returns: list[float], confidence_level: float = 0.95, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 3:
        raise ValueError("Need at least 3 returns for modified VaR")
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if variance == 0:
        return Decimal(0)
    std = math.sqrt(variance)
    skewness = _compute_skewness(returns)
    kurtosis = _compute_kurtosis(returns)
    result = cornish_fisher_var(mean, std, skewness, kurtosis, confidence_level, ndigits=ndigits)
    return result
