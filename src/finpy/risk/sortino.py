from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


def sortino_ratio(returns: list[float], risk_free_rate: float = 0.0, target_return: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    mean_ret = sum(returns) / n
    downside_var = sum(min(r - target_return, 0) ** 2 for r in returns) / (n - 1)
    downside_std = math.sqrt(downside_var)
    if downside_std == 0:
        return Decimal(0)
    excess = mean_ret - risk_free_rate
    result = Decimal(str(excess)) / Decimal(str(downside_std))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def downside_deviation(returns: list[float], target_return: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    downside_var = sum(min(r - target_return, 0) ** 2 for r in returns) / (n - 1)
    result = Decimal(str(math.sqrt(downside_var)))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def upside_potential_ratio(returns: list[float], target_return: float = 0.0, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    upside = sum(max(r - target_return, 0) for r in returns) / n
    downside_var = sum(min(r - target_return, 0) ** 2 for r in returns) / (n - 1)
    downside_std = math.sqrt(downside_var)
    if downside_std == 0:
        if upside > 0:
            return Decimal('Inf')
        return Decimal(0)
    result = Decimal(str(upside)) / Decimal(str(downside_std))
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def omega_ratio(returns: list[float], target_return: float = 0.0, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    sorted_ret = sorted(returns)
    gains = sum(r - target_return for r in sorted_ret if r > target_return)
    losses = sum(target_return - r for r in sorted_ret if r < target_return)
    if losses == 0:
        if gains > 0:
            return Decimal('Inf')
        return Decimal(1)
    result = Decimal(str(gains)) / Decimal(str(losses))
    result += Decimal(1)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def sortino_with_target(returns: list[float], risk_free_rate: float = 0.0, target_return: float = 0.0, target_downside: float = 0.05, periods_per_year: Optional[int] = None, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    mean_ret = sum(returns) / n
    downside_var = sum(min(r - target_return, 0) ** 2 for r in returns) / (n - 1)
    downside_std = math.sqrt(downside_var)
    if downside_std == 0:
        return Decimal(0)
    excess = mean_ret - risk_free_rate
    min_accepted = Decimal(str(target_downside))
    dd_target = max(Decimal(str(downside_std)), min_accepted)
    result = Decimal(str(excess)) / dd_target
    if periods_per_year is not None:
        result *= Decimal(str(math.sqrt(periods_per_year)))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result
