from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.fx.spot import convert_spot, convert_bid_ask, cross_rate, inverse_rate
from finpy.fx.spot import pips_to_points, points_to_pips, midpoint_rate
from finpy.fx.spot import is_positive_carry, forward_points
from finpy.core.errors import UnknownCurrencyError
from tests._helpers import approx_decimal


class TestConvertSpot:
    def test_basic(self):
        result = convert_spot(100, "USD", "EUR", 0.85)
        assert result == Decimal("85")

    def test_unknown_currency(self):
        with pytest.raises(UnknownCurrencyError):
            convert_spot(100, "AAA", "USD", 1.0)

    def test_unknown_target(self):
        with pytest.raises(UnknownCurrencyError):
            convert_spot(100, "USD", "ZZZ", 1.0)

    def test_with_ndigits(self):
        result = convert_spot(100, "USD", "EUR", 0.85678, ndigits=2)
        assert result == Decimal("85.68")

    def test_zero_amount(self):
        result = convert_spot(0, "USD", "EUR", 0.85)
        assert result == Decimal(0)

    def test_rate_gt_one(self):
        result = convert_spot(100, "USD", "JPY", 110.0)
        assert result == Decimal("11000")

    def test_negative_amount(self):
        result = convert_spot(-100, "USD", "EUR", 0.85)
        assert result == Decimal("-85")

    def test_large_amount(self):
        result = convert_spot(1e6, "USD", "EUR", 0.85)
        assert result == Decimal("850000")


class TestConvertBidAsk:
    def test_basic(self):
        result = convert_bid_ask(100, "USD", "EUR", 0.84, 0.86)
        assert "bid" in result
        assert "ask" in result
        assert "mid" in result
        assert "spread" in result
        assert result["bid"] < result["ask"]

    def test_unknown_from(self):
        with pytest.raises(UnknownCurrencyError):
            convert_bid_ask(100, "XXX", "EUR", 0.84, 0.86)

    def test_unknown_to(self):
        with pytest.raises(UnknownCurrencyError):
            convert_bid_ask(100, "USD", "YYY", 0.84, 0.86)

    def test_bid_gt_ask(self):
        with pytest.raises(ValueError):
            convert_bid_ask(100, "USD", "EUR", 0.86, 0.84)

    def test_bid_equals_ask(self):
        result = convert_bid_ask(100, "USD", "EUR", 0.85, 0.85)
        assert result["spread"] == Decimal(0)

    def test_with_ndigits(self):
        result = convert_bid_ask(100, "USD", "EUR", 0.84123, 0.86234, ndigits=2)
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_mid_is_average(self):
        result = convert_bid_ask(100, "USD", "EUR", 0.84, 0.86)
        assert result["mid"] == (result["bid"] + result["ask"]) / Decimal(2)

    def test_zero_amount(self):
        result = convert_bid_ask(0, "USD", "EUR", 0.84, 0.86)
        assert result["bid"] == Decimal(0)
        assert result["ask"] == Decimal(0)

    def test_large_amount(self):
        result = convert_bid_ask(1e6, "USD", "EUR", 0.84, 0.86)
        assert result["bid"] == Decimal("840000")
        assert result["ask"] == Decimal("860000")


class TestCrossRate:
    def test_basic(self):
        result = cross_rate(1.2, 0.85, "USD", "EUR", "GBP")
        assert isinstance(result, Decimal)

    def test_unknown_currency(self):
        with pytest.raises(UnknownCurrencyError):
            cross_rate(1.2, 0.85, "XXX", "EUR", "GBP")

    def test_with_ndigits(self):
        result = cross_rate(1.2, 0.85, "USD", "EUR", "GBP", ndigits=4)
        assert isinstance(result, Decimal)

    def test_rate_zero(self):
        with pytest.raises(UnknownCurrencyError):
            cross_rate(1.2, 0.85, "YYY", "EUR", "GBP")

    def test_cross_rate_value(self):
        result = cross_rate(1.2, 0.85, "USD", "EUR", "GBP")
        assert result == Decimal("1.2") / Decimal("0.85")

    def test_same_currencies(self):
        result = cross_rate(1.0, 1.0, "USD", "EUR", "GBP")
        assert result == Decimal(1)


class TestInverseRate:
    def test_basic(self):
        result = inverse_rate(0.85)
        assert result == pytest.approx(Decimal("1.176470588235294"), abs=Decimal("1e-10"))

    def test_zero_rate(self):
        with pytest.raises(ValueError):
            inverse_rate(0)

    def test_negative_rate(self):
        with pytest.raises(ValueError):
            inverse_rate(-0.5)

    def test_with_ndigits(self):
        result = inverse_rate(0.85, ndigits=3)
        assert result == Decimal("1.176")

    def test_rate_of_one(self):
        result = inverse_rate(1.0)
        assert result == Decimal(1)

    def test_inverse_of_inverse(self):
        result = inverse_rate(inverse_rate(0.85))
        assert result == pytest.approx(Decimal("0.85"), abs=Decimal("0.001"))


class TestPipsToPoints:
    def test_basic(self):
        result = pips_to_points(1.2000, 50)
        assert result == Decimal("1.205")

    def test_zero_pips(self):
        result = pips_to_points(1.2000, 0)
        assert result == Decimal("1.2")


class TestPointsToPips:
    def test_basic(self):
        result = points_to_pips(1.2050, 1.2000)
        assert result == Decimal(50)

    def test_larger_rate_first_negative(self):
        result = points_to_pips(1.2000, 1.2050)
        assert result < 0


class TestMidpointRate:
    def test_basic(self):
        result = midpoint_rate(1.2000, 1.2100)
        assert result == Decimal("1.205")

    def test_bid_gt_ask(self):
        with pytest.raises(ValueError):
            midpoint_rate(1.2100, 1.2000)

    def test_equal(self):
        result = midpoint_rate(1.2000, 1.2000)
        assert result == Decimal("1.2")

    def test_with_ndigits(self):
        result = midpoint_rate(1.20123, 1.20897, ndigits=4)
        assert result == Decimal("1.2051")


class TestIsPositiveCarry:
    def test_positive(self):
        assert is_positive_carry(0.01, 0.02) is True

    def test_negative(self):
        assert is_positive_carry(0.02, 0.01) is False

    def test_equal(self):
        assert is_positive_carry(0.01, 0.01) is False


class TestForwardPoints:
    def test_basic(self):
        result = forward_points(1.2000, 1.2050)
        assert result == Decimal(50)

    def test_negative(self):
        result = forward_points(1.2050, 1.2000)
        assert result == Decimal(-50)

    def test_zero(self):
        result = forward_points(1.2000, 1.2000)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        result = forward_points(1.2000, 1.205678, ndigits=2)
        assert isinstance(result, Decimal)


@given(st.floats(0.01, 1000), st.floats(0.01, 10))
def test_fx_spot_roundtrip(amount, rate):
    result = convert_spot(amount, "USD", "EUR", rate)
    back = convert_spot(float(result), "EUR", "USD", 1.0 / rate)
    assert back == pytest.approx(Decimal(str(amount)), abs=0.01)


@given(st.floats(0.01, 10))
def test_inverse_roundtrip(rate):
    assume(rate > 0)
    inv = inverse_rate(rate)
    back = inverse_rate(inv)
    assert back == pytest.approx(Decimal(str(rate)), abs=Decimal("1e-10"))


@given(st.floats(0.01, 10), st.floats(0.01, 10))
def test_pips_points_roundtrip(rate, pips):
    pips = abs(pips) % 10000
    result = pips_to_points(rate, pips)
    back = points_to_pips(result, Decimal(str(rate)))
    assert back == pytest.approx(Decimal(str(pips)), abs=Decimal("0.001"))


@given(st.floats(1, 1000))
def test_convert_spot_identity(amount):
    result = convert_spot(amount, "USD", "USD", 1.0)
    assert result == Decimal(str(amount))


@given(st.floats(0.01, 10), st.floats(0.01, 10))
def test_forward_points_symmetric(bid, ask):
    assume(bid != ask)
    fp = forward_points(max(bid, ask), min(bid, ask))
    fn = forward_points(min(bid, ask), max(bid, ask))
    assert fp == -fn


@given(st.floats(0.01, 10))
def test_midpoint_rate_between(rate):
    bid = rate - 0.001
    ask = rate + 0.001
    mid = midpoint_rate(bid, ask)
    assert bid <= float(mid) <= ask


@given(st.floats(1, 1000))
def test_convert_spot_ndigits_rounding(amount):
    result = convert_spot(amount, "USD", "EUR", 0.85678, ndigits=1)
    assert isinstance(result, Decimal)


@given(st.floats(0.01, 10), st.floats(0.01, 10))
def test_is_positive_carry_direction(short_r, long_r):
    assert is_positive_carry(short_r, long_r) == (long_r > short_r)


@given(st.floats(1, 1000), st.floats(0.01, 10))
def test_convert_bid_ask_midpoint(amount, spread):
    rate = spread + 0.01
    result = convert_bid_ask(amount, "USD", "EUR", rate, rate + spread)
    expected_mid = Decimal(str(amount)) * (Decimal(str(rate)) + Decimal(str(rate + spread))) / Decimal(2)
    assert result["mid"] == pytest.approx(expected_mid, abs=Decimal("1e-10"))


@given(st.floats(0.01, 10), st.floats(0.001, 0.1))
def test_cross_rate_known_currencies(rate, spread):
    result = cross_rate(rate + spread, rate, "USD", "EUR", "GBP")
    assert isinstance(result, Decimal)


@given(st.floats(0.01, 1000))
def test_forward_points_positive_for_bid_lt_ask(amount):
    fp = forward_points(amount, amount + 0.01)
    assert fp > 0


@given(st.floats(0.01, 1000))
def test_forward_points_negative_for_bid_gt_ask(amount):
    fp = forward_points(amount + 0.01, amount)
    assert fp < 0
