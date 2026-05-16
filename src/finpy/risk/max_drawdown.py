from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


def max_drawdown(prices: list[float], *, ndigits: Optional[int] = None) -> Decimal:
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    peak = prices[0]
    max_dd = 0.0
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        if dd > max_dd:
            max_dd = dd
    result = Decimal(str(max_dd))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def drawdown_series(prices: list[float], *, ndigits: Optional[int] = None) -> list[Decimal]:
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    peak = prices[0]
    results: list[Decimal] = []
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        d = Decimal(str(dd))
        if ndigits is not None:
            d = d.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
        results.append(d)
    return results


def average_drawdown(prices: list[float], *, ndigits: Optional[int] = None) -> Decimal:
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    dds = drawdown_series(prices)
    total = sum(dds[1:], Decimal(0))
    count = len(dds) - 1
    if count == 0:
        return Decimal(0)
    result = total / Decimal(str(count))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def drawdown_duration(prices: list[float], *, ndigits: Optional[int] = None) -> int:
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    peak = prices[0]
    peak_idx = 0
    max_duration = 0
    current_duration = 0
    in_drawdown = False
    for i, price in enumerate(prices):
        if price > peak:
            peak = price
            peak_idx = i
            in_drawdown = False
            current_duration = 0
        elif price < peak:
            if not in_drawdown:
                in_drawdown = True
                current_duration = 1
            else:
                current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
    return max_duration


def calmar_ratio(returns: list[float], periods_per_year: int = 252, *, ndigits: Optional[int] = None) -> Decimal:
    if len(returns) < 2:
        raise ValueError("Need at least 2 returns")
    n = len(returns)
    cumulative = Decimal(1)
    for r in returns:
        cumulative *= Decimal(1) + Decimal(str(r))
    ann_factor = Decimal(str(periods_per_year)) / Decimal(str(n))
    ann_return = cumulative ** ann_factor - Decimal(1)
    prices: list[float] = []
    price = 100.0
    prices.append(price)
    for r in returns:
        price *= (1 + r)
        prices.append(price)
    md = max_drawdown(prices)
    if md == 0:
        return Decimal(0)
    result = ann_return / md
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def ulcer_index(prices: list[float], *, ndigits: Optional[int] = None) -> Decimal:
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices")
    peak = prices[0]
    sum_sq = Decimal(0)
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        d = Decimal(str(dd))
        sum_sq += d * d
    result = (sum_sq / Decimal(str(len(prices)))).sqrt()
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result
