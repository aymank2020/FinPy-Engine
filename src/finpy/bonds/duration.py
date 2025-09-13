from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def macaulay_duration(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    n = int(years_to_maturity * payments_per_year)
    r = Decimal(str(ytm)) / Decimal(str(payments_per_year))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    fv = Decimal(str(face_value))
    m = Decimal(str(payments_per_year))
    one = Decimal(1)
    coupon_pmt = c * fv
    numerator = Decimal(0)
    for t in range(1, n + 1):
        cf = coupon_pmt if t < n else coupon_pmt + fv
        numerator += Decimal(str(t)) * cf / (one + r) ** Decimal(str(t))
    denominator = coupon_pmt * (one - (one + r) ** (-n)) / r + fv / (one + r) ** n
    result = numerator / denominator / m
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def modified_duration(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    mac = macaulay_duration(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    r = Decimal(str(ytm)) / Decimal(str(payments_per_year))
    result = mac / (Decimal(1) + r)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def dollar_duration(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    mod_dur = modified_duration(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    n = int(years_to_maturity * payments_per_year)
    r = Decimal(str(ytm)) / Decimal(str(payments_per_year))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    fv = Decimal(str(face_value))
    one = Decimal(1)
    coupon_pmt = c * fv
    price = coupon_pmt * (one - (one + r) ** (-n)) / r + fv / (one + r) ** n
    result = mod_dur * price / Decimal(100)
    if ndigits is not None:
        result = result.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return result


def pvbp(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    pv01 = Decimal(0)
    n = int(years_to_maturity * payments_per_year)
    r = Decimal(str(ytm)) / Decimal(str(payments_per_year))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    fv = Decimal(str(face_value))
    one = Decimal(1)
    coupon_pmt = c * fv
    base_price = coupon_pmt * (one - (one + r) ** (-n)) / r + fv / (one + r) ** n
    shifted_r = r + Decimal(0.0001) / Decimal(payments_per_year)
    shifted_price = coupon_pmt * (one - (one + shifted_r) ** (-n)) / shifted_r + fv / (one + shifted_r) ** n
    pv01 = base_price - shifted_price
    if ndigits is not None:
        pv01 = pv01.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return pv01


def key_rate_duration(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, key_tenor: float, payments_per_year: int = 2) -> Decimal:
    n = int(years_to_maturity * payments_per_year)
    r = Decimal(str(ytm)) / Decimal(str(payments_per_year))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    fv = Decimal(str(face_value))
    one = Decimal(1)
    coupon_pmt = c * fv
    base_price = coupon_pmt * (one - (one + r) ** (-n)) / r + fv / (one + r) ** n
    shift = Decimal('0.0001')
    shifted_r = r + shift
    shifted_price = coupon_pmt * (one - (one + shifted_r) ** (-n)) / shifted_r + fv / (one + shifted_r) ** n
    return (shifted_price - base_price) / base_price / shift * Decimal(key_tenor)


def effective_duration(price_down: Decimal, price_up: Decimal, initial_price: Decimal, yield_change: Decimal) -> Decimal:
    if initial_price == 0:
        raise ValueError("initial_price must be non-zero")
    if yield_change == 0:
        raise ValueError("yield_change must be non-zero")
    return (price_down - price_up) / (Decimal(2) * initial_price * yield_change)
