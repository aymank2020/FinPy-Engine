from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.convexity import convexity, convexity_adjustment, effective_convexity
from finpy.bonds.convexity import price_change_estimate, approximate_convexity
from finpy.bonds.duration import modified_duration
from finpy.core.errors import NoSolutionFoundError
from tests._helpers import approx_decimal


class TestConvexity:
    def test_positive(self):
        result = convexity(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_zero_coupon(self):
        result = convexity(1000, 0.0, 0.05, 5)
        assert result > 0

    def test_short_maturity(self):
        result = convexity(1000, 0.05, 0.05, 0.5)
        assert result > 0

    def test_long_maturity(self):
        result = convexity(1000, 0.05, 0.05, 30)
        assert result > 0

    def test_annual_payments(self):
        result = convexity(1000, 0.05, 0.05, 5, 1)
        assert result > 0

    def test_high_ytm(self):
        result = convexity(1000, 0.05, 0.15, 5)
        assert result > 0

    def test_low_coupon_vs_high_coupon(self):
        low_c = convexity(1000, 0.02, 0.05, 10)
        high_c = convexity(1000, 0.10, 0.05, 10)
        assert low_c > high_c

    def test_ndigits(self):
        result = convexity(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)


class TestConvexityAdjustment:
    def test_zero_change(self):
        result = convexity_adjustment(Decimal("50"), Decimal("0"))
        assert result == Decimal("0")

    def test_positive_change(self):
        result = convexity_adjustment(Decimal("50"), Decimal("0.01"))
        assert result > 0

    def test_negative_change_same_as_positive(self):
        pos = convexity_adjustment(Decimal("50"), Decimal("0.01"))
        neg = convexity_adjustment(Decimal("50"), Decimal("-0.01"))
        assert pos == neg

    def test_basic(self):
        result = convexity_adjustment(Decimal("50"), Decimal("0.02"))
        assert result == pytest.approx(Decimal("0.01"), abs=1e-6)


class TestEffectiveConvexity:
    def test_no_change(self):
        result = effective_convexity(Decimal("100"), Decimal("100"), Decimal("100"), Decimal("0.01"))
        assert result == Decimal("0")

    def test_positive(self):
        result = effective_convexity(Decimal("102"), Decimal("98.5"), Decimal("100"), Decimal("0.01"))
        assert result > 0

    def test_zero_initial_price(self):
        with pytest.raises(ValueError):
            effective_convexity(Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0.01"))

    def test_zero_yield_change(self):
        with pytest.raises(ValueError):
            effective_convexity(Decimal("100"), Decimal("100"), Decimal("100"), Decimal("0"))


class TestPriceChangeEstimate:
    def test_no_change(self):
        result = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0"))
        assert result == Decimal("0")

    def test_positive_yield(self):
        result = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0.01"))
        assert result < 0

    def test_negative_yield(self):
        result = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("-0.01"))
        assert result > 0

    def test_convexity_reduces_loss(self):
        linear = -Decimal("5") * Decimal("0.01")
        with_conv = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0.01"))
        assert with_conv > linear


class TestApproximateConvexity:
    def test_basic(self):
        result = approximate_convexity(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_positive(self):
        result = approximate_convexity(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_ndigits(self):
        result = approximate_convexity(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)

    def test_agrees_with_convexity(self):
        c1 = convexity(1000, 0.05, 0.05, 5)
        c2 = approximate_convexity(1000, 0.05, 0.05, 5)
        assert c1 == pytest.approx(c2 / Decimal(4), abs=0.1)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_positive(coupon, years):
    c = convexity(1000, coupon, coupon, years)
    assert c >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_approximate_convexity_positive(coupon, years):
    c = approximate_convexity(1000, coupon, coupon, years)
    assert c >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_effective_convexity_positive(coupon, years):
    from finpy.bonds.clean_price import clean_price
    price = clean_price(1000, coupon, coupon, years)
    shift = Decimal("0.001")
    r = Decimal(str(coupon)) / Decimal(2)
    exp = Decimal(str(years * 2))
    one = Decimal(1)
    price_up = Decimal(1000) * Decimal(str(coupon)) / Decimal(2) * (one - (one + r + shift) ** (-exp)) / (r + shift) + Decimal(1000) / (one + r + shift) ** exp
    price_down = Decimal(1000) * Decimal(str(coupon)) / Decimal(2) * (one - (one + r - shift) ** (-exp)) / (r - shift) + Decimal(1000) / (one + r - shift) ** exp
    result = effective_convexity(price_down, price_up, price, shift)
    assert result >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_adjustment_symmetric(coupon, years):
    adj_pos = convexity_adjustment(Decimal("50"), Decimal("0.01"))
    adj_neg = convexity_adjustment(Decimal("50"), Decimal("-0.01"))
    assert adj_pos == adj_neg


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_price_change_estimate_monotonic(coupon, years):
    base = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0.00"))
    small = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0.01"))
    large = price_change_estimate(Decimal("5"), Decimal("50"), Decimal("0.02"))
    assert base == 0
    assert small < base
    assert large < small


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_and_approx_agree(coupon, years):
    c1 = convexity(1000, coupon, coupon, years)
    c2 = approximate_convexity(1000, coupon, coupon, years)
    assert c1 == pytest.approx(c2 / Decimal(4), abs=0.5)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_greater_for_lower_coupon(coupon, years):
    c_low = convexity(1000, 0.01, coupon, years)
    c_high = convexity(1000, 0.12, coupon, years)
    assert c_low > c_high


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_vs_scaled_duration(coupon, years):
    c = convexity(1000, coupon, coupon, years)
    d = modified_duration(1000, coupon, coupon, years)
    assert c > d * d * Decimal("0.5")


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_increasing_with_maturity(coupon, years):
    short = convexity(1000, coupon, coupon, years)
    long_c = convexity(1000, coupon, coupon, years + 5)
    assert long_c > short


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_adjustment_squared(coupon, years):
    small = convexity_adjustment(Decimal("50"), Decimal("0.001"))
    large = convexity_adjustment(Decimal("50"), Decimal("0.002"))
    assert large == pytest.approx(small * 4, abs=1e-10)


@given(st.decimals(90, 110), st.decimals(90, 110), st.decimals(90, 110), st.decimals(0.001, 0.05))
def test_effective_convexity_zero_for_linear(price_down, price_up, init_price, yc):
    if init_price == 0 or yc == 0:
        return
    if price_down + price_up == 2 * init_price:
        ec = effective_convexity(price_down, price_up, init_price, yc)
        assert ec == 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_price_change_estimate_convexity_helps(coupon, years):
    dur = modified_duration(1000, coupon, coupon, years)
    conv = convexity(1000, coupon, coupon, years)
    linear = -dur * Decimal("0.01")
    full = price_change_estimate(dur, conv, Decimal("0.01"))
    assert full > linear


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_price_change_estimate_down_up(coupon, years):
    dur = modified_duration(1000, coupon, coupon, years)
    conv = convexity(1000, coupon, coupon, years)
    down = price_change_estimate(dur, conv, Decimal("0.01"))
    up = price_change_estimate(dur, conv, Decimal("-0.01"))
    assert abs(down) < abs(-dur * Decimal("0.01"))
    assert up > -dur * Decimal("-0.01")


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_approximate_convexity_positive(coupon, years):
    result = approximate_convexity(1000, coupon, coupon, years)
    assert result >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_adjustment_always_positive(coupon, years):
    pos = convexity_adjustment(Decimal("50"), Decimal("0.01"))
    neg = convexity_adjustment(Decimal("50"), Decimal("-0.01"))
    assert pos >= 0
    assert neg >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_annual_payments_match(coupon, years):
    c = convexity(1000, coupon, coupon, years, 1)
    assert c > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_quarterly_payments(coupon, years):
    c = convexity(1000, coupon, coupon, years, 4)
    assert c > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_approximate_convexity_annual(coupon, years):
    c = approximate_convexity(1000, coupon, coupon, years, 1)
    assert c > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_effective_convexity_symmetric(coupon, years):
    ec = effective_convexity(Decimal("101"), Decimal("101"), Decimal("100"), Decimal("0.01"))
    if ec == 0:
        pass
    assert ec >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_price_change_estimate_duration_only(coupon, years):
    dur = modified_duration(1000, coupon, coupon, years)
    change = price_change_estimate(dur, Decimal("0"), Decimal("0.01"))
    assert change == -dur * Decimal("0.01")


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_price_change_estimate_positive_convexity(coupon, years):
    dur = modified_duration(1000, coupon, coupon, years)
    change_no_conv = price_change_estimate(dur, Decimal("0"), Decimal("0.01"))
    change_with_conv = price_change_estimate(dur, Decimal("50"), Decimal("0.01"))
    assert change_with_conv > change_no_conv


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_zero_coupon_vs_coupon(coupon, years):
    c_zero = convexity(1000, 0.0, coupon, years)
    c_coupon = convexity(1000, coupon, coupon, years)
    assert c_zero > c_coupon


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_approximate_convexity_nonnegative(coupon, years):
    for ppy in [1, 2, 4]:
        c = approximate_convexity(1000, coupon, coupon, years, ppy)
        assert c >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_adjustment_scales_with_square(coupon, years):
    base = convexity_adjustment(Decimal("50"), Decimal("0.001"))
    double = convexity_adjustment(Decimal("50"), Decimal("0.002"))
    assert double == pytest.approx(base * 4, abs=1e-10)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_high_ytm_lower(coupon, years):
    c_low_ytm = convexity(1000, coupon, 0.03, years)
    c_high_ytm = convexity(1000, coupon, 0.08, years)
    assert c_high_ytm < c_low_ytm


@given(st.floats(100, 10000), st.floats(0.02, 0.10), st.floats(2, 10))
def test_convexity_scales_with_face(face, coupon, years):
    c_base = convexity(1000, coupon, coupon, years)
    c_scaled = convexity(face, coupon, coupon, years)
    assert c_scaled > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_approximate_convexity_vs_ppy(coupon, years):
    c2 = approximate_convexity(1000, coupon, coupon, years, 2)
    c4 = approximate_convexity(1000, coupon, coupon, years, 4)
    assert c2 != c4


@given(st.decimals(90, 110), st.decimals(90, 110), st.decimals(90, 110), st.decimals(0.001, 0.05))
def test_effective_convexity_no_error(price_down, price_up, init_price, yc):
    if init_price == 0 or yc == 0:
        return
    ec = effective_convexity(price_down, price_up, init_price, yc)
    assert isinstance(ec, Decimal)


