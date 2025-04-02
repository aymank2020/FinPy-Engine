from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.clean_price import clean_price, clean_price_from_ytm_bootstrap
from finpy.bonds.clean_price import clean_price_from_discount_factors
from finpy.bonds.clean_price import clean_price_zero_coupon, clean_price_perpetuity
from finpy.bonds.clean_price import clean_price_fractional_period
from finpy.bonds.clean_price import clean_price_odd_first_period, price_yield_relationship


class TestCleanPrice:
    def test_par_bond(self):
        result = clean_price(1000, 0.05, 0.05, 5)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_premium_bond(self):
        result = clean_price(1000, 0.06, 0.04, 5)
        assert result > Decimal("1000")

    def test_discount_bond(self):
        result = clean_price(1000, 0.04, 0.06, 5)
        assert result < Decimal("1000")

    def test_zero_years(self):
        result = clean_price(1000, 0.05, 0.05, 0)
        assert result == Decimal("1000")

    def test_zero_coupon_par(self):
        result = clean_price(1000, 0.0, 0.05, 5)
        assert result < Decimal("1000")

    def test_annual_payments(self):
        result = clean_price(1000, 0.05, 0.05, 5, 1)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_quarterly_payments(self):
        result = clean_price(1000, 0.05, 0.05, 5, 4)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_monthly_payments(self):
        result = clean_price(1000, 0.05, 0.05, 5, 12)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_ndigits_rounding(self):
        result = clean_price(1000, 0.05, 0.05, 5, ndigits=0)
        assert result == Decimal("1000")

    def test_large_face_value(self):
        result = clean_price(10_000_000, 0.04, 0.05, 30)
        assert result > 0

    def test_high_ytm(self):
        result = clean_price(1000, 0.05, 0.50, 5)
        assert result < Decimal("500")

    def test_very_short_maturity(self):
        result = clean_price(1000, 0.05, 0.05, 0.5)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_non_annual_ppy_par(self):
        for ppy in [1, 2, 4, 12]:
            result = clean_price(1000, 0.06, 0.06, 5, ppy)
            assert result == pytest.approx(Decimal("1000.00"), abs=0.02)


class TestCleanPriceFromYtmBootstrap:
    def test_basic(self):
        result = clean_price_from_ytm_bootstrap(1000, 0.05, [0.04, 0.045, 0.05, 0.055, 0.06], 5)
        assert result > 0

    def test_flat_curve(self):
        rates = [0.05] * 10
        result = clean_price_from_ytm_bootstrap(1000, 0.05, rates, 5)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.10)

    def test_empty_rates_list(self):
        result = clean_price_from_ytm_bootstrap(1000, 0.05, [], 5)
        assert result > 0

    def test_single_rate(self):
        result = clean_price_from_ytm_bootstrap(1000, 0.05, [0.05], 5)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.10)

    def test_ndigits(self):
        rates = [0.05] * 10
        result = clean_price_from_ytm_bootstrap(1000, 0.05, rates, 5, ndigits=0)
        assert result == Decimal("1000")


class TestPriceYieldRelationship:
    def test_returns_list(self):
        result = price_yield_relationship(1000, 0.05, [0.03, 0.05, 0.07], 5)
        assert len(result) == 3

    def test_decreasing_prices(self):
        result = price_yield_relationship(1000, 0.05, [0.03, 0.05, 0.07], 5)
        assert result[0]["price"] > result[1]["price"] > result[2]["price"]

    def test_par_at_coupon(self):
        result = price_yield_relationship(1000, 0.05, [0.05], 5)
        assert result[0]["price"] == pytest.approx(Decimal("1000"), abs=0.01)

    def test_ndigits(self):
        result = price_yield_relationship(1000, 0.05, [0.03], 5, ndigits=0)
        assert isinstance(result[0]["price"], Decimal)

    def test_single_yield(self):
        result = price_yield_relationship(1000, 0.05, [0.04], 5)
        assert len(result) == 1


class TestCleanPriceFromDiscountFactors:
    def test_basic(self):
        dfs = [0.98, 0.96, 0.94, 0.92, 0.90, 0.88, 0.86, 0.84, 0.82, 0.80]
        result = clean_price_from_discount_factors(1000, 0.05, dfs, 2)
        assert result > 0

    def test_all_ones(self):
        dfs = [1.0] * 10
        result = clean_price_from_discount_factors(1000, 0.05, dfs, 2)
        assert result == pytest.approx(Decimal("1250.00"), abs=0.01)

    def test_ndigits(self):
        dfs = [0.98, 0.96, 0.94, 0.92, 0.90]
        result = clean_price_from_discount_factors(1000, 0.05, dfs, 2, ndigits=2)
        assert isinstance(result, Decimal)


class TestCleanPriceZeroCoupon:
    def test_discount(self):
        result = clean_price_zero_coupon(1000, 0.05, 5)
        assert result < Decimal("1000")

    def test_zero_ytm(self):
        result = clean_price_zero_coupon(1000, 0.0, 5)
        assert result == Decimal("1000")

    def test_short_maturity(self):
        result = clean_price_zero_coupon(1000, 0.05, 0.5)
        assert result < Decimal("1000")

    def test_positive_price(self):
        result = clean_price_zero_coupon(1000, 0.10, 10)
        assert result < Decimal("1000")
        assert result > 0

    def test_ndigits(self):
        result = clean_price_zero_coupon(1000, 0.05, 5, ndigits=0)
        assert isinstance(result, Decimal)


class TestCleanPricePerpetuity:
    def test_basic(self):
        result = clean_price_perpetuity(25, 0.05, 2)
        assert result == pytest.approx(Decimal("1000"), abs=0.01)

    def test_zero_ytm_infinite(self):
        result = clean_price_perpetuity(25, 0.0, 2)
        assert str(result) == "Infinity"

    def test_ndigits(self):
        result = clean_price_perpetuity(25, 0.05, 2, ndigits=0)
        assert result == Decimal("1000")


class TestCleanPriceFractionalPeriod:
    def test_basic(self):
        result = clean_price_fractional_period(1000, 0.05, 0.05, 5, 2, 0.5)
        assert result > 0

    def test_zero_ratio(self):
        result = clean_price_fractional_period(1000, 0.05, 0.05, 5, 2, 0.0)
        assert result == pytest.approx(Decimal("1025.00"), abs=0.01)

    def test_ndigits(self):
        result = clean_price_fractional_period(1000, 0.05, 0.05, 5, 2, 0.5, ndigits=2)
        assert isinstance(result, Decimal)


class TestCleanPriceOddFirstPeriod:
    def test_basic(self):
        result = clean_price_odd_first_period(1000, 0.05, 0.05, 5, 2, 91, 182)
        assert result > 0

    def test_normal_period(self):
        result = clean_price_odd_first_period(1000, 0.05, 0.05, 5, 2, 182, 182)
        assert result == pytest.approx(Decimal("1000.00"), abs=0.01)

    def test_zero_days_odd(self):
        result = clean_price_odd_first_period(1000, 0.05, 0.05, 5, 2, 0, 182)
        assert result > 0

    def test_ndigits(self):
        result = clean_price_odd_first_period(1000, 0.05, 0.05, 5, 2, 91, 182, ndigits=2)
        assert isinstance(result, Decimal)


@given(st.floats(100, 10000), st.floats(0.01, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_non_negative(face, coupon, years, ppy):
    result = clean_price(face, coupon, coupon, years, ppy)
    assert result > 0


@given(st.floats(0.02, 0.10), st.floats(1, 15))
def test_clean_price_par_when_ytm_equals_coupon(coupon, years):
    result = clean_price(1000, coupon, coupon, years)
    assert result == pytest.approx(Decimal("1000.00"), abs=0.02)


@given(st.floats(0.02, 0.08), st.floats(0.04, 0.12), st.floats(1, 15))
def test_price_yield_inverse(coupon, ytm, years):
    if ytm <= coupon:
        return
    result = clean_price(1000, coupon, ytm, years)
    assert result < Decimal("1000")


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.floats(1, 15))
def test_zero_coupon_less_than_face(face, ytm, years):
    result = clean_price_zero_coupon(face, ytm, years)
    assert result <= Decimal(str(face))


@given(st.floats(1, 10), st.floats(0.02, 0.10), st.integers(1, 4))
def test_perpetuity_finite(coupon, ytm, ppy):
    result = clean_price_perpetuity(coupon * 1000, ytm, ppy)
    assert 0 < result < Decimal("Infinity")


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_decreasing_with_ytm(face, coupon, years, ppy):
    p1 = clean_price(face, coupon, 0.04, years, ppy)
    p2 = clean_price(face, coupon, 0.06, years, ppy)
    p3 = clean_price(face, coupon, 0.08, years, ppy)
    assert p1 > p2 > p3


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(0.02, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_monotonic_yield(face, coupon, ytm, years, ppy):
    p = clean_price(face, coupon, ytm, years, ppy)
    p_up = clean_price(face, coupon, ytm + 0.005, years, ppy)
    p_down = clean_price(face, coupon, max(0.001, ytm - 0.005), years, ppy)
    assert p_down >= p >= p_up


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_from_ytm_bootstrap_flat(face, coupon, years, ppy):
    n = int(years * ppy)
    rates = [coupon] * n
    result = clean_price_from_ytm_bootstrap(face, coupon, rates, years, ppy)
    direct = clean_price(face, coupon, coupon, years, ppy)
    assert result == pytest.approx(direct, abs=0.10)


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_from_discount_factors_matches(face, coupon, years, ppy):
    n = int(years * ppy)
    r = Decimal(str(coupon)) / Decimal(str(ppy))
    one = Decimal(1)
    dfs = [float(one / (one + r) ** Decimal(t + 1)) for t in range(n)]
    result = clean_price_from_discount_factors(face, coupon, dfs, ppy)
    direct = clean_price(face, coupon, coupon, years, ppy)
    assert result == pytest.approx(direct, abs=0.10)


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15))
def test_clean_price_zero_coupon_discount(face, ytm, years):
    result = clean_price_zero_coupon(face, ytm, years)
    assert result <= Decimal(str(face))
    assert result > 0


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15), st.integers(1, 4))
def test_clean_price_ndigits_rounds_down(face, coupon, years, ppy):
    result = clean_price(face, coupon, coupon, years, ppy, ndigits=0)
    assert isinstance(result, Decimal)
    assert result == result.to_integral_value()


@given(st.floats(100, 10000), st.floats(0.04, 0.10), st.floats(0.5, 5))
def test_clean_price_short_maturity_discount(face, coupon, years):
    p_high = clean_price(face, coupon, coupon + 0.02, years)
    p_low = clean_price(face, coupon, max(coupon - 0.02, 0.001), years)
    assert p_low > Decimal(str(face))
    assert p_high < Decimal(str(face))


@given(st.lists(st.floats(0.03, 0.07), min_size=2, max_size=10), st.floats(1, 10))
def test_price_yield_relationship_monotonic(rates, years):
    rates = sorted(rates)
    result = price_yield_relationship(1000, 0.05, rates, years)
    prices = [r["price"] for r in result]
    for i in range(1, len(prices)):
        assert prices[i] <= prices[i - 1]


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15))
def test_clean_price_odd_first_period_less_than_normal(face, coupon, years):
    odd = clean_price_odd_first_period(face, coupon, coupon, years, 2, 91, 182)
    normal = clean_price(face, coupon, coupon, years, 2)
    assert odd > 0
    assert normal > 0


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(1, 15))
def test_clean_price_fractional_period_increasing_ratio(face, coupon, years):
    r1 = clean_price_fractional_period(face, coupon, coupon, years, 2, 0.0)
    r2 = clean_price_fractional_period(face, coupon, coupon, years, 2, 0.5)
    assert r1 != r2

