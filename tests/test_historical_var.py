from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.historical_var import historical_var, historical_cvar
from finpy.risk.historical_var import historical_var_multiple_periods, var_backtest, cvar_backtest
from finpy.risk.historical_var import expected_shortfall, marginal_var
from tests._helpers import approx_decimal


class TestHistoricalVaR:
    def test_basic(self):
        returns = [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03]
        result = historical_var(returns, 0.95)
        assert result == pytest.approx(Decimal("0.05"), abs=0.001)

    def test_empty(self):
        with pytest.raises(ValueError):
            historical_var([])

    def test_with_ndigits(self):
        returns = [-0.12345, -0.06789, -0.01, 0.02]
        result = historical_var(returns, 0.95, ndigits=3)
        assert result == Decimal("0.123")

    def test_confidence_one(self):
        returns = [-0.05, -0.03, -0.01, 0.01]
        result = historical_var(returns, 0.99)
        assert result == Decimal("0.05")

    def test_all_positive_returns(self):
        returns = [0.01, 0.02, 0.03, 0.04]
        result = historical_var(returns, 0.95)
        assert result == Decimal("0.01")

    def test_single_element(self):
        result = historical_var([0.01], 0.95)
        assert isinstance(result, Decimal)

    def test_var_reproducible(self):
        returns = [-0.1, -0.05, -0.02, 0.0, 0.03, 0.07]
        r1 = historical_var(returns, 0.95)
        r2 = historical_var(returns, 0.95)
        assert r1 == r2


class TestHistoricalCVaR:
    def test_basic(self):
        returns = [-0.05, -0.04, -0.03, -0.01, 0.02, 0.03]
        result = historical_cvar(returns, 0.95)
        assert result > 0

    def test_empty(self):
        with pytest.raises(ValueError):
            historical_cvar([])

    def test_with_ndigits(self):
        returns = [-0.12345, -0.06789, -0.01, 0.02]
        result = historical_cvar(returns, 0.95, ndigits=2)
        assert result == Decimal("0.12")

    def test_high_confidence(self):
        returns = [-0.1, -0.05, -0.02, 0.0, 0.03]
        result = historical_cvar(returns, 0.99)
        assert result > 0

    def test_cvar_not_less_than_var(self):
        returns = [-0.1, -0.05, -0.02, 0.0, 0.03, 0.07]
        var_95 = historical_var(returns, 0.95)
        cvar_95 = historical_cvar(returns, 0.95)
        assert cvar_95 >= var_95

    def test_low_confidence(self):
        returns = [-0.1, -0.05, -0.02, 0.0, 0.03]
        result = historical_cvar(returns, 0.50)
        assert result > 0


class TestHistoricalVarMultiplePeriods:
    def test_basic(self):
        returns = [-0.05, -0.03, -0.01, 0.01, 0.02, 0.03]
        result = historical_var_multiple_periods(returns, [0.95, 0.99])
        assert 0.95 in result
        assert 0.99 in result
        assert result[0.99] >= result[0.95]

    def test_empty_returns(self):
        with pytest.raises(ValueError):
            historical_var_multiple_periods([], [0.95])

    def test_empty_levels(self):
        with pytest.raises(ValueError):
            historical_var_multiple_periods([-0.1, 0.0, 0.1], [])

    def test_single_level(self):
        returns = [-0.05, -0.03, -0.01, 0.01]
        result = historical_var_multiple_periods(returns, [0.95])
        assert result[0.95] > 0

    def test_invalid_level_high(self):
        with pytest.raises(ValueError):
            historical_var_multiple_periods([-0.05, 0.01], [1.5])

    def test_invalid_level_low(self):
        with pytest.raises(ValueError):
            historical_var_multiple_periods([-0.05, 0.01], [-0.5])

    def test_with_ndigits(self):
        returns = [-0.1234, -0.0567, -0.01, 0.02]
        result = historical_var_multiple_periods(returns, [0.95], ndigits=2)
        assert result[0.95] == Decimal("0.12")

    def test_multiple_levels_ordering(self):
        returns = [-0.1, -0.08, -0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06, 0.08]
        result = historical_var_multiple_periods(returns, [0.90, 0.95, 0.99])
        assert result[0.99] >= result[0.95] >= result[0.90]


class TestVarBacktest:
    def test_basic(self):
        returns = [-0.06, -0.02, 0.01, 0.03, -0.05]
        var_est = [0.05, 0.05, 0.05, 0.05, 0.05]
        result = var_backtest(returns, var_est, 0.95)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            var_backtest([-0.05, 0.01], [0.05], 0.95)

    def test_few_observations(self):
        with pytest.raises(ValueError):
            var_backtest([-0.05], [0.05], 0.95)

    def test_zero_exceptions(self):
        returns = [0.01, 0.02, 0.03]
        var_est = [0.05, 0.05, 0.05]
        result = var_backtest(returns, var_est, 0.95)
        assert result >= 0

    def test_with_ndigits(self):
        returns = [-0.06, -0.02, 0.01]
        var_est = [0.05, 0.05, 0.05]
        result = var_backtest(returns, var_est, 0.95, ndigits=2)
        assert isinstance(result, Decimal)


class TestCvarBacktest:
    def test_basic(self):
        returns = [-0.06, -0.02, 0.01, 0.03, -0.05]
        cvar_est = [0.05, 0.05, 0.05, 0.05, 0.05]
        result = cvar_backtest(returns, cvar_est, 0.95)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            cvar_backtest([-0.05, 0.01], [0.05], 0.95)

    def test_few_observations(self):
        with pytest.raises(ValueError):
            cvar_backtest([-0.05], [0.05], 0.95)

    def test_no_exceptions(self):
        returns = [0.01, 0.02, 0.03]
        cvar_est = [0.05, 0.05, 0.05]
        result = cvar_backtest(returns, cvar_est, 0.95)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        returns = [-0.06, -0.02, 0.01]
        cvar_est = [0.05, 0.05, 0.05]
        result = cvar_backtest(returns, cvar_est, 0.95, ndigits=2)
        assert isinstance(result, Decimal)


class TestExpectedShortfall:
    def test_basic(self):
        returns = [-0.05, -0.04, -0.03, -0.01, 0.02, 0.03]
        result = expected_shortfall(returns, 0.95)
        assert result > 0

    def test_empty(self):
        with pytest.raises(ValueError):
            expected_shortfall([])

    def test_equals_cvar(self):
        returns = [-0.05, -0.04, -0.03, -0.01, 0.02]
        es = expected_shortfall(returns, 0.95)
        cvar = historical_cvar(returns, 0.95)
        assert es == cvar

    def test_with_ndigits(self):
        returns = [-0.12345, -0.06789, -0.01]
        result = expected_shortfall(returns, 0.95, ndigits=3)
        assert isinstance(result, Decimal)


class TestMarginalVaR:
    def test_basic(self):
        portfolio = [-0.05, -0.03, 0.01, 0.02, 0.03]
        asset = [-0.04, -0.02, 0.005, 0.01, 0.015]
        result = marginal_var(portfolio, asset, 0.95)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            marginal_var([-0.05, 0.01], [-0.04], 0.95)

    def test_too_short(self):
        with pytest.raises(ValueError):
            marginal_var([-0.05], [-0.04], 0.95)

    def test_zero_portfolio_variance(self):
        portfolio = [0.01, 0.01, 0.01]
        asset = [0.02, 0.02, 0.02]
        result = marginal_var(portfolio, asset, 0.95)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        portfolio = [-0.05, -0.03, 0.01, 0.02, 0.03]
        asset = [-0.04, -0.02, 0.005, 0.01, 0.015]
        result = marginal_var(portfolio, asset, 0.95, ndigits=4)
        assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=50))
def test_var_monotonic(returns):
    var95 = historical_var(returns, 0.95)
    var99 = historical_var(returns, 0.99)
    assert var99 >= var95


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=50))
def test_cvar_not_less_than_var_hypothesis(returns):
    assume(len(set(returns)) > 1)
    var95 = historical_var(returns, 0.95)
    cvar95 = historical_cvar(returns, 0.95)
    assert cvar95 >= var95


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=30))
def test_var_positive_for_negative_returns(returns):
    assume(any(r < 0 for r in returns))
    result = historical_var(returns, 0.95)
    assert result >= 0


@given(st.lists(st.floats(-0.1, 0.1), min_size=10, max_size=40))
def test_expected_shortfall_greater_than_var(returns):
    assume(any(r < 0 for r in returns))
    es = expected_shortfall(returns, 0.95)
    var = historical_var(returns, 0.95)
    assert es >= var


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_historical_var_output_type(returns):
    result = historical_var(returns, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_historical_cvar_output_type(returns):
    result = historical_cvar(returns, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_var_backtest_output_type(returns):
    var_est = [0.05] * len(returns)
    result = var_backtest(returns, var_est, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_cvar_backtest_output_type(returns):
    cvar_est = [0.05] * len(returns)
    result = cvar_backtest(returns, cvar_est, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_historical_var_multiple_output_type(returns):
    result = historical_var_multiple_periods(returns, [0.90, 0.95, 0.99])
    assert all(isinstance(v, Decimal) for v in result.values())


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_expected_shortfall_output_type(returns):
    result = expected_shortfall(returns, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_var_backtest_range(returns):
    var_est = [0.05] * len(returns)
    result = var_backtest(returns, var_est, 0.95)
    assert result >= 0


@given(st.lists(st.floats(-0.1, 0.1), min_size=5, max_size=40))
def test_cvar_backtest_range(returns):
    cvar_est = [0.05] * len(returns)
    result = cvar_backtest(returns, cvar_est, 0.95)
    assert result >= 0
