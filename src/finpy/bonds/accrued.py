"""Accrued-interest helpers — multiple day-count conventions.

Signatures (matching the existing test suite):
    accrued_interest(face, coupon, days_since_last_coupon, days_in_coupon_period=182, *, ndigits)
    accrued_interest_actual_actual(face, coupon, settlement, prev, next, *, ndigits)
    accrued_interest_30_360(face, coupon, settlement, prev, next, *, ndigits)
    accrued_interest_actual_360(face, coupon, settlement, prev, next, *, ndigits)
    accrued_interest_actual_365(face, coupon, settlement, prev, next, *, ndigits)
    accrued_interest_30_360_isda(face, coupon, settlement, prev, next, *, ndigits)
    days_between_dates(d1, d2) -> int
    days_between_coupons(prev, next) -> int
    days_since_last_coupon(settlement, prev) -> int  (note order)
    next_coupon_date(date_str, *, months_per_period=6) -> str
    previous_coupon_date(date_str, *, months_per_period=6) -> str
    is_leap_year(year) -> bool
"""

from decimal import Decimal, ROUND_HALF_UP
import datetime as dt


def _quantize(v, ndigits):
    if ndigits is None:
        return v
    return v.quantize(Decimal(10) ** (-ndigits), rounding=ROUND_HALF_UP)


def _to_date(d):
    if isinstance(d, dt.date):
        return d
    if isinstance(d, str):
        return dt.date.fromisoformat(d)
    raise TypeError(f"cannot convert {type(d)} to date")


def days_between_dates(d1, d2) -> int:
    """Calendar days from d1 to d2 (d2 - d1). Negative if d2 < d1."""
    return (_to_date(d2) - _to_date(d1)).days


def is_leap_year(year: int) -> bool:
    """Standard Gregorian leap-year rule."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def days_between_coupons(prev_coupon, next_coupon) -> int:
    return days_between_dates(prev_coupon, next_coupon)


def days_since_last_coupon(settlement, prev_coupon) -> int:
    """Days from prev_coupon up to settlement; clamps to 0 if settlement is earlier."""
    diff = days_between_dates(prev_coupon, settlement)
    return max(0, diff)


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        next_first = dt.date(year + 1, 1, 1)
    else:
        next_first = dt.date(year, month + 1, 1)
    return (next_first - dt.timedelta(days=1)).day


def _shift_months(d: dt.date, months: int) -> dt.date:
    new_month_index = d.month - 1 + months
    new_year = d.year + new_month_index // 12
    new_month = new_month_index % 12 + 1
    new_day = min(d.day, _last_day_of_month(new_year, new_month))
    return dt.date(new_year, new_month, new_day)


def next_coupon_date(date_str, *, months_per_period: int = 6) -> str:
    """Add months_per_period months and return ISO-formatted date string."""
    d = _to_date(date_str)
    return _shift_months(d, months_per_period).isoformat()


def previous_coupon_date(date_str, *, months_per_period: int = 6) -> str:
    """Subtract months_per_period months and return ISO-formatted date string."""
    d = _to_date(date_str)
    return _shift_months(d, -months_per_period).isoformat()


def accrued_interest(face_value, coupon_rate, days_since, days_in_coupon_period=182, *, ndigits=None) -> Decimal:
    """Linear accrual within coupon period (default semi-annual: 182 days, half a coupon).

    Note the historical convention: a full `days_in_coupon_period` accrues
    `face*coupon/2` (half a coupon's worth of interest). Tests rely on this.
    """
    fv = Decimal(str(face_value))
    c = Decimal(str(coupon_rate))
    d = Decimal(str(days_since))
    period = Decimal(str(days_in_coupon_period))
    accrued = fv * c * d / (period * 2)
    return _quantize(accrued, ndigits)


def accrued_interest_actual_actual(face, coupon, settlement, prev_coupon, next_coupon, *, ndigits=None) -> Decimal:
    """ACT/ACT: days_since/days_in_period * face*coupon (annual coupon basis)."""
    days_since = days_between_dates(prev_coupon, settlement)
    days_in = days_between_dates(prev_coupon, next_coupon)
    if days_in <= 0:
        raise ValueError("invalid coupon period")
    fv = Decimal(str(face))
    c = Decimal(str(coupon))
    full_coupon = fv * c
    accrued = full_coupon * Decimal(days_since) / Decimal(days_in)
    return _quantize(accrued, ndigits)


def _days_30_360(d_from, d_to) -> int:
    """30/360 day count from d_from to d_to (US/NASD convention, simple)."""
    f = _to_date(d_from)
    t = _to_date(d_to)
    f_day = min(f.day, 30)
    t_day = min(t.day, 30) if f_day == 30 else t.day
    return (t.year - f.year) * 360 + (t.month - f.month) * 30 + (t_day - f_day)


def accrued_interest_30_360(face, coupon, settlement, prev_coupon, next_coupon=None, *, ndigits=None) -> Decimal:
    """30/360 day count: each month 30 days, 360-day coupon basis."""
    days_since = _days_30_360(prev_coupon, settlement)
    fv = Decimal(str(face))
    c = Decimal(str(coupon))
    full_coupon = fv * c
    accrued = full_coupon * Decimal(days_since) / Decimal(360)
    return _quantize(accrued, ndigits)


def accrued_interest_actual_360(face, coupon, settlement, prev_coupon, next_coupon=None, *, ndigits=None) -> Decimal:
    """ACT/360: actual days, 360-day year."""
    days = days_between_dates(prev_coupon, settlement)
    fv = Decimal(str(face))
    c = Decimal(str(coupon))
    accrued = fv * c * Decimal(days) / Decimal(360)
    return _quantize(accrued, ndigits)


def accrued_interest_actual_365(face, coupon, settlement, prev_coupon, next_coupon=None, *, ndigits=None) -> Decimal:
    """ACT/365: actual days, 365-day year."""
    days = days_between_dates(prev_coupon, settlement)
    fv = Decimal(str(face))
    c = Decimal(str(coupon))
    accrued = fv * c * Decimal(days) / Decimal(365)
    return _quantize(accrued, ndigits)


def accrued_interest_30_360_isda(face, coupon, settlement, prev_coupon, next_coupon=None, *, ndigits=None) -> Decimal:
    """ISDA variant of 30/360 — symmetric end-of-month adjustment."""
    p = _to_date(prev_coupon)
    s = _to_date(settlement)
    p_day = p.day
    s_day = s.day
    if p_day == 31:
        p_day = 30
    if s_day == 31 and p_day == 30:
        s_day = 30
    days_since = (s.year - p.year) * 360 + (s.month - p.month) * 30 + (s_day - p_day)
    fv = Decimal(str(face))
    c = Decimal(str(coupon))
    full_coupon = fv * c / 2
    accrued = full_coupon * Decimal(days_since) / Decimal(180)
    return _quantize(accrued, ndigits)
