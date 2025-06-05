from decimal import Decimal
from datetime import date
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from finpy.tvm.irr import irr, xirr, modified_irr_with_reinvestment, irr_with_bisection
from finpy.tvm.irr import multiple_irr_check, irr_npv_profile, irr_approximate, irr_annual
from finpy.tvm.irr import irr_semi_annual, irr_monthly
from finpy.tvm.npv import npv
from finpy.core.errors import NoSolutionFoundError
from tests._helpers import approx_decimal


class TestIRR:
    def test_basic(self):
        result = irr([-1000, 300, 400, 500, 600])
        assert result == pytest.approx(Decimal("0.2438"), abs=0.01)

    def test_no_convergence(self):
        with pytest.raises(NoSolutionFoundError):
            irr([-1000, 100, 100], max_iter=5)

    def test_simple_project(self):
        result = irr([-100, 110])
        assert result == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_zero_cashflows_returns_guess(self):
        result = irr([0, 0, 0])
        assert result == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_all_negative(self):
        with pytest.raises(NoSolutionFoundError):
            irr([-100, -50, -25])

    def test_all_positive(self):
        with pytest.raises(NoSolutionFoundError):
            irr([100, 50, 25])

    def test_custom_guess(self):
        result = irr([-1000, 300, 400, 500, 600], guess=0.5)
        assert result == pytest.approx(Decimal("0.2438"), abs=0.01)

    def test_high_irr(self):
        result = irr([-100, 200])
        assert result == pytest.approx(Decimal("1.0"), abs=1e-10)

    def test_with_ndigits(self):
        result = irr([-100, 110], ndigits=4)
        assert result == Decimal("0.1000")

    def test_longer_cashflows(self):
        result = irr([-10000, 2000, 2000, 2000, 2000, 2000])
        assert result == pytest.approx(Decimal("0.0"), abs=0.01)

    def test_irr_roundtrip(self):
        cfs = [-1000, 300, 400, 500, 600]
        r = irr(cfs)
        npv_val = npv(float(r), cfs)
        assert abs(npv_val) < Decimal("0.01")


class TestXirr:
    def test_basic(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1)]
        result = xirr([-1000, 500, 600], dates)
        assert result == pytest.approx(Decimal("0.05"), abs=0.02)

    def test_mismatched_lengths(self):
        dates = [date(2024, 1, 1)]
        with pytest.raises(ValueError):
            xirr([-1000, 500], dates)

    def test_less_than_two_flows(self):
        dates = [date(2024, 1, 1)]
        with pytest.raises(ValueError):
            xirr([-100], dates)

    def test_all_positive(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1)]
        with pytest.raises(ValueError):
            xirr([100, 200], dates)

    def test_all_negative(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1)]
        with pytest.raises(ValueError):
            xirr([-100, -200], dates)

    def test_same_year_non_leap(self):
        dates = [date(2023, 1, 1), date(2023, 6, 1)]
        result = xirr([-100, 110], dates)
        assert abs(result - Decimal("0.10")) < Decimal("0.20")

    def test_with_ndigits(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1)]
        result = xirr([-100, 110], dates, ndigits=4)
        assert result > 0


class TestModifiedIrrWithReinvestment:
    def test_basic(self):
        result = modified_irr_with_reinvestment([-1000, 300, 400, 500, 600], 0.05, 0.05)
        assert result == pytest.approx(Decimal("0.1778"), abs=0.01)

    def test_different_rates(self):
        result = modified_irr_with_reinvestment([-1000, 300, 400, 500, 600], 0.06, 0.04)
        assert result > 0

    def test_less_than_two_cashflows(self):
        with pytest.raises(ValueError):
            modified_irr_with_reinvestment([-100], 0.05, 0.05)

    def test_no_negative_flows(self):
        with pytest.raises(ValueError):
            modified_irr_with_reinvestment([100, 200], 0.05, 0.05)

    def test_no_positive_flows(self):
        with pytest.raises(ValueError):
            modified_irr_with_reinvestment([-100, -200], 0.05, 0.05)

    def test_single_negative_then_positives(self):
        result = modified_irr_with_reinvestment([-100, 110], 0.05, 0.05)
        assert result > 0

    def test_with_ndigits(self):
        result = modified_irr_with_reinvestment([-100, 110], 0.05, 0.05, ndigits=4)
        assert isinstance(result, Decimal)


class TestIrrWithBisection:
    def test_basic(self):
        result = irr_with_bisection([-1000, 300, 400, 500, 600], low=0, high=2.0)
        assert result == pytest.approx(Decimal("0.2438"), abs=0.01)

    def test_simple(self):
        result = irr_with_bisection([-100, 110], low=0, high=1.0)
        assert result == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_no_convergence(self):
        with pytest.raises(NoSolutionFoundError):
            irr_with_bisection([-100, 100, 100], low=0, high=1, max_iter=5)

    def test_custom_bracket(self):
        result = irr_with_bisection([-100, 110], low=-0.5, high=2.0)
        assert result == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_with_ndigits(self):
        result = irr_with_bisection([-100, 110], low=0, high=1.0, ndigits=4)
        assert result == Decimal("0.1000")


class TestMultipleIrrCheck:
    def test_single_result(self):
        results = multiple_irr_check([-100, 110])
        assert len(results) >= 1

    def test_no_results(self):
        with pytest.raises(NoSolutionFoundError):
            multiple_irr_check([100, 200])

    def test_custom_guesses(self):
        results = multiple_irr_check([-1000, 300, 400, 500, 600], guesses=[0.05, 0.10, 0.20])
        assert len(results) >= 1

    def test_multiple_results_project(self):
        results = multiple_irr_check([-100, 230, -132])
        assert len(results) >= 1

    def test_with_ndigits(self):
        results = multiple_irr_check([-100, 110], ndigits=4)
        assert len(results) >= 1


class TestIrrNpvProfile:
    def test_basic(self):
        profile = irr_npv_profile([-1000, 300, 400, 500, 600])
        assert len(profile) == 101
        assert profile[0][0] == pytest.approx(Decimal("-0.5"), abs=0.01)
        assert profile[-1][0] == pytest.approx(Decimal("5.0"), abs=0.01)

    def test_custom_range(self):
        profile = irr_npv_profile([-100, 110], low_rate=0, high_rate=1.0, steps=10)
        assert len(profile) == 11

    def test_npv_sign_change(self):
        profile = irr_npv_profile([-100, 110])
        assert profile[0][1] > 0
        assert profile[-1][1] < 0

    def test_with_ndigits(self):
        profile = irr_npv_profile([-100, 110], steps=5, ndigits=2)
        assert profile[0][0] == Decimal("-0.50")


class TestIrrApproximate:
    def test_basic(self):
        result = irr_approximate([-1000, 300, 400, 500, 600])
        assert result > 0

    def test_all_positive(self):
        result = irr_approximate([100, 200])
        assert result == Decimal(0)

    def test_all_negative(self):
        result = irr_approximate([-100, -200])
        assert result == Decimal(0)

    def test_no_outflow(self):
        result = irr_approximate([100, 200])
        assert result == Decimal(0)

    def test_no_inflow(self):
        result = irr_approximate([-100, -200])
        assert result == Decimal(0)


class TestIrrAnnual:
    def test_basic(self):
        result = irr_annual([-100, 110])
        assert result == pytest.approx(Decimal("0.10"), abs=1e-10)

    def test_same_as_irr(self):
        cfs = [-1000, 300, 400, 500, 600]
        assert irr_annual(cfs) == irr(cfs)


class TestIrrSemiAnnual:
    def test_basic(self):
        result = irr_semi_annual([-100, 110])
        assert result > irr([-100, 110])

    def test_positive_rate(self):
        result = irr_semi_annual([-50, 60])
        assert result > 0


class TestIrrMonthly:
    def test_basic(self):
        result = irr_monthly([-100, 110])
        assert result > irr([-100, 110])

    def test_positive_rate(self):
        result = irr_monthly([-50, 60])
        assert result > 0


@given(st.lists(st.floats(min_value=-1000, max_value=1000), min_size=3, max_size=10))
def test_irr_roundtrip(cfs):
    try:
        r = irr(cfs)
        npv_val = npv(float(r), cfs)
        assert abs(npv_val) < Decimal("0.01")
    except (NoSolutionFoundError, ValueError):
        pass


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.lists(st.floats(min_value=-1000, max_value=-1), min_size=1).flatmap(lambda neg: st.lists(st.floats(min_value=1, max_value=1000), min_size=2, max_size=7).map(lambda pos: neg + pos)))
def test_irr_bisection_roundtrip(cfs):
    try:
        r = irr_with_bisection(cfs, low=-0.5, high=5.0)
        npv_val = npv(float(r), cfs)
        assert abs(npv_val) < Decimal("0.2")
    except (NoSolutionFoundError, ValueError):
        pass
