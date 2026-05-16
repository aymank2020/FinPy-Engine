from decimal import Decimal
from datetime import date
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from finpy.tvm.npv import npv, npv_series, npv_with_terminal_value, xnpv, npv_perpetuity
from finpy.tvm.npv import npv_at_date, npv_profile, npv_annual, npv_semi_annual, npv_continuous
from finpy.tvm.npv import npv_perpetuity_constant, npv_from_discount_factors, npv_series_with_terminal
from tests._helpers import approx_decimal


class TestNPV:
    def test_basic(self):
        result = npv(0.1, [-1000, 300, 400, 500, 600])
        assert result == pytest.approx(Decimal("388.77"), abs=0.01)

    def test_empty(self):
        assert npv(0.1, []) == Decimal(0)

    def test_single_positive(self):
        result = npv(0.1, [100])
        assert result == Decimal("100")

    def test_single_negative(self):
        result = npv(0.1, [-100])
        assert result == Decimal("-100")

    def test_zero_rate(self):
        result = npv(0, [-100, 50, 50, 50])
        assert result == Decimal("50")

    def test_negative_rate(self):
        result = npv(-0.1, [-100, 50, 60])
        assert result > 0

    def test_all_positive(self):
        result = npv(0.1, [100, 200, 300])
        assert result > 0

    def test_all_negative(self):
        result = npv(0.1, [-100, -200, -300])
        assert result < 0

    def test_with_ndigits(self):
        result = npv(0.1, [-1000, 300, 400, 500, 600], ndigits=2)
        assert result == Decimal("388.77")


class TestNpvSeries:
    def test_basic(self):
        result = npv_series(0.1, [-1000, 300, 400, 500, 600])
        assert len(result) == 5
        assert result[0] == pytest.approx(Decimal("-1000"), abs=0.01)
        assert result[-1] == pytest.approx(Decimal("388.77"), abs=0.01)

    def test_empty(self):
        assert npv_series(0.1, []) == []

    def test_with_ndigits(self):
        result = npv_series(0.1, [-1000, 300], ndigits=2)
        assert result[1] == Decimal("-727.27")


class TestNpvWithTerminalValue:
    def test_basic(self):
        result = npv_with_terminal_value(0.1, [-1000, 100, 200, 300], 500)
        assert isinstance(result, Decimal)

    def test_with_terminal_growth(self):
        result = npv_with_terminal_value(0.1, [-1000, 100, 200], 500, terminal_growth_rate=0.03)
        assert isinstance(result, Decimal)

    def test_single_cashflow(self):
        result = npv_with_terminal_value(0.1, [100], 500)
        assert result == Decimal("600")

    def test_zero_rate(self):
        result = npv_with_terminal_value(0, [-100, 50, 50], 100)
        assert result == Decimal("100")

    def test_with_ndigits(self):
        result = npv_with_terminal_value(0.1, [-1000, 200, 300], 500, ndigits=2)
        assert result == Decimal("-157.02")


class TestXnpv:
    def test_basic(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1), date(2026, 1, 1)]
        result = xnpv(0.1, [-1000, 500, 600], dates)
        assert result == pytest.approx(Decimal("-49.83"), abs=0.01)

    def test_mismatched_lengths(self):
        dates = [date(2024, 1, 1)]
        with pytest.raises(ValueError):
            xnpv(0.1, [-1000, 500], dates)

    def test_empty_cashflows(self):
        with pytest.raises(ValueError):
            xnpv(0.1, [], [])

    def test_same_year(self):
        dates = [date(2024, 1, 1), date(2024, 6, 1)]
        result = xnpv(0.1, [-100, 110], dates)
        assert result > Decimal("0")

    def test_with_ndigits(self):
        dates = [date(2024, 1, 1), date(2025, 1, 1)]
        result = xnpv(0.1, [-1000, 1000], dates, ndigits=2)
        assert isinstance(result, Decimal)


class TestNpvPerpetuity:
    def test_basic(self):
        result = npv_perpetuity(0.10, [100, 200, 300], 0.03)
        assert result > 0

    def test_no_growth(self):
        result = npv_perpetuity(0.10, [100, 200, 300], 0.0)
        assert result > 0

    def test_single_cashflow(self):
        result = npv_perpetuity(0.10, [100], 0.03)
        assert result > 0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            npv_perpetuity(0.10, [])

    def test_rate_less_than_growth_raises(self):
        with pytest.raises(ValueError):
            npv_perpetuity(0.03, [100], 0.05)

    def test_with_ndigits(self):
        result = npv_perpetuity(0.10, [100, 200], 0.03, ndigits=2)
        assert result > 0


class TestNpvAtDate:
    def test_basic(self):
        result = npv_at_date(0.1, [-1000, 300, 400, 500, 600], target_date=2)
        assert result > 0

    def test_target_date_zero(self):
        result = npv_at_date(0.1, [-1000, 300, 400], target_date=0)
        assert result != 0

    def test_empty(self):
        assert npv_at_date(0.1, [], target_date=0) == Decimal(0)

    def test_with_ndigits(self):
        result = npv_at_date(0.1, [-1000, 300, 400], target_date=1, ndigits=2)
        assert isinstance(result, Decimal)


class TestNpvProfile:
    def test_basic(self):
        result = npv_profile([-1000, 300, 400, 500], [0.05, 0.10, 0.15])
        assert len(result) == 3
        assert result[0] > result[1] > result[2]

    def test_single_rate(self):
        result = npv_profile([-100, 110], [0.10])
        assert len(result) == 1

    def test_empty_rates(self):
        result = npv_profile([-100, 110], [])
        assert result == []

    def test_with_ndigits(self):
        result = npv_profile([-100, 110], [0.10], ndigits=2)
        assert result[0] == Decimal("0.00")


class TestNpvAnnual:
    def test_basic(self):
        result = npv_annual(0.1, [-1000, 500, 600])
        assert result == npv(0.1, [-1000, 500, 600])

    def test_empty(self):
        assert npv_annual(0.1, []) == Decimal(0)


class TestNpvSemiAnnual:
    def test_basic(self):
        result = npv_semi_annual(0.1, [-1000, 500, 600])
        assert result > 0

    def test_empty(self):
        assert npv_semi_annual(0.1, []) == Decimal(0)

    def test_different_from_annual(self):
        annual = npv_annual(0.10, [-100, 110])
        semi = npv_semi_annual(0.10, [-100, 110])
        assert semi != annual

    def test_zero_rate(self):
        result = npv_semi_annual(0, [-100, 110])
        assert result == Decimal("10")


class TestNpvContinuous:
    def test_basic(self):
        result = npv_continuous(0.1, [-1000, 500, 600], [0.0, 1.0, 2.0])
        assert result == pytest.approx(Decimal("-56.34"), abs=0.01)

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            npv_continuous(0.1, [-1000, 500], [0.0])

    def test_empty(self):
        result = npv_continuous(0.1, [], [])
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = npv_continuous(0.1, [-1000, 1100], [0.0, 1.0], ndigits=2)
        assert isinstance(result, Decimal)


class TestNpvPerpetuityConstant:
    def test_basic(self):
        result = npv_perpetuity_constant(100, 0.05)
        assert result == Decimal("2000")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            npv_perpetuity_constant(100, 0)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            npv_perpetuity_constant(100, -0.05)

    def test_with_ndigits(self):
        result = npv_perpetuity_constant(100, 0.05, ndigits=2)
        assert result == Decimal("2000.00")


class TestNpvFromDiscountFactors:
    def test_basic(self):
        result = npv_from_discount_factors([100, 200, 300], [0.95, 0.90, 0.85])
        assert result == Decimal("95") + Decimal("180") + Decimal("255")

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            npv_from_discount_factors([100, 200], [0.95])

    def test_empty(self):
        result = npv_from_discount_factors([], [])
        assert result == Decimal("0")

    def test_with_ndigits(self):
        result = npv_from_discount_factors([100, 200], [0.95, 0.90], ndigits=2)
        assert result == Decimal("275.00")


class TestNpvSeriesWithTerminal:
    def test_basic(self):
        result = npv_series_with_terminal(0.1, [-1000, 200, 300], 500)
        assert len(result) == 3
        assert len(result) == 3

    def test_empty(self):
        result = npv_series_with_terminal(0.1, [], 500)
        assert result == []

    def test_with_ndigits(self):
        result = npv_series_with_terminal(0.1, [-1000, 200], 500, ndigits=2)
        assert result[-1] == Decimal("-363.64")


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.lists(st.floats(min_value=1, max_value=1000), min_size=2, max_size=10))
def test_npv_of_all_positive_is_positive(cfs):
    result = npv(0.05, cfs)
    assert result > 0


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.lists(st.floats(min_value=-1000, max_value=-1), min_size=2, max_size=10))
def test_npv_of_all_negative_is_negative(cfs):
    result = npv(0.05, cfs)
    assert result < 0


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(st.floats(min_value=0.01, max_value=0.5), st.lists(st.floats(min_value=1, max_value=1000), min_size=2, max_size=10))
def test_npv_monotonic(rate, cfs):
    npv1 = npv(rate, cfs)
    npv2 = npv(rate * 2, cfs)
    assert npv1 >= npv2


@given(st.lists(st.floats(min_value=-1000, max_value=1000), min_size=1, max_size=5))
def test_npv_zero_rate_is_sum(cfs):
    total = sum(Decimal(str(cf)) for cf in cfs)
    assert npv(0, cfs) == total
