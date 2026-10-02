from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.core.discount import discount_factor, present_value_of_flow, present_value, future_value_of_flow
from finpy.core.discount import discount_yield, money_market_yield, bond_equivalent_yield, yield_to_maturity
from finpy.core.discount import current_yield, macaulay_duration, modified_duration, convexity
from finpy.core.discount import zero_coupon_rate, forward_rate, annuity_factor, sinking_factor, capital_recovery_factor
from tests._helpers import approx_decimal


class TestDiscountFactor:
    def test_annual(self):
        result = discount_factor(Decimal("0.05"), 1.0)
        assert result == pytest.approx(Decimal("0.95238"), abs=1e-5)

    def test_zero_rate(self):
        result = discount_factor(Decimal("0"), 1.0)
        assert result == Decimal("1")

    def test_semi_annual(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="semi-annual")
        assert result == pytest.approx(Decimal("0.95181"), abs=1e-5)

    def test_quarterly(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="quarterly")
        assert result == pytest.approx(Decimal("0.95152"), abs=1e-5)

    def test_monthly(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="monthly")
        assert result == pytest.approx(Decimal("0.95133"), abs=1e-5)

    def test_weekly(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="weekly")
        assert result == pytest.approx(Decimal("0.95125"), abs=1e-5)

    def test_daily(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="daily")
        assert result == pytest.approx(Decimal("0.95123"), abs=1e-5)

    def test_continuous(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="continuous")
        assert result == pytest.approx(Decimal("0.95123"), abs=1e-5)

    def test_money_market(self):
        result = discount_factor(Decimal("0.05"), 1.0, mode="money-market")
        assert result == pytest.approx(Decimal("0.95238"), abs=1e-5)

    def test_bond_basis(self):
        result = discount_factor(Decimal("0.05"), 365.0, mode="bond-basis")
        assert result == pytest.approx(Decimal("0.95238"), abs=1e-5)

    def test_unknown_mode(self):
        with pytest.raises(ValueError):
            discount_factor(Decimal("0.05"), 1.0, mode="unknown")

    def test_zero_time(self):
        result = discount_factor(Decimal("0.05"), 0.0)
        assert result == Decimal("1")

    def test_negative_rate(self):
        result = discount_factor(Decimal("-0.05"), 1.0)
        assert result > Decimal("1")

    def test_multiple_years(self):
        result = discount_factor(Decimal("0.10"), 10.0)
        assert result == pytest.approx(Decimal("0.38554"), abs=1e-5)


class TestPresentValueOfFlow:
    def test_basic(self):
        result = present_value_of_flow(Decimal("100"), 1.0, Decimal("0.05"))
        assert result == pytest.approx(Decimal("95.238"), abs=0.001)

    def test_zero_rate(self):
        result = present_value_of_flow(Decimal("100"), 1.0, Decimal("0"))
        assert result == Decimal("100")

    def test_zero_time(self):
        result = present_value_of_flow(Decimal("100"), 0.0, Decimal("0.05"))
        assert result == Decimal("100")

    def test_negative_flow(self):
        result = present_value_of_flow(Decimal("-100"), 1.0, Decimal("0.05"))
        assert result == pytest.approx(Decimal("-95.238"), abs=0.001)

    def test_continuous_mode(self):
        result = present_value_of_flow(Decimal("100"), 1.0, Decimal("0.05"), mode="continuous")
        assert result == pytest.approx(Decimal("95.123"), abs=0.01)

    def test_money_market(self):
        result = present_value_of_flow(Decimal("100"), 0.5, Decimal("0.05"), mode="money-market")
        assert result == pytest.approx(Decimal("97.560"), abs=0.01)


class TestPresentValue:
    def test_basic(self):
        cfs = [(Decimal("100"), 1.0), (Decimal("200"), 2.0)]
        result = present_value(cfs, Decimal("0.10"))
        assert result == pytest.approx(Decimal("256.198"), abs=0.001)

    def test_empty(self):
        result = present_value([], Decimal("0.10"))
        assert result == Decimal("0")

    def test_zero_rate(self):
        cfs = [(Decimal("100"), 1.0), (Decimal("200"), 2.0)]
        result = present_value(cfs, Decimal("0"))
        assert result == Decimal("300")

    def test_single_flow(self):
        cfs = [(Decimal("100"), 1.0)]
        result = present_value(cfs, Decimal("0.05"))
        assert result == pytest.approx(Decimal("95.238"), abs=0.001)

    def test_with_mode(self):
        cfs = [(Decimal("100"), 1.0)]
        result = present_value(cfs, Decimal("0.05"), mode="continuous")
        assert result == pytest.approx(Decimal("95.123"), abs=0.01)


class TestFutureValueOfFlow:
    def test_basic(self):
        result = future_value_of_flow(Decimal("100"), 2.0, Decimal("0.05"))
        assert result == pytest.approx(Decimal("110.25"), abs=1e-10)

    def test_zero_rate(self):
        result = future_value_of_flow(Decimal("100"), 2.0, Decimal("0"))
        assert result == Decimal("100")

    def test_fractional_time(self):
        result = future_value_of_flow(Decimal("100"), 1.5, Decimal("0.05"))
        assert result == pytest.approx(Decimal("107.593"), abs=0.01)

    def test_zero_time(self):
        result = future_value_of_flow(Decimal("100"), 0.0, Decimal("0.05"))
        assert result == Decimal("100")


class TestDiscountYield:
    def test_basic(self):
        result = discount_yield(Decimal("98"), Decimal("100"), 180)
        assert result == pytest.approx(Decimal("0.04"), abs=1e-5)

    def test_zero_days(self):
        with pytest.raises(ValueError):
            discount_yield(Decimal("98"), Decimal("100"), 0)

    def test_negative_price(self):
        with pytest.raises(ValueError):
            discount_yield(Decimal("-98"), Decimal("100"), 180)

    def test_at_par(self):
        result = discount_yield(Decimal("100"), Decimal("100"), 180)
        assert result == Decimal("0")

    def test_custom_days_year(self):
        result = discount_yield(Decimal("98"), Decimal("100"), 180, days_year=365)
        assert result == pytest.approx(Decimal("0.040556"), abs=1e-6)


class TestMoneyMarketYield:
    def test_basic(self):
        result = money_market_yield(Decimal("0.04"), 180)
        assert result == pytest.approx(Decimal("0.040816"), abs=1e-6)

    def test_zero_days(self):
        with pytest.raises(ValueError):
            money_market_yield(Decimal("0.04"), 0)

    def test_custom_days_year(self):
        result = money_market_yield(Decimal("0.04"), 180, days_year=365)
        assert result == pytest.approx(Decimal("0.040805"), abs=1e-6)


class TestBondEquivalentYield:
    def test_basic(self):
        result = bond_equivalent_yield(Decimal("98"), Decimal("100"), 180)
        assert result == pytest.approx(Decimal("0.041384"), abs=1e-6)

    def test_zero_days(self):
        with pytest.raises(ValueError):
            bond_equivalent_yield(Decimal("98"), Decimal("100"), 0)

    def test_negative_price(self):
        with pytest.raises(ValueError):
            bond_equivalent_yield(Decimal("-98"), Decimal("100"), 180)

    def test_at_par(self):
        result = bond_equivalent_yield(Decimal("100"), Decimal("100"), 180)
        assert result == Decimal("0")


class TestCurrentYield:
    def test_basic(self):
        result = current_yield(Decimal("50"), Decimal("1000"))
        assert result == Decimal("0.05")

    def test_zero_price(self):
        with pytest.raises(ValueError):
            current_yield(Decimal("50"), Decimal("0"))


class TestMacaulayDuration:
    def test_zero_coupon_bond(self):
        cfs = [(Decimal("1000"), 5.0)]
        dur = macaulay_duration(cfs, Decimal("0.05"))
        assert dur == pytest.approx(Decimal("5"), abs=0.01)

    def test_coupon_bond(self):
        cfs = [(Decimal("50"), 1.0), (Decimal("50"), 2.0), (Decimal("1050"), 3.0)]
        dur = macaulay_duration(cfs, Decimal("0.05"))
        assert dur == pytest.approx(Decimal("2.859"), abs=0.01)

    def test_zero_pv(self):
        with pytest.raises(ValueError):
            macaulay_duration([(Decimal("0"), 1.0)], Decimal("0.05"))


class TestModifiedDuration:
    def test_basic(self):
        md = modified_duration([(Decimal("1000"), 5)], Decimal("0.05"))
        assert md == pytest.approx(Decimal(5) / Decimal("1.05"), abs=Decimal("1e-20"))

    def test_semi_annual(self):
        md = modified_duration([(Decimal("1000"), 5)], Decimal("0.05"), periods_per_year=2)
        assert md == pytest.approx(Decimal(5) / Decimal("1.025"), abs=Decimal("1e-20"))


class TestConvexity:
    def test_zero_coupon(self):
        cfs = [(Decimal("1000"), 5.0)]
        conv = convexity(cfs, Decimal("0.05"))
        assert conv > 0

    def test_coupon_bond(self):
        cfs = [(Decimal("50"), 1.0), (Decimal("50"), 2.0), (Decimal("1050"), 3.0)]
        conv = convexity(cfs, Decimal("0.05"))
        assert conv > 0

    def test_zero_pv(self):
        with pytest.raises(ValueError):
            convexity([(Decimal("0"), 1.0)], Decimal("0.05"))


class TestZeroCouponRate:
    def test_annual(self):
        zcr = zero_coupon_rate(Decimal("0.95238"), 1.0)
        assert zcr == pytest.approx(Decimal("0.05"), abs=1e-4)

    def test_continuous(self):
        zcr = zero_coupon_rate(Decimal("0.95123"), 1.0, mode="continuous")
        assert zcr == pytest.approx(Decimal("0.05"), abs=1e-4)

    def test_semi_annual(self):
        zcr = zero_coupon_rate(Decimal("0.95181"), 1.0, mode="semi-annual")
        assert zcr == pytest.approx(Decimal("0.05"), abs=1e-4)

    def test_money_market(self):
        zcr = zero_coupon_rate(Decimal("0.95238"), 1.0, mode="money-market")
        assert zcr == pytest.approx(Decimal("0.05"), abs=1e-4)

    def test_invalid_df(self):
        with pytest.raises(ValueError):
            zero_coupon_rate(Decimal("0"), 1.0)

    def test_df_greater_than_one_implies_negative_yield(self):
        rate = zero_coupon_rate(Decimal("2"), 1.0)
        assert rate == Decimal("-0.5")
        assert discount_factor(rate, 1) == Decimal("2")

    def test_zero_time(self):
        with pytest.raises(ValueError):
            zero_coupon_rate(Decimal("0.95"), 0.0)

    def test_unknown_mode(self):
        with pytest.raises(ValueError):
            zero_coupon_rate(Decimal("0.95"), 1.0, mode="unknown")


class TestForwardRate:
    def test_basic(self):
        fr = forward_rate(Decimal("0.05"), Decimal("0.06"), 1.0, 2.0)
        assert fr == pytest.approx(Decimal("0.07012"), abs=1e-4)

    def test_invalid_order(self):
        with pytest.raises(ValueError):
            forward_rate(Decimal("0.05"), Decimal("0.06"), 2.0, 1.0)

    def test_negative_short_time(self):
        with pytest.raises(ValueError):
            forward_rate(Decimal("0.05"), Decimal("0.06"), -1.0, 2.0)

    def test_zero_spread(self):
        fr = forward_rate(Decimal("0.05"), Decimal("0.05"), 1.0, 2.0)
        assert fr == pytest.approx(Decimal("0.05"), abs=1e-10)


class TestAnnuityFactor:
    def test_basic(self):
        af = annuity_factor(Decimal("0.05"), 10)
        assert af == pytest.approx(Decimal("7.72173"), abs=1e-5)

    def test_zero_rate(self):
        af = annuity_factor(Decimal("0"), 10)
        assert af == Decimal("10")

    def test_continuous(self):
        af = annuity_factor(Decimal("0.05"), 10, mode="continuous")
        assert af == pytest.approx(Decimal("7.8694"), abs=1e-4)

    def test_one_period(self):
        af = annuity_factor(Decimal("0.05"), 1)
        assert af == pytest.approx(Decimal("0.95238"), abs=1e-5)

    def test_unknown_mode(self):
        with pytest.raises(ValueError):
            annuity_factor(Decimal("0.05"), 10, mode="unknown")


class TestSinkingFactor:
    def test_basic(self):
        sf = sinking_factor(Decimal("0.05"), 10)
        assert sf == pytest.approx(Decimal("0.07950"), abs=1e-5)

    def test_zero_rate(self):
        sf = sinking_factor(Decimal("0"), 10)
        assert sf == pytest.approx(Decimal("0.10"), abs=1e-5)

    def test_one_period(self):
        sf = sinking_factor(Decimal("0.05"), 1)
        assert sf == Decimal("1")


class TestCapitalRecoveryFactor:
    def test_basic(self):
        crf = capital_recovery_factor(Decimal("0.05"), 10)
        assert crf == pytest.approx(Decimal("0.12950"), abs=1e-5)

    def test_zero_rate(self):
        crf = capital_recovery_factor(Decimal("0"), 10)
        assert crf == pytest.approx(Decimal("0.10"), abs=1e-5)

    def test_one_period(self):
        crf = capital_recovery_factor(Decimal("0.05"), 1)
        assert crf == pytest.approx(Decimal("1.05"), abs=1e-10)


class TestYieldToMaturity:
    def test_zero_coupon(self):
        ytm = yield_to_maturity(Decimal("783.53"), Decimal("1000"), Decimal("0"), 10)
        assert ytm == pytest.approx(Decimal("0.0247"), abs=0.001)

    def test_coupon_bond(self):
        ytm = yield_to_maturity(Decimal("950"), Decimal("1000"), Decimal("40"), 10)
        assert ytm == pytest.approx(Decimal("0.0465"), abs=0.001)

    def test_negative_price(self):
        with pytest.raises(ValueError):
            yield_to_maturity(Decimal("-950"), Decimal("1000"), Decimal("40"), 10)

    def test_zero_periods(self):
        with pytest.raises(ValueError):
            yield_to_maturity(Decimal("950"), Decimal("1000"), Decimal("40"), 0)

    def test_at_par(self):
        ytm = yield_to_maturity(Decimal("1000"), Decimal("1000"), Decimal("50"), 10)
        assert ytm == pytest.approx(Decimal("0.05"), abs=0.001)


@given(st.floats(min_value=0.01, max_value=0.5), st.floats(min_value=0.5, max_value=10.0))
def test_discount_factor_between_zero_and_one(rate, t):
    result = discount_factor(Decimal(str(rate)), t)
    assert Decimal("0") < result < Decimal("1")


@given(st.floats(min_value=0.01, max_value=0.5))
def test_zero_coupon_rate_roundtrip(rate):
    df = discount_factor(Decimal(str(rate)), 1.0)
    zcr = zero_coupon_rate(df, 1.0)
    assert zcr == pytest.approx(Decimal(str(rate)), abs=1e-4)


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=2, max_value=30))
def test_annuity_sinking_roundtrip(rate, nper):
    af = annuity_factor(Decimal(str(rate)), nper)
    sf = sinking_factor(Decimal(str(rate)), nper)
    one = Decimal(1)
    expected = one / (one + Decimal(str(rate))) ** nper
    assert af * sf == pytest.approx(expected, abs=1e-10)
