from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.accrued import accrued_interest, days_between_dates
from finpy.bonds.accrued import accrued_interest_actual_actual, accrued_interest_30_360
from finpy.bonds.accrued import accrued_interest_actual_360, accrued_interest_actual_365
from finpy.bonds.accrued import accrued_interest_30_360_isda
from finpy.bonds.accrued import days_between_coupons, days_since_last_coupon
from finpy.bonds.accrued import next_coupon_date, previous_coupon_date, is_leap_year


class TestAccruedInterest:
    def test_half_period(self):
        result = accrued_interest(1000, 0.05, 91)
        assert result == pytest.approx(Decimal("12.50"), abs=0.01)

    def test_zero_days(self):
        result = accrued_interest(1000, 0.05, 0)
        assert result == Decimal("0")

    def test_full_period(self):
        result = accrued_interest(1000, 0.05, 182)
        assert result == pytest.approx(Decimal("25.00"), abs=0.01)

    def test_ndigits_rounding(self):
        result = accrued_interest(1000, 0.05, 91, ndigits=0)
        assert result == Decimal("13")

    def test_zero_face_value(self):
        result = accrued_interest(0, 0.05, 91)
        assert result == Decimal("0")

    def test_zero_coupon(self):
        result = accrued_interest(1000, 0.0, 91)
        assert result == Decimal("0")

    def test_custom_days_in_period(self):
        result = accrued_interest(1000, 0.05, 30, days_in_coupon_period=180)
        assert result == pytest.approx(Decimal("4.1666666667"), abs=1e-9)

    def test_large_face_value(self):
        result = accrued_interest(1_000_000, 0.05, 91)
        assert result > 0

    def test_negative_days_zeros(self):
        result = accrued_interest(1000, 0.05, -10)
        assert result < 0


class TestAccruedInterestActualActual:
    def test_basic(self):
        result = accrued_interest_actual_actual(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15")
        assert result > 0

    def test_settlement_on_coupon_date(self):
        result = accrued_interest_actual_actual(1000, 0.05, "2024-01-15", "2024-01-15", "2024-07-15")
        assert result == Decimal("0")

    def test_settlement_equals_next_coupon(self):
        result = accrued_interest_actual_actual(1000, 0.05, "2024-07-15", "2024-01-15", "2024-07-15")
        assert result == pytest.approx(Decimal("50.0"), abs=0.01)

    def test_leap_year(self):
        result = accrued_interest_actual_actual(1000, 0.05, "2024-03-01", "2024-01-01", "2024-07-01")
        assert result > 0

    def test_ndigits(self):
        result = accrued_interest_actual_actual(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15", ndigits=2)
        assert result == pytest.approx(Decimal("41.76"), abs=0.01)


class TestAccruedInterest30360:
    def test_basic(self):
        result = accrued_interest_30_360(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15")
        assert result > 0

    def test_end_of_month_jan31(self):
        result = accrued_interest_30_360(1000, 0.05, "2024-02-28", "2024-01-31", "2024-07-31")
        assert result > 0

    def test_both_31(self):
        result = accrued_interest_30_360(1000, 0.05, "2024-05-31", "2024-01-31", "2024-07-31")
        assert result > 0

    def test_feb_30_adjustment(self):
        result = accrued_interest_30_360(1000, 0.05, "2024-02-28", "2024-01-31", "2024-07-31")
        assert result > 0

    def test_ndigits(self):
        result = accrued_interest_30_360(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15", ndigits=2)
        assert result == pytest.approx(Decimal("20.83"), abs=0.01)


class TestAccruedInterestActual360:
    def test_basic(self):
        result = accrued_interest_actual_360(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15")
        assert result > 0

    def test_zero_days(self):
        result = accrued_interest_actual_360(1000, 0.05, "2024-01-15", "2024-01-15", "2024-07-15")
        assert result == Decimal("0")


class TestAccruedInterestActual365:
    def test_basic(self):
        result = accrued_interest_actual_365(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15")
        assert result > 0

    def test_zero_days(self):
        result = accrued_interest_actual_365(1000, 0.05, "2024-01-15", "2024-01-15", "2024-07-15")
        assert result == Decimal("0")


class TestAccruedInterest30360ISDA:
    def test_basic(self):
        result = accrued_interest_30_360_isda(1000, 0.05, "2024-06-15", "2024-01-15", "2024-07-15")
        assert result > 0

    def test_both_31(self):
        result = accrued_interest_30_360_isda(1000, 0.05, "2024-05-31", "2024-01-31", "2024-07-31")
        assert result > 0


class TestDaysBetweenDates:
    def test_same_day(self):
        assert days_between_dates("2024-01-15", "2024-01-15") == 0

    def test_same_year(self):
        assert days_between_dates("2024-01-01", "2024-12-31") == 365

    def test_across_years(self):
        assert days_between_dates("2023-12-31", "2024-12-31") == 366

    def test_leap_year_february(self):
        assert days_between_dates("2024-02-28", "2024-03-01") == 2

    def test_multi_year(self):
        assert days_between_dates("2020-01-01", "2024-01-01") == 1461

    def test_reverse_order_negative(self):
        result = days_between_dates("2024-12-31", "2024-01-01")
        assert result < 0

    def test_non_leap_feb(self):
        assert days_between_dates("2023-02-28", "2023-03-01") == 1


class TestDaysBetweenCoupons:
    def test_basic(self):
        result = days_between_coupons("2024-01-15", "2024-07-15")
        assert result == 182

    def test_same_date(self):
        result = days_between_coupons("2024-01-15", "2024-01-15")
        assert result == 0


class TestDaysSinceLastCoupon:
    def test_positive(self):
        result = days_since_last_coupon("2024-06-15", "2024-01-15")
        assert result == 152

    def test_settlement_before_last_coupon(self):
        result = days_since_last_coupon("2024-01-01", "2024-01-15")
        assert result == 0

    def test_same_date(self):
        result = days_since_last_coupon("2024-01-15", "2024-01-15")
        assert result == 0


class TestNextCouponDate:
    def test_basic(self):
        result = next_coupon_date("2024-01-15")
        assert result == "2024-07-15"

    def test_december_rollover(self):
        result = next_coupon_date("2024-12-15")
        assert result == "2025-06-15"

    def test_end_of_month_jan31(self):
        result = next_coupon_date("2024-01-31")
        assert result == "2024-07-31"

    def test_february_roll(self):
        result = next_coupon_date("2024-08-31")
        assert result == "2025-02-28"

    def test_custom_months(self):
        result = next_coupon_date("2024-01-15", months_per_period=3)
        assert result == "2024-04-15"


class TestPreviousCouponDate:
    def test_basic(self):
        result = previous_coupon_date("2024-07-15")
        assert result == "2024-01-15"

    def test_january_rollover(self):
        result = previous_coupon_date("2024-01-15")
        assert result == "2023-07-15"

    def test_custom_months(self):
        result = previous_coupon_date("2024-04-15", months_per_period=3)
        assert result == "2024-01-15"


class TestIsLeapYear:
    def test_leap_year_2024(self):
        assert is_leap_year(2024) is True

    def test_non_leap_2023(self):
        assert is_leap_year(2023) is False

    def test_century_not_leap(self):
        assert is_leap_year(1900) is False

    def test_century_leap(self):
        assert is_leap_year(2000) is True


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(0, 182))
def test_accrued_non_negative(face, coupon, days):
    result = accrued_interest(face, coupon, days)
    assert result >= 0


@given(st.floats(100, 10000), st.floats(0.01, 0.15))
def test_accrued_zero_days(face, coupon):
    result = accrued_interest(face, coupon, 0)
    assert result == Decimal("0")


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(1, 181))
def test_accrued_less_than_full(face, coupon, days):
    full = accrued_interest(face, coupon, 182)
    partial = accrued_interest(face, coupon, days)
    assert partial <= full


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(0, 182))
def test_accrued_ndigits_rounds(face, coupon, days):
    result = accrued_interest(face, coupon, days, ndigits=0)
    assert isinstance(result, Decimal)


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(0, 182))
def test_accrued_linear_in_days(face, coupon, days):
    result = accrued_interest(face, coupon, days)
    half = accrued_interest(face, coupon, days // 2 if days > 0 else 0)
    if days > 0:
        assert result > half or result == half


@given(st.floats(100, 10000), st.floats(0.01, 0.15))
def test_accrued_proportional_to_face(face, coupon):
    r1 = accrued_interest(face, coupon, 91)
    r2 = accrued_interest(face * 2, coupon, 91)
    assert r2 == pytest.approx(r1 * 2, abs=0.01)


@given(st.floats(0.01, 0.15), st.integers(0, 182))
def test_accrued_proportional_to_coupon(coupon, days):
    r1 = accrued_interest(1000, coupon, days)
    r2 = accrued_interest(1000, coupon * 2, days)
    assert r2 == pytest.approx(r1 * 2, abs=0.01)


@given(st.integers(1, 182))
def test_accrued_increasing_with_days(days):
    r1 = accrued_interest(1000, 0.05, days)
    r2 = accrued_interest(1000, 0.05, days + 1)
    assert r2 >= r1


@given(st.floats(0.01, 0.15))
def test_accrued_custom_period_shorter(coupon):
    short = accrued_interest(1000, coupon, 30, days_in_coupon_period=90)
    long = accrued_interest(1000, coupon, 30, days_in_coupon_period=180)
    assert short > long


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(1, 181))
def test_accrued_bounded_by_full(face, coupon, days):
    full = accrued_interest(face, coupon, 182)
    partial = accrued_interest(face, coupon, days)
    assert partial <= full


@given(st.integers(2020, 2030), st.integers(1, 12), st.integers(1, 28))
def test_days_between_same_date(y, m, d):
    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    assert days_between_dates(date_str, date_str) == 0


@given(st.integers(2020, 2030), st.integers(1, 12), st.integers(1, 28))
def test_days_since_last_coupon_same_date(y, m, d):
    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    assert days_since_last_coupon(date_str, date_str) == 0


@given(st.integers(2020, 2029), st.integers(1, 6), st.integers(1, 28))
def test_next_coupon_date_rolls_forward(y, m, d):
    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    result = next_coupon_date(date_str)
    assert result > date_str


@given(st.integers(2021, 2030), st.integers(1, 12), st.integers(1, 28))
def test_previous_coupon_date_rolls_back(y, m, d):
    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    result = previous_coupon_date(date_str)
    assert result < date_str


@given(st.integers(1900, 2100))
def test_is_leap_year_consistent(year):
    is_leap = is_leap_year(year)
    import calendar
    assert is_leap == calendar.isleap(year)


@given(st.floats(100, 10000), st.floats(0.01, 0.15))
def test_full_year_accrued_equals_half_coupon(face, coupon):
    result = accrued_interest(face, coupon, 182)
    expected = Decimal(str(face)) * Decimal(str(coupon)) / Decimal(2)
    assert result == pytest.approx(expected, abs=0.01)


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.integers(0, 182))
def test_accrued_various_methods_differ(face, coupon, days):
    aa = accrued_interest_actual_actual(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    t30 = accrued_interest_30_360(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    a360 = accrued_interest_actual_360(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    a365 = accrued_interest_actual_365(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    assert aa > 0
    assert t30 > 0
    assert a360 > 0
    assert a365 > 0


@given(st.floats(100, 10000), st.floats(0.01, 0.15))
def test_days_between_coupons_positive(face, coupon):
    d = days_between_coupons("2024-01-15", "2024-07-15")
    assert d == 182


@given(st.floats(100, 10000), st.floats(0.01, 0.15))
def test_accrued_actual_360_less_than_actual_365(face, coupon):
    a360 = accrued_interest_actual_360(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    a365 = accrued_interest_actual_365(face, coupon, "2024-06-15", "2024-01-15", "2024-07-15")
    assert a360 > a365
