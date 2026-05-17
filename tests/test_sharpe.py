from decimal import Decimal
import math
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.sharpe import sharpe_ratio, adjusted_sharpe
from finpy.risk.sharpe import probabilistic_sharpe, deflated_sharpe_ratio
from tests._helpers import approx_decimal


class TestSharpe:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sharpe_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_positive_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sharpe_ratio(returns, 0.005)
        assert isinstance(result, Decimal)

    def test_negative_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sharpe_ratio(returns, -0.005)
        assert isinstance(result, Decimal)

    def test_short_series(self):
        with pytest.raises(ValueError):
            sharpe_ratio([0.01])

    def test_zero_risk_free_and_constant(self):
        returns = [0.01, 0.01, 0.01]
        result = sharpe_ratio(returns, 0.0)
        assert result == Decimal(0)

    def test_with_periods_per_year(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sharpe_ratio(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = sharpe_ratio(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_annualized_larger_than_daily(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        daily = sharpe_ratio(returns, 0.0)
        annual = sharpe_ratio(returns, 0.0, periods_per_year=252)
        assert annual >= daily

    def test_negative_sharpe(self):
        returns = [-0.01, -0.02, -0.01, -0.015]
        result = sharpe_ratio(returns, 0.0)
        assert result < 0

    def test_zero_variance(self):
        returns = [0.01, 0.01, 0.01, 0.01]
        result = sharpe_ratio(returns, 0.0)
        assert result == Decimal(0)

    def test_ndigits_rounding(self):
        returns = [0.01111, 0.02222, -0.01111]
        result = sharpe_ratio(returns, 0.0, ndigits=3)
        assert isinstance(result, Decimal)


class TestAdjustedSharpe:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = adjusted_sharpe(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            adjusted_sharpe([0.01, 0.02], 0.0)

    def test_zero_variance(self):
        returns = [0.01, 0.01, 0.01, 0.01, 0.01]
        result = adjusted_sharpe(returns, 0.0)
        assert result == Decimal(0)

    def test_with_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = adjusted_sharpe(returns, 0.005)
        assert isinstance(result, Decimal)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = adjusted_sharpe(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = adjusted_sharpe(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_negative_returns(self):
        returns = [-0.01, -0.02, -0.01, -0.015, -0.03, -0.02, -0.01]
        result = adjusted_sharpe(returns, 0.0)
        assert isinstance(result, Decimal)

    def diff_from_sharpe(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        sr = sharpe_ratio(returns, 0.0)
        asr = adjusted_sharpe(returns, 0.0)
        assert asr != sr


class TestProbabilisticSharpe:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = probabilistic_sharpe(returns, 0.0)
        assert 0 <= result <= 1

    def test_too_short(self):
        with pytest.raises(ValueError):
            probabilistic_sharpe([0.01, 0.02], 0.0)

    def test_target_sharpe_positive(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = probabilistic_sharpe(returns, 0.0, target_sharpe=0.5)
        assert 0 <= result <= 1

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = probabilistic_sharpe(returns, 0.0, periods_per_year=252)
        assert 0 <= result <= 1

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = probabilistic_sharpe(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_high_target_prob_zero(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = probabilistic_sharpe(returns, 0.0, target_sharpe=10.0)
        assert 0 <= result <= 1

    def test_zero_variance(self):
        returns = [0.01, 0.01, 0.01, 0.01, 0.01]
        result = probabilistic_sharpe(returns, 0.0, target_sharpe=0.0)
        assert 0 <= result <= 1


@pytest.mark.skipif(not hasattr(math, 'euler_gamma'), reason="requires math.euler_gamma")
class TestDeflatedSharpeRatio:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        result = deflated_sharpe_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            deflated_sharpe_ratio([0.01, 0.02, 0.03], 0.0)

    def test_invalid_num_trials(self):
        with pytest.raises(ValueError):
            deflated_sharpe_ratio([0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01], 0.0, num_trials=0)

    def test_multiple_trials(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        result = deflated_sharpe_ratio(returns, 0.0, num_trials=100)
        assert isinstance(result, Decimal)

    def test_with_risk_free(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        result = deflated_sharpe_ratio(returns, 0.005)
        assert isinstance(result, Decimal)

    def test_with_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        result = deflated_sharpe_ratio(returns, 0.0, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        result = deflated_sharpe_ratio(returns, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_nonpositive_negative_returns(self):
        returns = [-0.01, -0.02, -0.01, -0.015, -0.03, -0.02, -0.01, -0.005]
        result = deflated_sharpe_ratio(returns, 0.0)
        assert isinstance(result, Decimal)

    def test_single_trial(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.01]
        single = deflated_sharpe_ratio(returns, 0.0, num_trials=1)
        multi = deflated_sharpe_ratio(returns, 0.0, num_trials=10)
        assert single >= multi


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_sharpe_scale_invariance(returns):
    assume(len(set(returns)) > 1)
    sr = sharpe_ratio(returns)
    sr_scaled = sharpe_ratio([r * 2 for r in returns])
    assert abs(float(sr) - float(sr_scaled)) < 0.001


@given(st.lists(st.floats(0.001, 0.05), min_size=10, max_size=40))
def test_sharpe_positive_for_positive_returns(returns):
    assume(len(set(returns)) > 1)
    result = sharpe_ratio(returns, 0.0)
    assert result > 0


@given(st.lists(st.floats(-0.05, -0.001), min_size=10, max_size=40))
def test_sharpe_negative_for_negative_returns(returns):
    assume(len(set(returns)) > 1)
    result = sharpe_ratio(returns, 0.0)
    assert result < 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_probabilistic_sharpe_range(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    prob = probabilistic_sharpe(returns, 0.0)
    assert 0 <= prob <= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_adjusted_sharpe_type(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = adjusted_sharpe(returns, 0.0)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_sharpe_ratio_type(returns):
    assume(len(set(returns)) > 1)
    result = sharpe_ratio(returns, 0.0)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_sharpe_with_risk_free_type(returns):
    assume(len(set(returns)) > 1)
    result = sharpe_ratio(returns, 0.005)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_adjusted_sharpe_positive_risk_free(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = adjusted_sharpe(returns, 0.005)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_probabilistic_sharpe_positive_rf(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-10)
    prob = probabilistic_sharpe(returns, 0.005)
    assert 0 <= prob <= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_sharpe_annualized_vs_daily(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    daily = sharpe_ratio(returns, 0.0)
    annual = sharpe_ratio(returns, 0.0, periods_per_year=252)
    assert abs(float(annual)) >= abs(float(daily))


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_sharpe_without_rf_ge_with_rf(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    sr0 = sharpe_ratio(returns, 0.0)
    sr_pos = sharpe_ratio(returns, 0.01)
    assert sr0 >= sr_pos


@given(st.lists(st.floats(-0.05, 0.05), min_size=8, max_size=30))
def test_sharpe_negative_when_returns_below_rf(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    rf = mean + 0.01
    result = sharpe_ratio(returns, rf)
    assert result <= 0
