from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.returns.autocorrelation import autocorrelation, autocorrelation_matrix
from finpy.returns.autocorrelation import ljung_box_statistic, partial_autocorrelation
from tests._helpers import approx_decimal


class TestAutocorrelation:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = autocorrelation(returns, 1)
        assert isinstance(result, Decimal)

    def test_lag_two(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01]
        result = autocorrelation(returns, 2)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            autocorrelation([0.01, 0.02], 3)

    def test_lag_zero(self):
        returns = [0.01, 0.02, -0.01, 0.015]
        result = autocorrelation(returns, 0)
        assert result == Decimal(1)

    def test_white_noise(self):
        returns = [0.01, -0.01, 0.01, -0.01, 0.01, -0.01]
        result = autocorrelation(returns, 1)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = autocorrelation(returns, 1, ndigits=4)
        assert isinstance(result, Decimal)

    def test_bounds(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03]
        result = autocorrelation(returns, 1)
        assert -1 <= result <= 1

    def test_constant_returns(self):
        returns = [0.01, 0.01, 0.01, 0.01]
        result = autocorrelation(returns, 1)
        assert result == Decimal(0)

    def test_zero_variance(self):
        returns = [0.0, 0.0, 0.0, 0.0]
        result = autocorrelation(returns, 1)
        assert result == Decimal(0)

    def test_higher_lag(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03]
        result = autocorrelation(returns, 3)
        assert isinstance(result, Decimal)


class TestAutocorrelationMatrix:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02]
        result = autocorrelation_matrix(returns, 3)
        assert len(result) == 3
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_invalid_max_lag(self):
        with pytest.raises(ValueError):
            autocorrelation_matrix([0.01, 0.02], 0)

    def test_max_lag_one(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = autocorrelation_matrix(returns, 1)
        assert 1 in result

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = autocorrelation_matrix(returns, 2, ndigits=4)
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_short_series_handling(self):
        returns = [0.01, 0.02]
        result = autocorrelation_matrix(returns, 5)
        assert isinstance(result, dict)


class TestLjungBoxStatistic:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03, 0.01]
        result = ljung_box_statistic(returns, 3)
        assert len(result) == 3
        assert all(isinstance(v, Decimal) for v in result.values())

    def test_too_short(self):
        with pytest.raises(ValueError):
            ljung_box_statistic([0.01], 1)

    def test_nonnegative(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01]
        result = ljung_box_statistic(returns, 2)
        assert all(v >= 0 for v in result.values())

    def test_zero_for_white_noise(self):
        returns = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        result = ljung_box_statistic(returns, 2)
        assert all(v == Decimal(0) for v in result.values())

    def test_max_lag_one(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = ljung_box_statistic(returns, 1)
        assert 1 in result
        assert result[1] >= 0


class TestPartialAutocorrelation:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03]
        result = partial_autocorrelation(returns, 1)
        assert isinstance(result, Decimal)

    def test_lag_one_equals_autocorrelation(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01]
        pacf = partial_autocorrelation(returns, 1)
        acf = autocorrelation(returns, 1)
        assert pacf == acf

    def test_lag_two(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03]
        result = partial_autocorrelation(returns, 2)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            partial_autocorrelation([0.01, 0.02], 3)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = partial_autocorrelation(returns, 1, ndigits=4)
        assert isinstance(result, Decimal)

    def test_bounds(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03]
        result = partial_autocorrelation(returns, 2)
        assert -1 <= result <= 1

    def test_white_noise(self):
        returns = [0.01, -0.01, 0.01, -0.01, 0.01, -0.01]
        result = partial_autocorrelation(returns, 1)
        assert isinstance(result, Decimal)

    def test_constant_returns(self):
        returns = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        result = partial_autocorrelation(returns, 1)
        assert result == Decimal(0)

    def test_lag_three(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, 0.01, -0.02, 0.03, 0.01]
        result = partial_autocorrelation(returns, 3)
        assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_bounds(returns):
    assume(len(set(returns)) > 1)
    acf = autocorrelation(returns, 1)
    assert -1 <= acf <= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_partial_autocorrelation_bounds(returns):
    assume(len(set(returns)) > 1)
    pacf = partial_autocorrelation(returns, 1)
    assert -1 <= pacf <= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_ljung_box_nonnegative(returns):
    assume(len(set(returns)) > 1)
    lb = ljung_box_statistic(returns, 2)
    assert all(v >= 0 for v in lb.values())


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_matrix_keys(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation_matrix(returns, 3)
    assert set(result.keys()) == {1, 2, 3}



@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_pacf_lag1_equals_acf_lag1(returns):
    assume(len(set(returns)) > 1)
    pacf = partial_autocorrelation(returns, 1)
    acf = autocorrelation(returns, 1)
    assert pacf == acf


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_lag_one_range(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation(returns, 1)
    assert -1 <= result <= 1


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_matrix_length(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation_matrix(returns, 5)
    assert len(result) <= 5


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_ljung_box_keys(returns):
    assume(len(set(returns)) > 1)
    result = ljung_box_statistic(returns, 4)
    assert set(result.keys()) == {1, 2, 3, 4}


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_partial_autocorrelation_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = partial_autocorrelation(returns, 1, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation(returns, 1, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_matrix_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation_matrix(returns, 3, ndigits=4)
    assert all(isinstance(v, Decimal) for v in result.values())


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_partial_autocorrelation_high_lag(returns):
    assume(len(set(returns)) > 1)
    result = partial_autocorrelation(returns, 3)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_different_lags(returns):
    assume(len(set(returns)) > 1)
    r1 = autocorrelation(returns, 1)
    r2 = autocorrelation(returns, 2)
    assert isinstance(r1, Decimal)
    assert isinstance(r2, Decimal)


def test_autocorrelation_zero_for_constant():
    returns = [0.01] * 10
    result = autocorrelation(returns, 1)
    assert result == Decimal(0)


def test_autocorrelation_lag_zero_is_one():
    returns = [0.01, 0.02, -0.01, 0.015]
    result = autocorrelation(returns, 0)
    assert result == Decimal(1)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_matrix_contains_lags(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation_matrix(returns, 3)
    assert 1 in result and 2 in result and 3 in result


def test_ljung_box_zero_for_constant():
    returns = [0.01] * 10
    result = ljung_box_statistic(returns, 2)
    assert all(v == Decimal(0) for v in result.values())


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_short_series_zero_lag(returns):
    assume(len(set(returns)) > 1)
    result = autocorrelation(returns, 0)
    assert result == Decimal(1)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_partial_autocorrelation_lag1_equals_acf_lag1_consistency(returns):
    assume(len(set(returns)) > 1)
    p = partial_autocorrelation(returns, 1)
    a = autocorrelation(returns, 1)
    assert p == a


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_autocorrelation_short_series_zero_lag(returns):
    r0 = autocorrelation(returns, 0)
    assert r0 == Decimal(1)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_partial_autocorrelation_lag1_equals_acf_lag1_consistency(returns):
    assume(len(set(returns)) > 1)
    p = partial_autocorrelation(returns, 1)
    a = autocorrelation(returns, 1)
    assert p == a
