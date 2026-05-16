from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.dirty_price import dirty_price, full_price
from finpy.bonds.dirty_price import dirty_price_ex_dividend, dirty_price_short_coupon
from finpy.bonds.dirty_price import dirty_price_long_first_coupon, dirty_price_from_clean
from finpy.bonds.dirty_price import dirty_price_at_maturity, dirty_price_on_coupon_date
from finpy.bonds.dirty_price import dirty_price_between_payment_dates
from finpy.bonds.dirty_price import dirty_price_with_indexation, dirty_price_zero_coupon
from finpy.bonds.dirty_price import dirty_price_to_clean_price, dirty_price_validate
from finpy.bonds.dirty_price import dirty_price_from_yield_change
from finpy.bonds.clean_price import clean_price, clean_price_zero_coupon
from finpy.bonds.accrued import accrued_interest
from finpy.bonds.duration import modified_duration
from finpy.bonds.convexity import convexity
from tests._helpers import approx_decimal


class TestDirtyPrice:
    def test_basic(self):
        result = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=91)
        assert result > 0

    def test_zero_days_accrued(self):
        result = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=0)
        cp = clean_price(1000, 0.05, 0.05, 5)
        assert result == cp

    def test_full_period_accrued(self):
        result = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=182)
        assert result > 0

    def test_high_ytm(self):
        result = dirty_price(1000, 0.05, 0.15, 5, days_since_last_coupon=91)
        assert result > 0

    def test_ndigits(self):
        result = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=91, ndigits=0)
        assert isinstance(result, Decimal)

    def test_dirty_greater_than_clean(self):
        dp = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        cp = clean_price(1000, 0.05, 0.05, 5)
        assert dp > cp

    def test_dirty_various_ppy(self):
        for ppy in [1, 2, 4]:
            dp = dirty_price(1000, 0.05, 0.05, 5, ppy, 45)
            assert dp > 0


class TestFullPrice:
    def test_equals_dirty_price(self):
        dp = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        fp = full_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        assert dp == fp


class TestDirtyPriceExDividend:
    def test_basic(self):
        result = dirty_price_ex_dividend(1000, 0.05, 0.05, 5, days_since_last_coupon=91)
        assert result > 0

    def test_ex_dividend_period(self):
        result = dirty_price_ex_dividend(1000, 0.05, 0.05, 5, days_since_last_coupon=178, days_ex_dividend=7)
        cp = clean_price(1000, 0.05, 0.05, 5)
        assert result == cp

    def test_not_ex_dividend(self):
        result = dirty_price_ex_dividend(1000, 0.05, 0.05, 5, days_since_last_coupon=90, days_ex_dividend=7)
        cp = clean_price(1000, 0.05, 0.05, 5)
        ai = accrued_interest(1000, 0.05, 90)
        assert result == pytest.approx(cp + ai, abs=0.01)

    def test_ndigits(self):
        result = dirty_price_ex_dividend(1000, 0.05, 0.05, 5, days_since_last_coupon=91, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceShortCoupon:
    def test_basic(self):
        result = dirty_price_short_coupon(1000, 0.05, 0.05, 5, days_since_last_coupon=30, days_in_short_period=91)
        assert result > 0

    def test_ndigits(self):
        result = dirty_price_short_coupon(1000, 0.05, 0.05, 5, days_since_last_coupon=30, days_in_short_period=91, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceLongFirstCoupon:
    def test_basic(self):
        result = dirty_price_long_first_coupon(1000, 0.05, 0.05, 5, days_accrued=30, days_in_long_period=364)
        assert result > 0

    def test_ndigits(self):
        result = dirty_price_long_first_coupon(1000, 0.05, 0.05, 5, days_accrued=30, days_in_long_period=364, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceFromClean:
    def test_basic(self):
        result = dirty_price_from_clean(950.0, 12.50)
        assert result == Decimal("962.50")

    def test_zero_accrued(self):
        result = dirty_price_from_clean(1000.0, 0.0)
        assert result == Decimal("1000")

    def test_ndigits(self):
        result = dirty_price_from_clean(950.0, 12.50, ndigits=0)
        assert result == Decimal("963")


class TestDirtyPriceAtMaturity:
    def test_basic(self):
        result = dirty_price_at_maturity(1000, 0.05)
        assert result == pytest.approx(Decimal("1025.00"), abs=0.01)

    def test_zero_coupon_at_maturity(self):
        result = dirty_price_at_maturity(1000, 0.0)
        assert result == Decimal("1000")

    def test_ndigits(self):
        result = dirty_price_at_maturity(1000, 0.05, ndigits=0)
        assert result == Decimal("1025")


class TestDirtyPriceOnCouponDate:
    def test_basic(self):
        result = dirty_price_on_coupon_date(1000, 0.05, 0.05, 5)
        cp = clean_price(1000, 0.05, 0.05, 5)
        assert result == cp

    def test_ndigits(self):
        result = dirty_price_on_coupon_date(1000, 0.05, 0.05, 5, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceBetweenPaymentDates:
    def test_zero_days(self):
        result = dirty_price_between_payment_dates(1000, 0.05, 0.05, 5, days_since_last_coupon=0)
        cp = clean_price(1000, 0.05, 0.05, 5)
        assert result == cp

    def test_positive_days(self):
        result = dirty_price_between_payment_dates(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        cp = clean_price(1000, 0.05, 0.05, 5)
        ai = accrued_interest(1000, 0.05, 60)
        assert result == pytest.approx(cp + ai, abs=0.01)

    def test_ndigits(self):
        result = dirty_price_between_payment_dates(1000, 0.05, 0.05, 5, days_since_last_coupon=60, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceWithIndexation:
    def test_basic(self):
        result = dirty_price_with_indexation(1000, 0.05, 0.05, 5, days_since_last_coupon=60, index_ratio=1.05)
        cp = clean_price(1000, 0.05, 0.05, 5)
        ai = accrued_interest(1000, 0.05, 60)
        assert result == pytest.approx((cp + ai) * Decimal("1.05"), abs=0.01)

    def test_unit_index(self):
        result = dirty_price_with_indexation(1000, 0.05, 0.05, 5, days_since_last_coupon=60, index_ratio=1.0)
        dp = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        assert result == pytest.approx(dp, abs=0.01)

    def test_ndigits(self):
        result = dirty_price_with_indexation(1000, 0.05, 0.05, 5, days_since_last_coupon=60, index_ratio=1.02, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceZeroCoupon:
    def test_basic(self):
        result = dirty_price_zero_coupon(1000, 0.05, 5)
        assert result < Decimal("1000")

    def test_zero_ytm(self):
        result = dirty_price_zero_coupon(1000, 0.0, 5)
        assert result == Decimal("1000")

    def test_ndigits(self):
        result = dirty_price_zero_coupon(1000, 0.05, 5, ndigits=0)
        assert isinstance(result, Decimal)


class TestDirtyPriceToCleanPrice:
    def test_basic(self):
        result = dirty_price_to_clean_price(1012.50, 12.50)
        assert result == Decimal("1000")

    def test_zero_accrued(self):
        result = dirty_price_to_clean_price(1000.0, 0.0)
        assert result == Decimal("1000")

    def test_ndigits(self):
        result = dirty_price_to_clean_price(1012.50, 12.50, ndigits=0)
        assert result == Decimal("1000")


class TestDirtyPriceValidate:
    def test_basic(self):
        result = dirty_price_validate(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        assert "clean_price" in result
        assert "accrued_interest" in result
        assert "dirty_price" in result

    def test_relationship(self):
        result = dirty_price_validate(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        assert result["dirty_price"] == result["clean_price"] + result["accrued_interest"]

    def test_ndigits(self):
        result = dirty_price_validate(1000, 0.05, 0.05, 5, days_since_last_coupon=60, ndigits=0)
        assert all(isinstance(v, Decimal) for v in result.values())


class TestDirtyPriceFromYieldChange:
    def test_no_change(self):
        result = dirty_price_from_yield_change(1000.0, 5.0, 50.0, 0.0)
        assert result == Decimal("1000")

    def test_positive_yield_change(self):
        result = dirty_price_from_yield_change(1000.0, 5.0, 50.0, 0.01)
        assert result < 1000

    def test_negative_yield_change(self):
        result = dirty_price_from_yield_change(1000.0, 5.0, 50.0, -0.01)
        assert result > 1000

    def test_ndigits(self):
        result = dirty_price_from_yield_change(1000.0, 5.0, 50.0, 0.01, ndigits=0)
        assert isinstance(result, Decimal)


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10), st.integers(1, 4), st.integers(0, 182))
def test_dirty_equals_clean_plus_accrued(face, coupon, years, ppy, days):
    ytm = coupon
    cp = clean_price(face, coupon, ytm, years, ppy)
    ai = accrued_interest(face, coupon, days)
    dp = dirty_price(face, coupon, ytm, years, ppy, days)
    assert dp == pytest.approx(cp + ai, abs=0.01)


@given(st.floats(0.02, 0.10), st.floats(1, 10))
def test_full_equals_dirty(coupon, years):
    dp = dirty_price(1000, coupon, coupon, years, 2, 60)
    fp = full_price(1000, coupon, coupon, years, 2, 60)
    assert dp == fp


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_non_negative(face, coupon, years):
    result = dirty_price(face, coupon, coupon, years, 2, 60)
    assert result >= 0


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_on_coupon_equals_clean(face, coupon, years):
    result = dirty_price_on_coupon_date(face, coupon, coupon, years)
    cp = clean_price(face, coupon, coupon, years)
    assert result == cp


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_validate_components(face, coupon, years):
    result = dirty_price_validate(face, coupon, coupon, years, 60)
    assert result["dirty_price"] == result["clean_price"] + result["accrued_interest"]


@given(st.floats(1000, 10000), st.floats(0.02, 0.10), st.floats(2, 10))
def test_dirty_price_indexed_gt_non_indexed(face, coupon, years):
    indexed = dirty_price_with_indexation(face, coupon, coupon, years, 2, 60, 1.02)
    plain = dirty_price(face, coupon, coupon, years, 2, 60)
    assert indexed > plain


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_at_maturity_gt_face(face, coupon, years):
    result = dirty_price_at_maturity(face, coupon)
    assert result >= Decimal(str(face))


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10), st.integers(0, 91))
def test_dirty_price_short_coupon_positive(face, coupon, years, days):
    result = dirty_price_short_coupon(face, coupon, coupon, years, 2, days, 91)
    assert result > 0


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_long_first_coupon_positive(face, coupon, years):
    result = dirty_price_long_first_coupon(face, coupon, coupon, years, 30, 364)
    assert result > 0


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_ex_dividend_le_normal(face, coupon, years):
    normal = dirty_price(face, coupon, coupon, years, 2, 150)
    ex_div = dirty_price_ex_dividend(face, coupon, coupon, years, 2, 150)
    assert ex_div <= normal


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_from_clean_positive(face, coupon, years):
    cp = clean_price(face, coupon, coupon, years, 2)
    ai = accrued_interest(face, coupon, 60)
    dp = dirty_price_from_clean(float(cp), float(ai))
    assert dp == pytest.approx(cp + ai, abs=0.001)


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_to_clean_roundtrip(face, coupon, years):
    dp = dirty_price(face, coupon, coupon, years, 2, 60)
    ai = accrued_interest(face, coupon, 60)
    cp_back = dirty_price_to_clean_price(float(dp), float(ai))
    cp = clean_price(face, coupon, coupon, years, 2)
    assert cp_back == pytest.approx(cp, abs=0.01)


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_between_payment_dates_increasing(face, coupon, years):
    d0 = dirty_price_between_payment_dates(face, coupon, coupon, years, 2, 0)
    d60 = dirty_price_between_payment_dates(face, coupon, coupon, years, 2, 60)
    d120 = dirty_price_between_payment_dates(face, coupon, coupon, years, 2, 120)
    assert d0 <= d60 <= d120


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_from_yield_change_direction(face, coupon, years):
    dp = float(dirty_price(face, coupon, coupon, years, 2, 60))
    mod_dur = float(modified_duration(face, coupon, coupon, years, 2))
    conv = float(convexity(face, coupon, coupon, years, 2))
    up = dirty_price_from_yield_change(dp, mod_dur, conv, -0.005)
    down = dirty_price_from_yield_change(dp, mod_dur, conv, 0.005)
    assert up > down


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_zero_coupon_equals_clean(face, ytm, years):
    dp = dirty_price_zero_coupon(face, ytm, years)
    cp = clean_price_zero_coupon(face, ytm, years)
    assert dp == cp


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10), st.integers(0, 182))
def test_full_price_returns_same(face, coupon, years, days):
    dp = dirty_price(face, coupon, coupon, years, 2, days)
    fp = full_price(face, coupon, coupon, years, 2, days)
    assert dp == fp


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_validate_keys(face, coupon, years):
    result = dirty_price_validate(face, coupon, coupon, years, 2, 60)
    assert set(result.keys()) == {"clean_price", "accrued_interest", "dirty_price"}


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 10))
def test_dirty_price_on_coupon_date_no_accrued(face, coupon, years):
    result = dirty_price_on_coupon_date(face, coupon, coupon, years, 2)
    cp = clean_price(face, coupon, coupon, years, 2)
    assert result == cp

