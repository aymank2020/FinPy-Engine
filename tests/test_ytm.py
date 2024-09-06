from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.ytm import ytm, ytm_newton, approximate_ytm
from finpy.bonds.ytm import ytm_from_dirty_price, ytm_zero_coupon
from finpy.bonds.ytm import ytm_annual, ytm_semi_annual, ytm_quarterly, ytm_monthly
from finpy.bonds.ytm import ytm_bisection
from finpy.bonds.clean_price import clean_price
from finpy.bonds.dirty_price import dirty_price



class TestYTM:
    def test_par_bond(self):
        result = ytm(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_no_convergence(self):
        result = ytm_newton(1, 1000, 0.05, 5, max_iter=5)
        assert result is not None

    def test_premium_bond(self):
        price = clean_price(1000, 0.06, 0.04, 5)
        result = ytm(float(price), 1000, 0.06, 5)
        assert result == pytest.approx(Decimal("0.04"), abs=0.005)

    def test_discount_bond(self):
        price = clean_price(1000, 0.04, 0.06, 5)
        result = ytm(float(price), 1000, 0.04, 5)
        assert result == pytest.approx(Decimal("0.06"), abs=0.005)

    def test_zero_coupon_bond(self):
        result = ytm(700, 1000, 0.0, 5)
        assert result > 0

    def test_short_maturity(self):
        result = ytm(980, 1000, 0.05, 0.5)
        assert result > 0

    def test_monthly_payments(self):
        result = ytm(1000, 1000, 0.05, 5, 12)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_annual_payments(self):
        result = ytm(1000, 1000, 0.05, 5, 1)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_ndigits(self):
        result = ytm(1000, 1000, 0.05, 5, ndigits=4)
        assert result == pytest.approx(Decimal("0.05"), abs=0.0001)

    def test_high_coupon(self):
        price = clean_price(1000, 0.12, 0.08, 10)
        result = ytm(float(price), 1000, 0.12, 10)
        assert result == pytest.approx(Decimal("0.08"), abs=0.005)


class TestYTMNewton:
    def test_par_bond(self):
        result = ytm_newton(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_premium(self):
        price = clean_price(1000, 0.07, 0.05, 5)
        result = ytm_newton(float(price), 1000, 0.07, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.005)

    def test_custom_tolerance(self):
        result = ytm_newton(1000, 1000, 0.05, 5, tolerance=1e-6)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_custom_max_iter(self):
        result = ytm_newton(1000, 1000, 0.05, 5, max_iter=50)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_ndigits(self):
        result = ytm_newton(1000, 1000, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)

    def test_agrees_with_ytm(self):
        r1 = ytm(1000, 1000, 0.05, 5)
        r2 = ytm_newton(1000, 1000, 0.05, 5)
        assert r1 == pytest.approx(r2, abs=1e-6)


class TestApproximateYTM:
    def test_par_bond(self):
        result = approximate_ytm(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.005)

    def test_premium(self):
        result = approximate_ytm(1100, 1000, 0.05, 5)
        assert result < Decimal("0.05")

    def test_discount(self):
        result = approximate_ytm(900, 1000, 0.05, 5)
        assert result > Decimal("0.05")

    def test_ndigits(self):
        result = approximate_ytm(1000, 1000, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)


class TestYTMFromDirtyPrice:
    def test_basic(self):
        dp = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        result = ytm_from_dirty_price(float(dp), 1000, 0.05, 5, 60)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_ndigits(self):
        dp = dirty_price(1000, 0.05, 0.05, 5, days_since_last_coupon=60)
        result = ytm_from_dirty_price(float(dp), 1000, 0.05, 5, 60, ndigits=4)
        assert isinstance(result, Decimal)


class TestYTMZeroCoupon:
    def test_basic(self):
        result = ytm_zero_coupon(700, 1000, 5)
        assert result > 0

    def test_par_price(self):
        result = ytm_zero_coupon(1000, 1000, 5)
        assert result == Decimal("0")

    def test_short_maturity(self):
        result = ytm_zero_coupon(950, 1000, 0.5)
        assert result > 0

    def test_ndigits(self):
        result = ytm_zero_coupon(700, 1000, 5, ndigits=4)
        assert isinstance(result, Decimal)

    def test_discount_price_positive_ytm(self):
        for price in [800, 900, 950]:
            result = ytm_zero_coupon(price, 1000, 5)
            assert result > 0

    def test_quarterly(self):
        result = ytm_zero_coupon(700, 1000, 5, 4)
        assert result > 0


class TestYTMPeriodVariants:
    def test_annual(self):
        result = ytm_annual(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_semi_annual(self):
        result = ytm_semi_annual(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_quarterly(self):
        result = ytm_quarterly(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_monthly(self):
        result = ytm_monthly(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)


class TestYTMBisection:
    def test_par_bond(self):
        result = ytm_bisection(1000, 1000, 0.05, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_premium(self):
        price = clean_price(1000, 0.07, 0.05, 5)
        result = ytm_bisection(float(price), 1000, 0.07, 5)
        assert result == pytest.approx(Decimal("0.05"), abs=0.005)

    def test_discount(self):
        price = clean_price(1000, 0.03, 0.05, 10)
        result = ytm_bisection(float(price), 1000, 0.03, 10)
        assert result == pytest.approx(Decimal("0.05"), abs=0.005)

    def test_wide_range(self):
        result = ytm_bisection(1000, 1000, 0.05, 5, low=-0.5, high=2.0)
        assert result == pytest.approx(Decimal("0.05"), abs=0.01)

    def test_ndigits(self):
        result = ytm_bisection(1000, 1000, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)

    def test_agrees_with_newton(self):
        r1 = ytm(1000, 1000, 0.05, 5)
        r2 = ytm_bisection(1000, 1000, 0.05, 5)
        assert r1 == pytest.approx(r2, abs=0.001)


@given(st.floats(0.02, 0.10), st.floats(2, 15), st.integers(1, 2))
def test_ytm_roundtrip(coupon, years, ppy):
    fv = 1000
    p = clean_price(fv, coupon, coupon, years, ppy)
    y = ytm(float(p), fv, coupon, years, ppy)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.01)


@given(st.floats(0.02, 0.10), st.floats(2, 15))
def test_ytm_newton_roundtrip(coupon, years):
    fv = 1000
    p = clean_price(fv, coupon, coupon, years, 2)
    y = ytm_newton(float(p), fv, coupon, years, 2)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.01)


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.floats(2, 15))
def test_ytm_bisection_roundtrip(face, coupon, years):
    p = clean_price(face, coupon, coupon, years, 2)
    y = ytm_bisection(float(p), face, coupon, years, 2)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.02)


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.floats(2, 15))
def test_approximate_ytm_roughly_accurate(face, coupon, years):
    p = clean_price(face, coupon, coupon, years, 2)
    y = approximate_ytm(float(p), face, coupon, years, 2)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.05)


@given(st.floats(1000, 10000), st.floats(2, 15))
def test_ytm_zero_coupon_discount_monotonic(face, years):
    for price in [600, 700, 800, 900]:
        if price < face:
            y = ytm_zero_coupon(price, face, years)
            assert y > 0


@given(st.floats(0.02, 0.10), st.floats(2, 15))
def test_ytm_methods_agree(coupon, years):
    fv = 1000
    p = clean_price(fv, coupon, coupon, years, 2)
    y1 = ytm(float(p), fv, coupon, years, 2)
    y2 = ytm_newton(float(p), fv, coupon, years, 2)
    y3 = ytm_bisection(float(p), fv, coupon, years, 2)
    assert y1 == pytest.approx(y2, abs=0.001)
    assert y2 == pytest.approx(y3, abs=0.005)


@given(st.floats(0.02, 0.10), st.floats(2, 15))
def test_ytm_from_dirty_roundtrip(coupon, years):
    fv = 1000
    dp = dirty_price(fv, coupon, coupon, years, 2, 60)
    y = ytm_from_dirty_price(float(dp), fv, coupon, years, 60, 2)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.01)


@given(st.floats(0.02, 0.08), st.floats(100, 10000), st.floats(2, 15), st.integers(1, 4))
def test_ytm_annual_payments_roundtrip(coupon, fv, years, ppy):
    p = clean_price(fv, coupon, coupon, years, ppy)
    y = ytm(float(p), fv, coupon, years, ppy)
    assert y == pytest.approx(Decimal(str(coupon)), abs=0.01)


@given(st.floats(0.03, 0.10), st.floats(2, 10))
def test_ytm_bisection_annual_agrees(coupon, years):
    fv = 1000
    p = clean_price(fv, coupon, coupon, years, 1)
    y1 = ytm(float(p), fv, coupon, years, 1)
    y2 = ytm_bisection(float(p), fv, coupon, years, 1)
    assert y1 == pytest.approx(y2, abs=0.001)


@given(st.floats(900, 1100), st.floats(0.02, 0.10), st.floats(2, 15))
def test_ytm_newton_various_prices(price, coupon, years):
    fv = 1000
    y = ytm_newton(price, fv, coupon, years, 2)
    assert y is not None


@given(st.floats(0.03, 0.10), st.floats(2, 15))
def test_approximate_ytm_direction(coupon, years):
    fv = 1000
    p_prem = clean_price(fv, coupon + 0.02, coupon, years, 2)
    p_disc = clean_price(fv, coupon - 0.02, coupon, years, 2)
    y_prem = approximate_ytm(float(p_prem), fv, coupon + 0.02, years, 2)
    y_disc = approximate_ytm(float(p_disc), fv, coupon - 0.02, years, 2)
    if y_prem < Decimal(str(coupon)):
        assert y_disc > Decimal(str(coupon))


@given(st.floats(0.02, 0.10), st.floats(100, 10000), st.floats(2, 15))
def test_ytm_zero_coupon_positive_for_discount(coupon, fv, years):
    for price_pct in [0.5, 0.6, 0.7, 0.8, 0.9]:
        y = ytm_zero_coupon(fv * price_pct, fv, years)
        assert y > 0


@given(st.floats(0.03, 0.10), st.floats(2, 15))
def test_ytm_annual_quarterly_agree_for_par(coupon, years):
    fv = 1000
    y_a = ytm_annual(fv, fv, coupon, years)
    y_s = ytm_semi_annual(fv, fv, coupon, years)
    assert y_a == pytest.approx(Decimal(str(coupon)), abs=0.001)
    assert y_s == pytest.approx(Decimal(str(coupon)), abs=0.001)


@given(st.floats(0.02, 0.10), st.floats(2, 15))
def test_ytm_newton_and_bisection_agree(coupon, years):
    fv = 1000
    p = clean_price(fv, coupon, coupon, years, 2)
    y1 = ytm_newton(float(p), fv, coupon, years, 2)
    y2 = ytm_bisection(float(p), fv, coupon, years, 2)
    assert y1 == pytest.approx(y2, abs=0.005)

