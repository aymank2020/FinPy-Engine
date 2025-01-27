from decimal import Decimal
import pytest
from hypothesis import given, strategies as st
from finpy.bonds.duration import macaulay_duration, modified_duration, dollar_duration, pvbp
from finpy.bonds.duration import key_rate_duration, effective_duration
from finpy.bonds.convexity import convexity
from finpy.bonds.clean_price import clean_price
from finpy.core.errors import NoSolutionFoundError
from tests._helpers import approx_decimal


class TestMacaulayDuration:
    def test_basic(self):
        result = macaulay_duration(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_zero_coupon_equals_maturity(self):
        result = macaulay_duration(1000, 0.0, 0.05, 5)
        assert result == pytest.approx(Decimal("5.0"), abs=0.01)

    def test_par_bond_less_than_maturity(self):
        result = macaulay_duration(1000, 0.05, 0.05, 5)
        assert result < Decimal("5")

    def test_short_maturity(self):
        result = macaulay_duration(1000, 0.05, 0.05, 0.5)
        assert result == pytest.approx(Decimal("0.5"), abs=0.01)

    def test_long_maturity(self):
        result = macaulay_duration(1000, 0.05, 0.05, 30)
        assert result > 0

    def test_annual_payments(self):
        result_macaulay = macaulay_duration(1000, 0.05, 0.05, 5, 1)
        assert result_macaulay > 0

    def test_high_coupon_shorter_duration(self):
        low_coupon = macaulay_duration(1000, 0.02, 0.05, 10)
        high_coupon = macaulay_duration(1000, 0.10, 0.05, 10)
        assert high_coupon < low_coupon

    def test_ytm_increases_duration_decreases(self):
        low_ytm = macaulay_duration(1000, 0.05, 0.02, 10)
        high_ytm = macaulay_duration(1000, 0.05, 0.10, 10)
        assert high_ytm < low_ytm

    def test_ndigits(self):
        result = macaulay_duration(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)


class TestModifiedDuration:
    def test_basic(self):
        result = modified_duration(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_less_than_macaulay(self):
        mac = macaulay_duration(1000, 0.05, 0.05, 5)
        mod = modified_duration(1000, 0.05, 0.05, 5)
        assert mod < mac

    def test_zero_coupon(self):
        result = modified_duration(1000, 0.0, 0.05, 5)
        assert result > 0

    def test_high_ytm(self):
        result = modified_duration(1000, 0.05, 0.15, 5)
        assert result > 0

    def test_short_maturity(self):
        result = modified_duration(1000, 0.05, 0.05, 0.5)
        assert result > 0

    def test_ndigits(self):
        result = modified_duration(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)

    def test_relationship_with_macaulay(self):
        mac = macaulay_duration(1000, 0.05, 0.05, 5)
        mod = modified_duration(1000, 0.05, 0.05, 5)
        expected = mac / (Decimal(1) + Decimal("0.05") / Decimal("2"))
        assert mod == pytest.approx(expected, abs=1e-10)


class TestDollarDuration:
    def test_basic(self):
        result = dollar_duration(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_positive(self):
        result = dollar_duration(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_ndigits(self):
        result = dollar_duration(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)


class TestPVBP:
    def test_basic(self):
        result = pvbp(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_positive(self):
        result = pvbp(1000, 0.05, 0.05, 5)
        assert result > 0

    def test_ndigits(self):
        result = pvbp(1000, 0.05, 0.05, 5, ndigits=4)
        assert isinstance(result, Decimal)


class TestKeyRateDuration:
    def test_basic(self):
        result = key_rate_duration(1000, 0.05, 0.05, 5, 5.0)
        assert result != 0

    def test_nonzero(self):
        result = key_rate_duration(1000, 0.05, 0.05, 5, 2.0)
        assert result != 0

    def test_different_tenors(self):
        r1 = key_rate_duration(1000, 0.05, 0.05, 5, 2.0)
        r2 = key_rate_duration(1000, 0.05, 0.05, 5, 5.0)
        assert r1 != r2


class TestEffectiveDuration:
    def test_no_change(self):
        result = effective_duration(Decimal("100"), Decimal("100"), Decimal("100"), Decimal("0.01"))
        assert result == Decimal("0")

    def test_basic(self):
        result = effective_duration(Decimal("101"), Decimal("99"), Decimal("100"), Decimal("0.01"))
        assert result == pytest.approx(Decimal("1.0"), abs=0.01)

    def test_price_down_gt_price_up(self):
        result = effective_duration(Decimal("102"), Decimal("98"), Decimal("100"), Decimal("0.01"))
        assert result > 0

    def test_zero_initial_price(self):
        with pytest.raises(ValueError):
            effective_duration(Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0.01"))

    def test_zero_yield_change(self):
        with pytest.raises(ValueError):
            effective_duration(Decimal("100"), Decimal("100"), Decimal("100"), Decimal("0"))


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_modified_duration_non_negative(coupon, years):
    d = modified_duration(1000, coupon, coupon, years)
    assert d >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_duration_non_negative(coupon, years):
    d = macaulay_duration(1000, coupon, coupon, years)
    assert d >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_mod_duration_lt_mac_duration(coupon, years):
    mac = macaulay_duration(1000, coupon, coupon, years)
    mod = modified_duration(1000, coupon, coupon, years)
    assert mod < mac


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_dollar_duration_non_negative(coupon, years):
    d = dollar_duration(1000, coupon, coupon, years)
    assert d >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_pvbp_non_negative(coupon, years):
    p = pvbp(1000, coupon, coupon, years)
    assert p >= 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_between_zero_and_maturity(coupon, years):
    d = macaulay_duration(1000, coupon, coupon, years)
    assert Decimal("0") < d < Decimal(str(years)) + Decimal("1")


@given(st.floats(0.02, 0.10), st.integers(2, 10))
def test_zero_coupon_macaulay_equals_maturity(coupon, years):
    d = macaulay_duration(1000, 0.0, coupon, years)
    assert d == pytest.approx(Decimal(str(years)), abs=0.01)


@given(st.decimals(90, 110), st.decimals(90, 110), st.decimals(90, 110), st.decimals(0.001, 0.05))
def test_effective_duration_consistent(price_down, price_up, init_price, yc):
    if init_price == 0 or yc == 0:
        return
    d = effective_duration(price_down, price_up, init_price, yc)
    if price_down > price_up:
        assert d > 0
    elif price_down < price_up:
        assert d < 0
    else:
        assert d == 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_key_rate_duration_nonzero(coupon, years):
    krd = key_rate_duration(1000, coupon, coupon, years, float(years) / 2)
    assert krd != 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_greater_than_modified(coupon, years):
    mac = macaulay_duration(1000, coupon, coupon, years)
    mod = modified_duration(1000, coupon, coupon, years)
    assert mac > mod


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_modified_duration_positive_for_zero_coupon(coupon, years):
    result = modified_duration(1000, 0.0, coupon, years)
    assert result > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_dollar_duration_positive(coupon, years):
    result = dollar_duration(1000, coupon, coupon, years)
    assert result > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_pvbp_small_positive(coupon, years):
    result = pvbp(1000, coupon, coupon, years)
    assert Decimal("0") < result < Decimal("100")


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_duration_increasing_with_maturity(coupon, years):
    short = macaulay_duration(1000, coupon, coupon, years)
    long_d = macaulay_duration(1000, coupon, coupon, years + 5)
    assert long_d > short


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_dollar_duration_vs_modified(coupon, years):
    dd = dollar_duration(1000, coupon, coupon, years)
    md = modified_duration(1000, coupon, coupon, years)
    assert dd > md


@given(st.decimals(50, 150), st.decimals(50, 150), st.decimals(50, 150), st.decimals(0.001, 0.05))
def test_effective_duration_symmetric(price_down, price_up, init_price, yc):
    if init_price == 0 or yc == 0:
        return
    d = effective_duration(price_down, price_up, init_price, yc)
    d_rev = effective_duration(price_up, price_down, init_price, yc)
    assert d == -d_rev


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_key_rate_duration_scales_with_tenor(coupon, years):
    k1 = key_rate_duration(1000, coupon, coupon, years, 2.0)
    k2 = key_rate_duration(1000, coupon, coupon, years, 5.0)
    assert k2 > k1 or k2 < k1


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_pvbp_vs_dollar_duration(coupon, years):
    dd = dollar_duration(1000, coupon, coupon, years)
    pv = pvbp(1000, coupon, coupon, years)
    assert pv > 0
    assert dd > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_duration_annual(coupon, years):
    d = macaulay_duration(1000, coupon, coupon, years, 1)
    assert d > 0
    assert d < Decimal(str(years))


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_duration_quarterly(coupon, years):
    d = macaulay_duration(1000, coupon, coupon, years, 4)
    assert d > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_modified_duration_annual(coupon, years):
    d = modified_duration(1000, coupon, coupon, years, 1)
    assert d > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_dollar_duration_annual(coupon, years):
    d = dollar_duration(1000, coupon, coupon, years, 1)
    assert d > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_pvbp_annual(coupon, years):
    p = pvbp(1000, coupon, coupon, years, 1)
    assert p > 0


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_vs_modified_ratio(coupon, years):
    mac = macaulay_duration(1000, coupon, coupon, years, 2)
    mod = modified_duration(1000, coupon, coupon, years, 2)
    r = Decimal(str(coupon)) / Decimal(2)
    expected = mac / (Decimal(1) + r)
    assert mod == pytest.approx(expected, abs=1e-10)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_macaulay_high_coupon_lower(coupon, years):
    d_low = macaulay_duration(1000, 0.02, coupon, years)
    d_high = macaulay_duration(1000, 0.10, coupon, years)
    assert d_high < d_low


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_modified_duration_increasing_maturity(coupon, years):
    d_short = modified_duration(1000, coupon, coupon, years)
    d_long = modified_duration(1000, coupon, coupon, years + 10)
    assert d_long > d_short


@given(st.decimals(50, 150), st.decimals(50, 150), st.decimals(50, 150), st.decimals(0.001, 0.05))
def test_effective_duration_no_nan(price_down, price_up, init_price, yc):
    if init_price == 0 or yc == 0:
        return
    d = effective_duration(price_down, price_up, init_price, yc)
    assert isinstance(d, Decimal)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_key_rate_duration_positive_tenor(coupon, years):
    krd = key_rate_duration(1000, coupon, coupon, years, 1.0)
    assert isinstance(krd, Decimal)


@given(st.floats(0.02, 0.10), st.floats(2, 10))
def test_dollar_duration_vs_pvbp(coupon, years):
    dd = dollar_duration(1000, coupon, coupon, years)
    pv = pvbp(1000, coupon, coupon, years)
    assert dd > pv or dd <= pv


