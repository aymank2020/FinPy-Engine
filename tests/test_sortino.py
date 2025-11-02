from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.sortino import sortino_ratio, downside_deviation
from finpy.risk.sortino import upside_potential_ratio, omega_ratio, sortino_with_target
from tests._helpers import approx_decimal


class TestSortino:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_positive_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_ratio(returns, 0.005)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            sortino_ratio([0.01], 0.0)

    def test_all_positive(self):
        returns = [0.01, 0.02, 0.03]
        result = sortino_ratio(returns, 0.0)
        assert result == Decimal(0)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_ratio(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_ratio(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_negative_returns(self):
        returns = [-0.01, -0.02, -0.01, -0.015]
        result = sortino_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_annualized_larger(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        daily = sortino_ratio(returns, 0.0)
        annual = sortino_ratio(returns, 0.0, periods_per_year=252)
        assert annual >= daily

    def test_target_return_nonzero(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_ratio(returns, 0.0, target_return=0.01)
        assert isinstance(result, Decimal)


class TestDownsideDeviation:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = downside_deviation(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            downside_deviation([0.01], 0.0)

    def test_all_positive(self):
        returns = [0.01, 0.02, 0.03, 0.04]
        result = downside_deviation(returns, 0.0)
        assert result == Decimal(0)

    def test_all_negative(self):
        returns = [-0.01, -0.02, -0.03, -0.04]
        result = downside_deviation(returns, 0.0)
        assert result > 0

    def test_with_target(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = downside_deviation(returns, target_return=0.005)
        assert isinstance(result, Decimal)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = downside_deviation(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = downside_deviation(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_nonnegative(self):
        returns = [-0.01, -0.02, 0.01, 0.03]
        result = downside_deviation(returns, 0.0)
        assert result >= 0


class TestUpsidePotentialRatio:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = upside_potential_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            upside_potential_ratio([0.01], 0.0)

    def test_all_negative(self):
        returns = [-0.01, -0.02, -0.03]
        result = upside_potential_ratio(returns, 0.0)
        assert result == Decimal(0)

    def test_all_positive(self):
        returns = [0.01, 0.02, 0.03]
        result = upside_potential_ratio(returns, 0.0)
        assert result > 0

    def test_with_target(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = upside_potential_ratio(returns, target_return=0.005)
        assert isinstance(result, Decimal)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = upside_potential_ratio(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = upside_potential_ratio(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_nonnegative(self):
        returns = [-0.01, -0.02, 0.01, 0.03]
        result = upside_potential_ratio(returns, 0.0)
        assert result >= 0


class TestOmegaRatio:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = omega_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            omega_ratio([0.01], 0.0)

    def test_all_positive(self):
        returns = [0.01, 0.02, 0.03, 0.04]
        result = omega_ratio(returns, 0.0)
        assert result > 1

    def test_all_negative(self):
        returns = [-0.01, -0.02, -0.03]
        result = omega_ratio(returns, 0.0)
        assert result <= 1

    def test_with_target(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = omega_ratio(returns, target_return=0.005)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = omega_ratio(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_mixed_returns(self):
        returns = [0.1, -0.05, 0.02, -0.03, 0.07]
        result = omega_ratio(returns, 0.0)
        assert result >= 0

    def test_one_positive_no_losses(self):
        returns = [0.01, 0.02, 0.03]
        result = omega_ratio(returns, 0.0)
        assert isinstance(result, Decimal)


class TestSortinoWithTarget:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, 0.0, 0.0, 0.05)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            sortino_with_target([0.01], 0.0, 0.0, 0.05)

    def test_high_target_downside(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, 0.0, 0.0, target_downside=0.2)
        assert isinstance(result, Decimal)

    def test_low_target_downside(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, 0.0, 0.0, target_downside=0.01)
        assert isinstance(result, Decimal)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, 0.0, 0.0, 0.05, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, 0.0, 0.0, 0.05, ndigits=4)
        assert isinstance(result, Decimal)

    def test_with_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sortino_with_target(returns, risk_free_rate=0.005, target_return=0.0, target_downside=0.05)
        assert isinstance(result, Decimal)

    def test_floor_on_downside(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        no_floor = sortino_with_target(returns, 0.0, 0.0, target_downside=0.001)
        with_floor = sortino_with_target(returns, 0.0, 0.0, target_downside=0.1)
        assert no_floor >= with_floor


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_downside_deviation_nonnegative(returns):
    assume(len(set(returns)) > 1)
    result = downside_deviation(returns, 0.0)
    assert result >= 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_upside_potential_nonnegative(returns):
    assume(len(set(returns)) > 1)
    result = upside_potential_ratio(returns, 0.0)
    assert result >= 0


@given(st.lists(st.floats(0.0, 0.05), min_size=5, max_size=30))
def test_omega_ge_one_when_all_positive(returns):
    assume(sum(returns) > 0)
    result = omega_ratio(returns, 0.0)
    assert result >= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_sortino_with_target_type(returns):
    assume(len(set(returns)) > 1)
    result = sortino_with_target(returns, 0.0, 0.0, 0.05)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_sortino_ratio_type(returns):
    assume(len(set(returns)) > 1)
    result = sortino_ratio(returns, 0.0)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_omega_ratio_type(returns):
    assume(len(set(returns)) > 1)
    result = omega_ratio(returns, 0.0)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(0.0, 0.05), min_size=5, max_size=30))
def test_downside_deviation_zero_for_positive(returns):
    result = downside_deviation(returns, 0.0)
    assert result == Decimal(0)


@given(st.lists(st.floats(-0.05, 0.0), min_size=5, max_size=30))
def test_downside_deviation_positive_for_negative(returns):
    assume(len(set(returns)) > 1)
    result = downside_deviation(returns, 0.0)
    assert result >= 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_sortino_annualized_same_sign(returns):
    assume(len(set(returns)) > 1)
    daily = sortino_ratio(returns, 0.0)
    annual = sortino_ratio(returns, 0.0, periods_per_year=252)
    assert (daily >= 0) == (annual >= 0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_upside_potential_annualized_sign(returns):
    assume(len(set(returns)) > 1)
    daily = upside_potential_ratio(returns, 0.0)
    annual = upside_potential_ratio(returns, 0.0, periods_per_year=252)
    assert (daily >= 0) == (annual >= 0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_sortino_with_target_annualized_sign(returns):
    assume(len(set(returns)) > 1)
    daily = sortino_with_target(returns, 0.0, 0.0, 0.05)
    annual = sortino_with_target(returns, 0.0, 0.0, 0.05, periods_per_year=252)
    assert (daily >= 0) == (annual >= 0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_omega_ratio_nonnegative(returns):
    assume(len(set(returns)) > 1)
    result = omega_ratio(returns, 0.0)
    assert result >= 0
