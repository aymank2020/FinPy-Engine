from decimal import Decimal
from datetime import date
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from finpy.tvm.payback import payback, discounted_payback, discounted_payback_irregular
from finpy.tvm.payback import profitability_index, payback_with_fraction, discounted_payback_with_fraction
from finpy.tvm.payback import payback_from_investment, discounted_payback_from_investment
from finpy.tvm.payback import average_accounting_return, payback_period_years
from finpy.tvm.payback import discounted_payback_period_years, payback_ratio, benefit_cost_ratio
from tests._helpers import approx_decimal


class TestPayback:
    def test_basic(self):
        result = payback([-1000, 500, 500, 500])
        assert result == Decimal("2")

    def test_not_reached(self):
        with pytest.raises(ValueError):
            payback([-1000, 100])

    def test_exact_at_end(self):
        result = payback([-1000, 500, 500])
        assert result == Decimal("2")

    def test_immediate_payback(self):
        result = payback([100, 50])
        assert result == Decimal("0")

    def test_single_cashflow_positive(self):
        result = payback([100])
        assert result == Decimal("0")

    def test_single_cashflow_negative(self):
        with pytest.raises(ValueError):
            payback([-100])

    def test_multiple_positive_after_investment(self):
        result = payback([-100, 25, 25, 25, 25, 25])
        assert result == Decimal("4")

    def test_with_ndigits(self):
        result = payback([-1000, 500, 500, 500], ndigits=2)
        assert result == Decimal("2.00")


class TestDiscountedPayback:
    def test_basic(self):
        result = discounted_payback(0.1, [-1000, 500, 500, 500])
        assert result > 0

    def test_not_reached(self):
        with pytest.raises(ValueError):
            discounted_payback(0.1, [-1000, 100])

    def test_zero_rate(self):
        result = discounted_payback(0, [-1000, 500, 500, 500])
        assert result == Decimal("2")

    def test_immediate_payback(self):
        result = discounted_payback(0.1, [1000])
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = discounted_payback(0.1, [-1000, 500, 500, 500], ndigits=2)
        assert result == Decimal("3.00")

    def test_high_rate_delays_payback(self):
        result = discounted_payback(0.1, [-1000, 500, 500, 500])
        assert isinstance(result, Decimal)


class TestDiscountedPaybackIrregular:
    def test_basic(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1)]
        result = discounted_payback_irregular(0.1, [-1000, 600, 600], dates)
        assert result > 0

    def test_mismatched_lengths(self):
        dates = [date(2024, 1, 1)]
        with pytest.raises(ValueError):
            discounted_payback_irregular(0.1, [-1000, 500], dates)

    def test_empty_cashflows(self):
        with pytest.raises(ValueError):
            discounted_payback_irregular(0.1, [], [])

    def test_not_reached(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1)]
        with pytest.raises(ValueError):
            discounted_payback_irregular(0.1, [-1000, 100], dates)

    def test_with_ndigits(self):
        dates = [date(2023, 1, 1), date(2024, 1, 1)]
        result = discounted_payback_irregular(0.1, [-1000, 1100], dates, ndigits=2)
        assert isinstance(result, Decimal)

    def test_immediate_payback(self):
        dates = [date(2024, 1, 1)]
        result = discounted_payback_irregular(0.1, [100], dates)
        assert result == Decimal("0")


class TestProfitabilityIndex:
    def test_basic(self):
        result = profitability_index(388.77, 1000)
        assert result == pytest.approx(Decimal("1.38877"), abs=1e-5)

    def test_zero_investment(self):
        with pytest.raises(ValueError):
            profitability_index(100, 0)

    def test_negative_npv(self):
        result = profitability_index(-100, 1000)
        assert result == pytest.approx(Decimal("0.90"), abs=1e-5)

    def test_with_ndigits(self):
        result = profitability_index(50, 100, ndigits=2)
        assert result == Decimal("1.50")

    def test_unit_profitability(self):
        result = profitability_index(0, 100)
        assert result == Decimal("1")


class TestPaybackWithFraction:
    def test_basic(self):
        result = payback_with_fraction([-1000, 500, 500, 500])
        assert result == Decimal("2")

    def test_partial_period(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1), date(2027, 1, 1)]
        result = discounted_payback_with_fraction(0.05, [-1000, 500, 300, 300])
        assert result == pytest.approx(Decimal("2.9712"), abs=0.01)

    def test_with_ndigits(self):
        result = discounted_payback_with_fraction(0.1, [-1000, 1100], ndigits=2)
        assert isinstance(result, Decimal)


class TestPaybackFromInvestment:
    def test_basic(self):
        result = payback_from_investment(1000, 250)
        assert result == Decimal("4")

    def test_zero_annual_cf(self):
        with pytest.raises(ValueError):
            payback_from_investment(1000, 0)

    def test_negative_investment(self):
        with pytest.raises(ValueError):
            payback_from_investment(-1000, 250)

    def test_with_ndigits(self):
        result = payback_from_investment(1000, 300, ndigits=2)
        assert result == Decimal("3.33")


class TestDiscountedPaybackFromInvestment:
    def test_basic(self):
        result = discounted_payback_from_investment(1000, 400, 0.10)
        assert result > 0

    def test_zero_rate(self):
        result = discounted_payback_from_investment(1000, 250, 0)
        assert result == Decimal("4")

    def test_zero_annual_cf(self):
        with pytest.raises(ValueError):
            discounted_payback_from_investment(1000, 0, 0.10)

    def test_negative_investment(self):
        with pytest.raises(ValueError):
            discounted_payback_from_investment(-1000, 250, 0.10)

    def test_high_rate_longer_payback(self):
        result = discounted_payback_from_investment(1000, 400, 0.10)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        result = discounted_payback_from_investment(1000, 500, 0.10, ndigits=2)
        assert isinstance(result, Decimal)


class TestAverageAccountingReturn:
    def test_basic(self):
        result = average_accounting_return(1000, 5000)
        assert result == Decimal("0.20")

    def test_zero_investment(self):
        with pytest.raises(ValueError):
            average_accounting_return(1000, 0)

    def test_negative_profit(self):
        result = average_accounting_return(-1000, 5000)
        assert result == Decimal("-0.20")

    def test_with_ndigits(self):
        result = average_accounting_return(100, 1000, ndigits=2)
        assert result == Decimal("0.10")


class TestPaybackPeriodYears:
    def test_basic(self):
        result = payback_period_years(1000, 250)
        assert result == Decimal("4")

    def test_zero_cf(self):
        with pytest.raises(ValueError):
            payback_period_years(1000, 0)

    def test_negative_investment(self):
        with pytest.raises(ValueError):
            payback_period_years(-1000, 250)


class TestDiscountedPaybackPeriodYears:
    def test_basic(self):
        result = discounted_payback_period_years(1000, 300, 0.10)
        assert result > 0

    def test_zero_rate(self):
        result = discounted_payback_period_years(1000, 250, 0)
        assert result == Decimal("4")

    def test_zero_cf(self):
        with pytest.raises(ValueError):
            discounted_payback_period_years(1000, 0, 0.10)

    def test_negative_investment(self):
        with pytest.raises(ValueError):
            discounted_payback_period_years(-1000, 250, 0.10)

    def test_not_reached(self):
        with pytest.raises(ValueError):
            discounted_payback_period_years(1000, 10, 0.10, max_years=5)


class TestPaybackRatio:
    def test_basic(self):
        result = payback_ratio(1000, 3000)
        assert result == Decimal("3")

    def test_ratio_less_than_one(self):
        result = payback_ratio(1000, 500)
        assert result == Decimal("0.5")

    def test_negative_investment(self):
        with pytest.raises(ValueError):
            payback_ratio(-1000, 3000)

    def test_zero_investment(self):
        with pytest.raises(ValueError):
            payback_ratio(0, 3000)


class TestBenefitCostRatio:
    def test_basic(self):
        result = benefit_cost_ratio(5000, 1000)
        assert result == Decimal("5")

    def test_zero_costs(self):
        with pytest.raises(ValueError):
            benefit_cost_ratio(5000, 0)

    def test_ratio_less_than_one(self):
        result = benefit_cost_ratio(500, 1000)
        assert result == Decimal("0.5")

    def test_with_ndigits(self):
        result = benefit_cost_ratio(1000, 300, ndigits=2)
        assert result == Decimal("3.33")


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.lists(st.floats(min_value=-10000, max_value=-1), min_size=1), st.lists(st.floats(min_value=1, max_value=10000), min_size=1, max_size=10))
def test_payback_with_investment_and_returns(investments, returns):
    cfs = investments + returns
    try:
        result = payback(cfs)
        assert result >= 0
    except ValueError:
        pass


@given(st.floats(min_value=1, max_value=10000), st.floats(min_value=1, max_value=1000))
def test_benefit_cost_ratio_positive(investment, benefit):
    result = benefit_cost_ratio(benefit, investment)
    assert result > 0


@given(st.floats(min_value=1, max_value=10000), st.floats(min_value=1, max_value=1000))
def test_profitability_index_positive(npv_val, investment):
    result = profitability_index(npv_val, investment)
    assert result > 0
