from decimal import Decimal
from typing import Optional


def is_positive(value: Decimal) -> bool:
    return value > 0


def is_non_negative(value: Decimal) -> bool:
    return value >= 0


def is_zero(value: Decimal) -> bool:
    return value == 0


def clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    if value < low:
        return low
    if value > high:
        return high
    return value


def sign(value: Decimal) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def round_decimal(value: Decimal, ndigits: int = 4) -> Decimal:
    from decimal import ROUND_HALF_UP
    return value.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def percentage_change(old: Decimal, new: Decimal) -> Decimal:
    if old == 0:
        raise ZeroDivisionError("old value cannot be zero")
    return (new - old) / old


def weighted_average(values: list[Decimal], weights: list[Decimal]) -> Decimal:
    if len(values) != len(weights):
        raise ValueError("values and weights must have same length")
    total_weight = sum(weights, Decimal(0))
    if total_weight == 0:
        raise ValueError("total weight cannot be zero")
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def days_in_year(year: int) -> int:
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return 366
    return 365


def days_in_month(year: int, month: int) -> int:
    dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)):
        return 29
    return dim[month - 1]


def years_between(start_year: int, end_year: int) -> int:
    return end_year - start_year


def validate_rate(rate: Decimal, allow_negative: bool = False) -> None:
    if not isinstance(rate, Decimal):
        raise TypeError(f"rate must be Decimal, got {type(rate)}")
    if not allow_negative and rate < 0:
        raise ValueError(f"rate must be non-negative, got {rate}")


def validate_positive(value: Decimal, name: str = "value") -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_non_negative(value: Decimal, name: str = "value") -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def bucket_date(date_str: str) -> dict[str, int]:
    return {"year": int(date_str[0:4]), "month": int(date_str[5:7]), "day": int(date_str[8:10])}


def format_date(year: int, month: int, day: int) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def safe_divide(numerator: Decimal, denominator: Decimal, default: Optional[Decimal] = None) -> Decimal:
    if denominator == 0:
        if default is not None:
            return default
        raise ZeroDivisionError("division by zero")
    return numerator / denominator


def normalize_list(values: list[Decimal]) -> list[Decimal]:
    total = sum(values, Decimal(0))
    if total == 0:
        return [Decimal(0)] * len(values)
    return [v / total for v in values]


def cumulative_sum(values: list[Decimal]) -> list[Decimal]:
    result = []
    running = Decimal(0)
    for v in values:
        running += v
        result.append(running)
    return result


def running_max(values: list[Decimal]) -> list[Decimal]:
    result = []
    if not values:
        return result
    peak = values[0]
    for v in values:
        if v > peak:
            peak = v
        result.append(peak)
    return result


def running_min(values: list[Decimal]) -> list[Decimal]:
    result = []
    if not values:
        return result
    trough = values[0]
    for v in values:
        if v < trough:
            trough = v
        result.append(trough)
    return result


def deduplicate(seq: list) -> list:
    seen = set()
    result = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def batch(seq: list, size: int) -> list[list]:
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def safe_float(value: str) -> float:
    return float(value)


def safe_decimal(value: str) -> Decimal:
    return Decimal(value)


def moving_average(values: list[Decimal], window: int) -> list[Decimal]:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        raise ValueError("values length must be at least window")
    result = []
    for i in range(len(values) - window + 1):
        avg = sum(values[i:i + window], Decimal(0)) / Decimal(window)
        result.append(avg)
    return result


def moving_sum(values: list[Decimal], window: int) -> list[Decimal]:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        raise ValueError("values length must be at least window")
    result = []
    for i in range(len(values) - window + 1):
        total = sum(values[i:i + window], Decimal(0))
        result.append(total)
    return result


def difference(values: list[Decimal]) -> list[Decimal]:
    if len(values) < 2:
        raise ValueError("need at least 2 values")
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def lag(values: list[Decimal], periods: int = 1) -> list[Optional[Decimal]]:
    if periods <= 0:
        raise ValueError("periods must be positive")
    result: list[Optional[Decimal]] = [None] * periods
    for v in values[:-periods]:
        result.append(v)
    return result


def lead(values: list[Decimal], periods: int = 1) -> list[Optional[Decimal]]:
    if periods <= 0:
        raise ValueError("periods must be positive")
    result = list(values[periods:])
    result.extend([None] * periods)
    return result


def rank(values: list[Decimal]) -> list[int]:
    sorted_vals = sorted(values, reverse=True)
    return [sorted_vals.index(v) + 1 for v in values]


def percentile(values: list[Decimal], pct: Decimal) -> Decimal:
    if not values:
        raise ValueError("values list must be non-empty")
    if pct < 0 or pct > 1:
        raise ValueError("percentile must be between 0 and 1")
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    k = int(pct * Decimal(n - 1))
    return sorted_vals[k]


def interquartile_range(values: list[Decimal]) -> Decimal:
    q1 = percentile(values, Decimal('0.25'))
    q3 = percentile(values, Decimal('0.75'))
    return q3 - q1


def is_outlier(value: Decimal, values: list[Decimal], factor: Decimal = Decimal('1.5')) -> bool:
    q1 = percentile(values, Decimal('0.25'))
    q3 = percentile(values, Decimal('0.75'))
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return value < lower or value > upper


def z_score(value: Decimal, mean: Decimal, std_dev: Decimal) -> Decimal:
    if std_dev == 0:
        return Decimal(0)
    return (value - mean) / std_dev
