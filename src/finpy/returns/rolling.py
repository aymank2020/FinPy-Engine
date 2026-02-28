from decimal import Decimal
from typing import Callable, Optional


def rolling_mean(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        results.append(Decimal(str(sum(window) / window_size)))
    return results


def rolling_std(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    import math
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        mean = sum(window) / window_size
        variance = sum((x - mean) ** 2 for x in window) / (window_size - 1)
        results.append(Decimal(str(math.sqrt(variance))))
    return results


def rolling_window(data: list[float], window_size: int, func: Callable[[list[float]], float]) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        results.append(Decimal(str(func(window))))
    return results


def rolling_sum(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        results.append(Decimal(str(sum(data[i: i + window_size]))))
    return results


def rolling_min(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        results.append(Decimal(str(min(data[i: i + window_size]))))
    return results


def rolling_max(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        results.append(Decimal(str(max(data[i: i + window_size]))))
    return results


def rolling_median(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = sorted(data[i: i + window_size])
        n = len(window)
        if n % 2 == 0:
            med = (window[n // 2 - 1] + window[n // 2]) / 2.0
        else:
            med = window[n // 2]
        results.append(Decimal(str(med)))
    return results


def rolling_var(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        mean = sum(window) / window_size
        variance = sum((x - mean) ** 2 for x in window) / (window_size - 1)
        results.append(Decimal(str(variance)))
    return results


def rolling_cov(data1: list[float], data2: list[float], window_size: int) -> list[Decimal]:
    if len(data1) != len(data2):
        raise ValueError("Both data series must have same length")
    if len(data1) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data1) - window_size + 1):
        w1 = data1[i: i + window_size]
        w2 = data2[i: i + window_size]
        m1 = sum(w1) / window_size
        m2 = sum(w2) / window_size
        cov = sum((a - m1) * (b - m2) for a, b in zip(w1, w2)) / (window_size - 1)
        results.append(Decimal(str(cov)))
    return results


def rolling_corr(data1: list[float], data2: list[float], window_size: int) -> list[Decimal]:
    cov = rolling_cov(data1, data2, window_size)
    std1 = rolling_std(data1, window_size)
    std2 = rolling_std(data2, window_size)
    results = []
    for c, s1, s2 in zip(cov, std1, std2):
        if s1 == 0 or s2 == 0:
            results.append(Decimal(0))
        else:
            results.append(c / (s1 * s2))
    return results


def rolling_skew(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        n = len(window)
        mean = sum(window) / n
        variance = sum((x - mean) ** 2 for x in window) / (n - 1)
        if variance < 1e-100:
            results.append(Decimal(0))
        else:
            s = variance ** 0.5
            third = sum((x - mean) ** 3 for x in window) / n
            results.append(Decimal(str(third / (s ** 3))))
    return results


def rolling_kurtosis(data: list[float], window_size: int) -> list[Decimal]:
    if len(data) < window_size:
        raise ValueError("Data length must be at least window_size")
    results = []
    for i in range(len(data) - window_size + 1):
        window = data[i: i + window_size]
        n = len(window)
        mean = sum(window) / n
        variance = sum((x - mean) ** 2 for x in window) / (n - 1)
        if variance < 1e-140:
            results.append(Decimal(0))
        else:
            s = variance ** 0.5
            fourth = sum((x - mean) ** 4 for x in window) / n
            results.append(Decimal(str(fourth / (s ** 4) - 3)))
    return results


def ewm_mean(data: list[float], alpha: float = 0.1) -> list[Decimal]:
    if not data:
        raise ValueError("Data must be non-empty")
    if alpha <= 0 or alpha > 1:
        raise ValueError("alpha must be in (0, 1]")
    results = []
    ema = Decimal(str(data[0]))
    results.append(ema)
    a = Decimal(str(alpha))
    one_minus_a = Decimal(1) - a
    for i in range(1, len(data)):
        ema = a * Decimal(str(data[i])) + one_minus_a * ema
        results.append(ema)
    return results


def ewm_std(data: list[float], alpha: float = 0.1) -> list[Decimal]:
    if len(data) < 2:
        raise ValueError("Need at least 2 data points")
    means = ewm_mean(data, alpha)
    a = Decimal(str(alpha))
    results = []
    variance = Decimal(0)
    for i in range(1, len(data)):
        diff = Decimal(str(data[i])) - means[i]
        variance = a * (diff ** 2) + (Decimal(1) - a) * variance
        results.append(variance.sqrt())
    return results
