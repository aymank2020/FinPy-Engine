from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from finpy.bonds.clean_price import clean_price
from finpy.bonds.accrued import accrued_interest


def dirty_price(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, *, ndigits: Optional[int] = None) -> Decimal:
    cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, 182)
    dp = cp + ai
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def full_price(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, *, ndigits: Optional[int] = None) -> Decimal:
    return dirty_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year, days_since_last_coupon, ndigits=ndigits)


def dirty_price_ex_dividend(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, days_ex_dividend: int = 7, *, ndigits: Optional[int] = None) -> Decimal:
    cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    days_in_period = 182
    ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, days_in_period)
    if days_since_last_coupon > days_in_period - days_ex_dividend:
        ai = Decimal(0)
    dp = cp + ai
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_short_coupon(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, days_in_short_period: int = 91, *, ndigits: Optional[int] = None) -> Decimal:
    from finpy.bonds.clean_price import clean_price_fractional_period
    ratio = Decimal(str(days_since_last_coupon)) / Decimal(str(days_in_short_period))
    cp = clean_price_fractional_period(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year, float(ratio))
    ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, days_in_short_period)
    dp = cp + ai
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_long_first_coupon(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_accrued: int = 0, days_in_long_period: int = 364, *, ndigits: Optional[int] = None) -> Decimal:
    from finpy.bonds.clean_price import clean_price_odd_first_period
    normal_period = 182
    cp = clean_price_odd_first_period(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year, days_in_long_period, normal_period)
    ai = accrued_interest(face_value, coupon_rate, days_accrued, normal_period)
    dp = cp + ai
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_from_clean(clean_price_value: float, accrued_interest_value: float, *, ndigits: Optional[int] = None) -> Decimal:
    dp = Decimal(str(clean_price_value)) + Decimal(str(accrued_interest_value))
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_at_maturity(face_value: float, coupon_rate: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    fv = Decimal(str(face_value))
    c = Decimal(str(coupon_rate)) / Decimal(str(payments_per_year))
    dp = fv + c * fv
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_on_coupon_date(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    dp = cp
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_between_payment_dates(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, days_in_period: int = 182, *, ndigits: Optional[int] = None) -> Decimal:
    if days_since_last_coupon == 0:
        dp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    else:
        cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
        ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, days_in_period)
        dp = cp + ai
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_with_indexation(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, index_ratio: float = 1.0, *, ndigits: Optional[int] = None) -> Decimal:
    cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, 182)
    ir = Decimal(str(index_ratio))
    dp = (cp + ai) * ir
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_zero_coupon(face_value: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, *, ndigits: Optional[int] = None) -> Decimal:
    from finpy.bonds.clean_price import clean_price_zero_coupon
    dp = clean_price_zero_coupon(face_value, ytm, years_to_maturity, payments_per_year)
    if ndigits is not None:
        dp = dp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return dp


def dirty_price_to_clean_price(dirty_price_value: float, accrued_interest_value: float, *, ndigits: Optional[int] = None) -> Decimal:
    cp = Decimal(str(dirty_price_value)) - Decimal(str(accrued_interest_value))
    if ndigits is not None:
        cp = cp.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return cp


def dirty_price_validate(face_value: float, coupon_rate: float, ytm: float, years_to_maturity: float, payments_per_year: int = 2, days_since_last_coupon: int = 0, *, ndigits: Optional[int] = None) -> dict[str, Decimal]:
    cp = clean_price(face_value, coupon_rate, ytm, years_to_maturity, payments_per_year)
    ai = accrued_interest(face_value, coupon_rate, days_since_last_coupon, 182)
    dp = cp + ai
    result = {
        "clean_price": cp,
        "accrued_interest": ai,
        "dirty_price": dp,
    }
    if ndigits is not None:
        result = {k: v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP) for k, v in result.items()}
    return result


def dirty_price_from_yield_change(base_dirty_price: float, modified_duration_val: float, convexity_val: float, yield_change: float, *, ndigits: Optional[int] = None) -> Decimal:
    p0 = Decimal(str(base_dirty_price))
    dur = Decimal(str(modified_duration_val))
    conv = Decimal(str(convexity_val))
    dy = Decimal(str(yield_change))
    price_change = -dur * dy * p0 + Decimal(0.5) * conv * (dy ** 2) * p0
    new_price = p0 + price_change
    if ndigits is not None:
        new_price = new_price.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)
    return new_price
