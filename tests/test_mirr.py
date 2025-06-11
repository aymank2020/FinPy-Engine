from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from finpy.tvm.mirr import mirr, mirr_with_terminal_growth, mirr_from_separate_cashflows
from finpy.tvm.mirr import mirr_with_periodic_rates, mirr_with_investment_timing
from tests._helpers import approx_decimal


class TestMIRR:
    def test_basic(self):
        result = mirr([-1000, 300, 400, 500, 600], 0.05, 0.05)
        assert result > 0

    def test_known_value(self):
        result = mirr([-1000, 300, 400, 500, 600], 0.10, 0.10)
        assert result == pytest.approx(Decimal("0.1941"), abs=0.01)

    def test_simple_project(self):
        result = mirr([-100, 110], 0.05, 0.05)
        assert result > 0

    def test_less_than_two_cashflows(self):
        with pytest.raises(ValueError):
            mirr([-100], 0.05, 0.05)

    def test_all_negative(self):
        with pytest.raises(ValueError):
            mirr([-100, -200], 0.05, 0.05)

    def test_all_positive(self):
        with pytest.raises(ValueError):
            mirr([100, 200], 0.05, 0.05)

    def test_finance_rate_below_minus_one(self):
        with pytest.raises(ValueError):
            mirr([-100, 110], -1.5, 0.05)

    def test_reinvest_rate_below_minus_one(self):
        with pytest.raises(ValueError):
            mirr([-100, 110], 0.05, -1.5)

    def test_no_negative_flows(self):
        with pytest.raises(ValueError):
            mirr([100, 200, 300], 0.05, 0.05)

    def test_with_ndigits(self):
        result = mirr([-1000, 300, 400, 500, 600], 0.05, 0.05, ndigits=4)
        assert isinstance(result, Decimal)

    def test_different_finance_and_reinvest(self):
        result = mirr([-1000, 300, 400, 500, 600], 0.08, 0.04)
        assert result > 0

    def test_multi_period(self):
        result = mirr([-500, 100, 100, 100, 100, 100], 0.05, 0.05)
        assert result > 0

    def test_large_initial_outflow(self):
        result = mirr([-10000, 2000, 3000, 4000], 0.06, 0.06)
        assert isinstance(result, Decimal)


class TestMIRRWithTerminalGrowth:
    def test_basic(self):
        result = mirr_with_terminal_growth([-1000, 300, 400, 500, 600], 0.05, 0.05, 0.02)
        assert result > 0

    def test_zero_growth(self):
        result = mirr_with_terminal_growth([-1000, 300, 400], 0.05, 0.05, 0.0)
        base = mirr([-1000, 300, 400], 0.05, 0.05)
        assert result == base

    def test_less_than_two_cashflows(self):
        with pytest.raises(ValueError):
            mirr_with_terminal_growth([-100], 0.05, 0.05, 0.02)

    def test_no_negative_flows(self):
        with pytest.raises(ValueError):
            mirr_with_terminal_growth([100, 200], 0.05, 0.05, 0.02)

    def test_with_ndigits(self):
        result = mirr_with_terminal_growth([-1000, 300, 400], 0.05, 0.05, 0.02, ndigits=4)
        assert isinstance(result, Decimal)

    def test_negative_terminal_growth(self):
        result = mirr_with_terminal_growth([-1000, 300, 400], 0.05, 0.05, -0.01)
        assert isinstance(result, Decimal)


class TestMIRRFromSeparateCashflows:
    def test_basic(self):
        result = mirr_from_separate_cashflows([110, 120], [-100, -50], 0.05, 0.05)
        assert result > 0

    def test_single_positive_negative(self):
        result = mirr_from_separate_cashflows([110], [-100], 0.05, 0.05)
        assert result > 0

    def test_empty_positive(self):
        with pytest.raises(ValueError):
            mirr_from_separate_cashflows([], [-100], 0.05, 0.05)

    def test_empty_negative(self):
        with pytest.raises(ValueError):
            mirr_from_separate_cashflows([100], [], 0.05, 0.05)

    def test_different_lengths(self):
        result = mirr_from_separate_cashflows([110, 120, 130], [-100], 0.05, 0.05)
        assert result > 0

    def test_with_ndigits(self):
        result = mirr_from_separate_cashflows([110], [-100], 0.05, 0.05, ndigits=4)
        assert isinstance(result, Decimal)

    def test_larger_numbers(self):
        result = mirr_from_separate_cashflows([1000, 2000], [-500, -500], 0.06, 0.04)
        assert result > 0


class TestMIRRWithPeriodicRates:
    def test_basic(self):
        result = mirr_with_periodic_rates([-1000, 300, 400, 500, 600], 0.05, 0.05, payments_per_year=1)
        assert result > 0

    def test_semi_annual(self):
        result = mirr_with_periodic_rates([-1000, 300, 400, 500, 600], 0.05, 0.05, payments_per_year=2)
        assert result > 0

    def test_monthly(self):
        result = mirr_with_periodic_rates([-1000, 300, 400, 500, 600], 0.05, 0.05, payments_per_year=12)
        assert result > 0

    def test_invalid_payments_per_year(self):
        with pytest.raises(ValueError):
            mirr_with_periodic_rates([-100, 110], 0.05, 0.05, payments_per_year=0)

    def test_with_ndigits(self):
        result = mirr_with_periodic_rates([-100, 110], 0.05, 0.05, payments_per_year=1, ndigits=4)
        assert isinstance(result, Decimal)


class TestMIRRWithInvestmentTiming:
    def test_basic(self):
        result = mirr_with_investment_timing([-1000, 300, 400, 500, 600], 0.05, 0.05, [0.0, 1.0, 2.0, 3.0, 4.0])
        assert result > 0

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            mirr_with_investment_timing([-1000, 300], 0.05, 0.05, [0.0])

    def test_less_than_two_cashflows(self):
        with pytest.raises(ValueError):
            mirr_with_investment_timing([-100], 0.05, 0.05, [0.0])

    def test_irregular_timing(self):
        result = mirr_with_investment_timing([-1000, 200, 300, 400], 0.05, 0.05, [0.0, 0.5, 1.5, 3.0])
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        result = mirr_with_investment_timing([-100, 110], 0.05, 0.05, [0.0, 1.0], ndigits=4)
        assert isinstance(result, Decimal)

    def test_no_negative_flows(self):
        with pytest.raises(ValueError):
            mirr_with_investment_timing([100, 200], 0.05, 0.05, [0.0, 1.0])

    def test_all_investment_at_time_zero(self):
        result = mirr_with_investment_timing([-100, 50, 60], 0.05, 0.05, [0.0, 1.0, 2.0])
        assert result > 0


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.lists(st.floats(min_value=-1000, max_value=-1), min_size=1).flatmap(lambda neg: st.lists(st.floats(min_value=1, max_value=1000), min_size=2, max_size=7).map(lambda pos: neg + pos)))
def test_mirr_is_finite(cfs):
    try:
        result = mirr(cfs, 0.05, 0.05)
        assert isinstance(result, Decimal)
    except ValueError:
        pass


@given(st.floats(min_value=0.01, max_value=0.2), st.floats(min_value=0.01, max_value=0.2))
def test_mirr_monotonic_with_rate(finance, reinvest):
    cfs = [-1000, 200, 300, 400, 500]
    result = mirr(cfs, finance, reinvest)
    assert isinstance(result, Decimal)
