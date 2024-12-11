from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import math


def ytm(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, payments_per_year: int = 2, guess: float = 0.05, *, ndigits: Optional[int] = None) -> Decimal:
    n = int(years_to_maturity * payments_per_year)
    fv = Decimal(str(face_value))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    p = Decimal(str(price))
    one = Decimal(1)
    coupon_pmt = c * fv
    rate = Decimal(str(guess))
    for _ in range(1000):
        price_est = coupon_pmt * (one - (one + rate) ** (-n)) / rate + fv / (one + rate) ** n
        diff = price_est - p
        if abs(diff) < Decimal(1e-10):
            break
        dprice = -coupon_pmt * (one - (one + rate) ** (-n)) / (rate * rate)
        dprice += coupon_pmt * n * (one + rate) ** (-n - 1) / rate
        dprice += -n * fv * (one + rate) ** (-n - 1)
        if dprice == 0:
            rate = rate + Decimal(0.0001)
            continue
        rate = rate - diff / dprice
        if rate <= Decimal(-1):
            rate = Decimal(-0.9999)
    result = rate * Decimal(str(payments_per_year))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def ytm_newton(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, payments_per_year: int = 2, guess: float = 0.05, tolerance: float = 1e-10, max_iter: int = 1000, *, ndigits: Optional[int] = None) -> Decimal:
    n = int(years_to_maturity * payments_per_year)
    fv = Decimal(str(face_value))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    p = Decimal(str(price))
    one = Decimal(1)
    coupon_pmt = c * fv
    rate = Decimal(str(guess))
    for _ in range(max_iter):
        price_est = coupon_pmt * (one - (one + rate) ** (-n)) / rate + fv / (one + rate) ** n
        diff = price_est - p
        if abs(diff) < Decimal(str(tolerance)):
            break
        dprice = -coupon_pmt * (one - (one + rate) ** (-n)) / (rate * rate)
        dprice += coupon_pmt * n * (one + rate) ** (-n - 1) / rate
        dprice += -n * fv * (one + rate) ** (-n - 1)
        if dprice == 0:
            rate = rate + Decimal(0.0001)
            continue
        rate = rate - diff / dprice
        if rate <= Decimal(-1):
            rate = Decimal(-0.9999)
    result = rate * Decimal(str(payments_per_year))
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def approximate_ytm(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    fv = Decimal(str(face_value))
    p = Decimal(str(price))
    c = Decimal(str(coupon_rate)) * fv
    n = int(years_to_maturity * payments_per_year)
    annual_coupon = c
    avg_price = (fv + p) / Decimal(2)
    avg_gain = (fv - p) / Decimal(n / payments_per_year) if n > 0 else Decimal(0)
    result = (annual_coupon + avg_gain) / avg_price
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def ytm_from_dirty_price(dirty_price_val: float, face_value: float, coupon_rate: float, years_to_maturity: float, days_since_last_coupon: int, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    days_in_period = 182
    accrued = Decimal(str(face_value)) * Decimal(str(coupon_rate)) * Decimal(str(days_since_last_coupon)) / Decimal(str(days_in_period * 2))
    clean_p = Decimal(str(dirty_price_val)) - accrued
    return ytm(float(clean_p), face_value, coupon_rate, years_to_maturity, payments_per_year, ndigits=ndigits)


def ytm_zero_coupon(price: float, face_value: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    n = int(years_to_maturity * payments_per_year)
    p = Decimal(str(price))
    fv = Decimal(str(face_value))
    one = Decimal(1)
    result = (fv / p) ** (one / Decimal(n)) - one
    result = result * Decimal(payments_per_year)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def ytm_annual(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, *, ndigits: Optional[int] = None) -> Decimal:
    return ytm(price, face_value, coupon_rate, years_to_maturity, 1, ndigits=ndigits)


def ytm_semi_annual(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, *, ndigits: Optional[int] = None) -> Decimal:
    return ytm(price, face_value, coupon_rate, years_to_maturity, 2, ndigits=ndigits)


def ytm_quarterly(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, *, ndigits: Optional[int] = None) -> Decimal:
    return ytm(price, face_value, coupon_rate, years_to_maturity, 4, ndigits=ndigits)


def ytm_monthly(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, *, ndigits: Optional[int] = None) -> Decimal:
    return ytm(price, face_value, coupon_rate, years_to_maturity, 12, ndigits=ndigits)


def ytm_bisection(price: float, face_value: float, coupon_rate: float, years_to_maturity: float, payments_per_year: int = 2, low: float = -0.99, high: float = 1.0, tolerance: float = 1e-10, *, ndigits: Optional[int] = None) -> Decimal:
    fv = Decimal(str(face_value))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    p = Decimal(str(price))
    n = int(years_to_maturity * payments_per_year)
    one = Decimal(1)
    coupon_pmt = c * fv
    low_rate = Decimal(str(low))
    high_rate = Decimal(str(high))
    for _ in range(200):
        mid = (low_rate + high_rate) / Decimal(2)
        price_mid = coupon_pmt * (one - (one + mid) ** (-n)) / mid + fv / (one + mid) ** n
        price_low = coupon_pmt * (one - (one + low_rate) ** (-n)) / low_rate + fv / (one + low_rate) ** n
        diff = price_mid - p
        if abs(diff) < Decimal(str(tolerance)):
            break
        if (price_low - p) * diff > 0:
            low_rate = mid
        else:
            high_rate = mid
    result = mid * Decimal(payments_per_year)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result
