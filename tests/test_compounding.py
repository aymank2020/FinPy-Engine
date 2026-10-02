from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.core.compounding import compound, compound_factor, effective_annual_rate, nominal_from_effective
from finpy.core.compounding import continuous_equiv, discrete_equiv, doubling_time, future_value, present_value
from finpy.core.compounding import growth_rate, annualized_return, ln, exp, rule_of_72, rule_of_114, rule_of_144
from finpy.core.compounding import compounding_frequency, periodic_rate, annual_rate_from_periodic
from finpy.core.compounding import holding_period_return, real_rate_of_return, force_of_interest
from finpy.core.compounding import discount_rate_from_interest, interest_rate_from_discount
from tests._helpers import approx_decimal


class TestCompound:
    def test_annual(self):
        result = compound(Decimal("0.05"), 2)
        assert result == pytest.approx(Decimal("1.1025"), abs=1e-10)

    def test_semi_annual(self):
        result = compound(Decimal("0.05"), 2, mode="semi-annual")
        assert result == pytest.approx(Decimal("1.103812890625"), abs=1e-10)

    def test_continuous(self):
        result = compound(Decimal("0.05"), 1, mode="continuous")
        assert result > Decimal("1.05")

    def test_quarterly(self):
        result = compound(Decimal("0.05"), 2, mode="quarterly")
        assert result == pytest.approx(Decimal("1.104486"), abs=1e-6)

    def test_monthly(self):
        result = compound(Decimal("0.05"), 2, mode="monthly")
        assert result == pytest.approx(Decimal("1.104941"), abs=1e-6)

    def test_weekly(self):
        result = compound(Decimal("0.05"), 2, mode="weekly")
        assert result == pytest.approx(Decimal("1.105118"), abs=1e-6)

    def test_daily(self):
        result = compound(Decimal("0.05"), 2, mode="daily")
        assert result == pytest.approx(Decimal("1.105163"), abs=1e-6)

    def test_zero_rate(self):
        result = compound(Decimal("0"), 5)
        assert result == Decimal(1)

    def test_one_period(self):
        result = compound(Decimal("0.10"), 1)
        assert result == Decimal("1.10")

    def test_unknown_mode(self):
        with pytest.raises(ValueError):
            compound(Decimal("0.05"), 1, mode="unknown")

    def test_zero_periods(self):
        result = compound(Decimal("0.05"), 0)
        assert result == Decimal(1)

    def test_negative_rate(self):
        result = compound(Decimal("-0.05"), 2)
        assert result == pytest.approx(Decimal("0.9025"), abs=1e-10)


class TestCompoundFactor:
    def test_zero_periods(self):
        assert compound_factor(Decimal("0.05"), 0) == Decimal(1)

    def test_positive_periods(self):
        result = compound_factor(Decimal("0.05"), 2)
        assert result == pytest.approx(Decimal("1.1025"), abs=1e-10)

    def test_with_mode(self):
        result = compound_factor(Decimal("0.05"), 2, mode="semi-annual")
        assert result == pytest.approx(Decimal("1.103812890625"), abs=1e-10)


class TestEffectiveAnnualRate:
    def test_semi_annual(self):
        ear = effective_annual_rate(Decimal("0.05"), 2)
        assert ear == pytest.approx(Decimal("0.050625"), abs=1e-10)

    def test_quarterly(self):
        ear = effective_annual_rate(Decimal("0.05"), 4)
        assert ear == pytest.approx(Decimal("0.050945"), abs=1e-6)

    def test_monthly(self):
        ear = effective_annual_rate(Decimal("0.05"), 12)
        assert ear == pytest.approx(Decimal("0.051162"), abs=1e-6)

    def test_zero_nominal(self):
        assert effective_annual_rate(Decimal("0"), 12) == Decimal(0)

    def test_annual(self):
        ear = effective_annual_rate(Decimal("0.10"), 1)
        assert ear == Decimal("0.10")

    def test_daily(self):
        ear = effective_annual_rate(Decimal("0.05"), 365)
        assert ear == pytest.approx(Decimal("0.051267"), abs=1e-6)


class TestNominalFromEffective:
    def test_semi_annual(self):
        nominal = nominal_from_effective(Decimal("0.050625"), 2)
        assert nominal == pytest.approx(Decimal("0.05"), abs=1e-10)

    def test_annual(self):
        nominal = nominal_from_effective(Decimal("0.10"), 1)
        assert nominal == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_invalid_effective(self):
        with pytest.raises(ValueError):
            nominal_from_effective(Decimal("-1.5"), 2)

    def test_roundtrip(self):
        ear = effective_annual_rate(Decimal("0.08"), 12)
        nominal = nominal_from_effective(ear, 12)
        assert nominal == pytest.approx(Decimal("0.08"), abs=1e-10)

    def test_zero_effective(self):
        assert nominal_from_effective(Decimal("0"), 12) == Decimal(0)


class TestContinuousEquiv:
    def test_basic(self):
        cc = continuous_equiv(Decimal("0.05"), 2)
        assert cc == pytest.approx(Decimal("0.049385"), abs=1e-6)

    def test_annual(self):
        cc = continuous_equiv(Decimal("0.10"), 1)
        assert cc == pytest.approx(Decimal("0.09531"), abs=1e-5)

    def test_zero_nominal(self):
        assert continuous_equiv(Decimal("0"), 12) == Decimal(0)


class TestDiscreteEquiv:
    def test_basic(self):
        de = discrete_equiv(Decimal("0.05"), 2)
        assert de == pytest.approx(Decimal("0.050630241"), abs=1e-4)

    def test_annual(self):
        de = discrete_equiv(Decimal("0.10"), 1)
        assert de == pytest.approx(Decimal("0.10517"), abs=1e-4)

    def test_zero_continuous(self):
        assert discrete_equiv(Decimal("0"), 12) == Decimal(0)

    def test_roundtrip_with_ear(self):
        cc = continuous_equiv(Decimal("0.08"), 4)
        ear = (Decimal(1) + Decimal("0.08") / Decimal(4)) ** Decimal(4) - Decimal(1)
        de = discrete_equiv(cc, 4)
        assert de == pytest.approx(Decimal("0.08"), abs=Decimal("1e-20"))
        assert effective_annual_rate(de, 4) == pytest.approx(ear, abs=Decimal("1e-20"))


class TestDoublingTime:
    def test_annual(self):
        dt = doubling_time(Decimal("0.05"))
        assert dt == pytest.approx(Decimal("14.2067"), abs=0.01)

    def test_continuous(self):
        dt = doubling_time(Decimal("0.05"), mode="continuous")
        assert dt == pytest.approx(Decimal("13.8629"), abs=0.01)

    def test_semi_annual(self):
        dt = doubling_time(Decimal("0.05"), mode="semi-annual")
        assert dt == pytest.approx(Decimal("14.0355"), abs=0.01)

    def test_quarterly(self):
        dt = doubling_time(Decimal("0.05"), mode="quarterly")
        assert dt == pytest.approx(Decimal("13.9494"), abs=0.01)

    def test_monthly(self):
        dt = doubling_time(Decimal("0.05"), mode="monthly")
        assert dt == pytest.approx(Decimal("13.8919"), abs=0.01)

    def test_daily(self):
        dt = doubling_time(Decimal("0.05"), mode="daily")
        assert dt == pytest.approx(Decimal("13.8629"), abs=0.01)

    def test_zero_rate(self):
        with pytest.raises(ValueError):
            doubling_time(Decimal("0"))

    def test_negative_rate(self):
        with pytest.raises(ValueError):
            doubling_time(Decimal("-0.05"))

    def test_unknown_mode(self):
        with pytest.raises(ValueError):
            doubling_time(Decimal("0.05"), mode="unknown")

    def test_high_rate(self):
        dt = doubling_time(Decimal("1.0"))
        assert dt == pytest.approx(Decimal("1.0"), abs=0.01)


class TestFutureValue:
    def test_basic(self):
        result = future_value(Decimal("100"), Decimal("0.05"), 2)
        assert result == pytest.approx(Decimal("110.25"), abs=1e-10)

    def test_zero_rate(self):
        result = future_value(Decimal("100"), Decimal("0"), 5)
        assert result == Decimal("100")

    def test_continuous(self):
        result = future_value(Decimal("100"), Decimal("0.05"), 1, mode="continuous")
        assert result == pytest.approx(Decimal("105.1271"), abs=0.01)

    def test_semi_annual(self):
        result = future_value(Decimal("100"), Decimal("0.05"), 2, mode="semi-annual")
        assert result == pytest.approx(Decimal("110.381"), abs=0.001)

    def test_negative_rate(self):
        result = future_value(Decimal("100"), Decimal("-0.05"), 2)
        assert result == pytest.approx(Decimal("90.25"), abs=1e-10)


class TestPresentValue:
    def test_basic(self):
        result = present_value(Decimal("110.25"), Decimal("0.05"), 2)
        assert result == pytest.approx(Decimal("100"), abs=1e-10)

    def test_zero_rate(self):
        result = present_value(Decimal("100"), Decimal("0"), 5)
        assert result == Decimal("100")

    def test_continuous(self):
        result = present_value(Decimal("105.1271"), Decimal("0.05"), 1, mode="continuous")
        assert result == pytest.approx(Decimal("100"), abs=0.01)


class TestGrowthRate:
    def test_basic(self):
        gr = growth_rate(Decimal("100"), Decimal("121"), 2)
        assert gr == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_negative_begin(self):
        with pytest.raises(ValueError):
            growth_rate(Decimal("-100"), Decimal("121"), 2)

    def test_zero_begin(self):
        with pytest.raises(ValueError):
            growth_rate(Decimal("0"), Decimal("121"), 2)

    def test_zero_periods(self):
        with pytest.raises(ValueError):
            growth_rate(Decimal("100"), Decimal("121"), 0)

    def test_no_growth(self):
        gr = growth_rate(Decimal("100"), Decimal("100"), 1)
        assert gr == Decimal("0")


class TestAnnualizedReturn:
    def test_basic(self):
        ar = annualized_return(Decimal("0.21"), Decimal("2"))
        assert ar == pytest.approx(Decimal("0.10"), abs=0.01)

    def test_zero_period(self):
        with pytest.raises(ValueError):
            annualized_return(Decimal("0.10"), Decimal("0"))

    def test_negative_total(self):
        with pytest.raises(ValueError):
            annualized_return(Decimal("-2"), Decimal("1"))

    def test_one_year(self):
        ar = annualized_return(Decimal("0.10"), Decimal("1"))
        assert ar == Decimal("0.10")


class TestLnExp:
    def test_ln_positive(self):
        assert ln(Decimal(2)) == pytest.approx(Decimal("0.693147"), abs=1e-6)

    def test_ln_one(self):
        assert ln(Decimal(1)) == Decimal("0")

    def test_ln_zero(self):
        with pytest.raises(ValueError):
            ln(Decimal(0))

    def test_ln_negative(self):
        with pytest.raises(ValueError):
            ln(Decimal("-1"))

    def test_exp_zero(self):
        assert exp(Decimal("0")) == Decimal("1")

    def test_exp_one(self):
        assert exp(Decimal("1")) == pytest.approx(Decimal("2.71828"), abs=1e-5)

    def test_exp_ln_roundtrip(self):
        x = Decimal("2.5")
        assert ln(exp(x)) == pytest.approx(x, abs=1e-10)


class TestRuleOf72:
    def test_basic(self):
        result = rule_of_72(Decimal("8"))
        assert result == Decimal("9")

    def test_zero_rate(self):
        with pytest.raises(ValueError):
            rule_of_72(Decimal("0"))

    def test_negative_rate(self):
        with pytest.raises(ValueError):
            rule_of_72(Decimal("-1"))

    def test_higher_rate(self):
        result = rule_of_72(Decimal("12"))
        assert result == Decimal("6")


class TestRuleOf114:
    def test_basic(self):
        result = rule_of_114(Decimal("6"))
        assert result == Decimal("19")

    def test_zero_rate(self):
        with pytest.raises(ValueError):
            rule_of_114(Decimal("0"))


class TestRuleOf144:
    def test_basic(self):
        result = rule_of_144(Decimal("6"))
        assert result == Decimal("24")

    def test_zero_rate(self):
        with pytest.raises(ValueError):
            rule_of_144(Decimal("0"))


class TestCompoundingFrequency:
    def test_annual(self):
        assert compounding_frequency("annual") == 1

    def test_semi_annual(self):
        assert compounding_frequency("semi-annual") == 2

    def test_quarterly(self):
        assert compounding_frequency("quarterly") == 4

    def test_monthly(self):
        assert compounding_frequency("monthly") == 12

    def test_weekly(self):
        assert compounding_frequency("weekly") == 52

    def test_daily(self):
        assert compounding_frequency("daily") == 365

    def test_unknown(self):
        with pytest.raises(ValueError):
            compounding_frequency("unknown")


class TestPeriodicRate:
    def test_basic(self):
        pr = periodic_rate(Decimal("0.06"), 12)
        assert pr == Decimal("0.005")

    def test_zero_rate(self):
        assert periodic_rate(Decimal("0"), 12) == Decimal(0)

    def test_monthly(self):
        pr = periodic_rate(Decimal("0.05"), 12)
        assert pr == pytest.approx(Decimal("0.0041667"), abs=1e-7)


class TestAnnualRateFromPeriodic:
    def test_basic(self):
        ar = annual_rate_from_periodic(Decimal("0.005"), 12)
        assert ar == Decimal("0.06")

    def test_zero(self):
        assert annual_rate_from_periodic(Decimal("0"), 12) == Decimal(0)

    def test_roundtrip(self):
        pr = periodic_rate(Decimal("0.08"), 4)
        ar = annual_rate_from_periodic(pr, 4)
        assert ar == Decimal("0.08")


class TestHoldingPeriodReturn:
    def test_basic(self):
        hpr = holding_period_return(Decimal("100"), Decimal("110"))
        assert hpr == Decimal("0.10")

    def test_with_dividends(self):
        hpr = holding_period_return(Decimal("100"), Decimal("110"), dividends=Decimal("5"))
        assert hpr == Decimal("0.15")

    def test_loss(self):
        hpr = holding_period_return(Decimal("100"), Decimal("90"))
        assert hpr == Decimal("-0.10")

    def test_zero_begin_price(self):
        with pytest.raises(ValueError):
            holding_period_return(Decimal("0"), Decimal("110"))


class TestRealRateOfReturn:
    def test_basic(self):
        rrr = real_rate_of_return(Decimal("0.10"), Decimal("0.03"))
        assert rrr == pytest.approx(Decimal("0.06796"), abs=1e-5)

    def test_no_inflation(self):
        rrr = real_rate_of_return(Decimal("0.10"), Decimal("0"))
        assert rrr == Decimal("0.10")


class TestForceOfInterest:
    def test_basic(self):
        foi = force_of_interest(Decimal("0.05"))
        assert foi == pytest.approx(Decimal("0.04879"), abs=1e-5)

    def test_zero(self):
        assert force_of_interest(Decimal("0")) == Decimal("0")


class TestDiscountRateFromInterest:
    def test_basic(self):
        dr = discount_rate_from_interest(Decimal("0.05"))
        assert dr == pytest.approx(Decimal("0.04762"), abs=1e-5)

    def test_zero(self):
        assert discount_rate_from_interest(Decimal("0")) == Decimal("0")


class TestInterestRateFromDiscount:
    def test_basic(self):
        ir = interest_rate_from_discount(Decimal("0.05"))
        assert ir == pytest.approx(Decimal("0.05263"), abs=1e-5)

    def test_zero(self):
        assert interest_rate_from_discount(Decimal("0")) == Decimal("0")

    def test_invalid(self):
        with pytest.raises(ValueError):
            interest_rate_from_discount(Decimal("1"))

    def test_roundtrip(self):
        dr = discount_rate_from_interest(Decimal("0.08"))
        ir = interest_rate_from_discount(dr)
        assert ir == pytest.approx(Decimal("0.08"), abs=1e-10)


@given(st.floats(min_value=0.01, max_value=0.5))
def test_compound_greater_than_one_for_positive_rate(rate):
    result = compound(Decimal(str(rate)), 1)
    assert result > Decimal(1)


@given(st.floats(min_value=1, max_value=100))
def test_doubling_time_positive(rate_pct):
    dt = doubling_time(Decimal(str(rate_pct / 100)))
    assert dt > 0


@given(st.floats(min_value=0.01, max_value=0.5), st.integers(min_value=1, max_value=12))
def test_effective_nominal_roundtrip(rate, ppy):
    ear = effective_annual_rate(Decimal(str(rate)), ppy)
    nominal = nominal_from_effective(ear, ppy)
    assert nominal == pytest.approx(Decimal(str(rate)), abs=1e-10)


@given(st.floats(min_value=1, max_value=25))
def test_rule_of_72_positive(rate_pct):
    result = rule_of_72(Decimal(str(rate_pct)))
    assert result > 0
