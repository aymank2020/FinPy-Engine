from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.parametric_var import parametric_var, parametric_var_portfolio
from finpy.risk.parametric_var import cornish_fisher_var, modified_var
from tests._helpers import approx_decimal


class TestParametricVaR:
    def test_basic(self):
        result = parametric_var(0.001, 0.02, 0.95)
        assert result > 0

    def test_zero_mean(self):
        result = parametric_var(0.0, 0.02, 0.95)
        assert result > 0

    def test_zero_std(self):
        result = parametric_var(0.001, 0.0, 0.95)
        assert result == Decimal("0.001")

    def test_confidence_90(self):
        result = parametric_var(0.001, 0.02, 0.90)
        assert result > 0

    def test_confidence_99(self):
        result = parametric_var(0.001, 0.02, 0.99)
        assert result > 0

    def test_with_ndigits(self):
        result = parametric_var(0.001, 0.02, 0.95, ndigits=3)
        assert isinstance(result, Decimal)
        assert result == Decimal("0.032")

    def test_negative_mean(self):
        result = parametric_var(-0.002, 0.02, 0.95)
        assert result > 0

    def test_nonstandard_confidence(self):
        result = parametric_var(0.0, 0.02, 0.85)
        assert result > 0

    def test_very_high_confidence(self):
        result = parametric_var(0.0, 0.02, 0.999)
        assert result > 0

    def test_95_greater_than_90(self):
        var90 = parametric_var(0.0, 0.02, 0.90)
        var95 = parametric_var(0.0, 0.02, 0.95)
        assert var95 >= var90

    def test_ndigits_rounding(self):
        result = parametric_var(0.0, 0.02123, 0.95, ndigits=2)
        assert result == Decimal("0.03")

    def test_large_std(self):
        result = parametric_var(0.0, 0.5, 0.95)
        assert result > 0.8


class TestParametricVaRPortfolio:
    def test_basic(self):
        weights = [0.5, 0.5]
        cov = [[0.04, 0.01], [0.01, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.95)
        assert result > 0

    def test_single_asset(self):
        weights = [1.0]
        cov = [[0.04]]
        result = parametric_var_portfolio(weights, cov, 0.95)
        assert result > 0

    def test_empty_weights(self):
        with pytest.raises(ValueError):
            parametric_var_portfolio([], [[0.04]], 0.95)

    def test_cov_matrix_mismatch(self):
        with pytest.raises(ValueError):
            parametric_var_portfolio([0.5, 0.5], [[0.04]], 0.95)

    def test_non_square_cov(self):
        with pytest.raises(ValueError):
            parametric_var_portfolio([0.5, 0.5], [[0.04, 0.01], [0.01, 0.09, 0.02]], 0.95)

    def test_three_assets(self):
        weights = [0.33, 0.33, 0.34]
        cov = [[0.04, 0.01, 0.005],
               [0.01, 0.09, 0.01],
               [0.005, 0.01, 0.06]]
        result = parametric_var_portfolio(weights, cov, 0.95)
        assert result > 0

    def test_with_ndigits(self):
        weights = [0.5, 0.5]
        cov = [[0.04, 0.01], [0.01, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.95, ndigits=3)
        assert isinstance(result, Decimal)

    def test_confidence_99(self):
        weights = [0.5, 0.5]
        cov = [[0.04, 0.01], [0.01, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.99)
        assert result > 0

    def test_zero_covariance(self):
        weights = [0.5, 0.5]
        cov = [[0.04, 0.0], [0.0, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.95)
        assert result > 0

    def test_negative_weight(self):
        weights = [-0.5, 1.5]
        cov = [[0.04, 0.01], [0.01, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.95)
        assert result > 0

    def test_nonstandard_confidence(self):
        weights = [0.5, 0.5]
        cov = [[0.04, 0.01], [0.01, 0.09]]
        result = parametric_var_portfolio(weights, cov, 0.85)
        assert result > 0


class TestCornishFisherVaR:
    def test_basic(self):
        result = cornish_fisher_var(0.001, 0.02, 0.0, 0.0, 0.95)
        assert result > 0

    def test_negative_skewness(self):
        result = cornish_fisher_var(0.001, 0.02, -0.5, 0.0, 0.95)
        assert result > 0

    def test_positive_skewness(self):
        result = cornish_fisher_var(0.001, 0.02, 0.5, 0.0, 0.95)
        assert result > 0

    def test_positive_kurtosis(self):
        result = cornish_fisher_var(0.001, 0.02, 0.0, 2.0, 0.95)
        assert result > 0

    def test_negative_kurtosis(self):
        result = cornish_fisher_var(0.001, 0.02, 0.0, -0.5, 0.95)
        assert result > 0

    def test_with_ndigits(self):
        result = cornish_fisher_var(0.001, 0.02, 0.0, 0.0, 0.95, ndigits=3)
        assert isinstance(result, Decimal)

    def test_high_confidence(self):
        result = cornish_fisher_var(0.0, 0.02, 0.0, 0.0, 0.99)
        assert result > 0

    def test_skew_direction(self):
        pos_skew = cornish_fisher_var(0.0, 0.02, 0.5, 0.0, 0.95)
        neg_skew = cornish_fisher_var(0.0, 0.02, -0.5, 0.0, 0.95)
        assert pos_skew >= neg_skew

    def test_equals_parametric_when_skew_kurt_zero(self):
        cf = cornish_fisher_var(0.001, 0.02, 0.0, 0.0, 0.95)
        pv = parametric_var(0.001, 0.02, 0.95)
        assert cf == pv


class TestModifiedVaR:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = modified_var(returns, 0.95)
        assert result > 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            modified_var([0.01, 0.02], 0.95)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = modified_var(returns, 0.95, ndigits=3)
        assert isinstance(result, Decimal)

    def test_zero_variance(self):
        returns = [0.01, 0.01, 0.01, 0.01]
        result = modified_var(returns, 0.95)
        assert result == Decimal(0)

    def test_high_confidence(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        result = modified_var(returns, 0.99)
        assert result > 0

    def test_confidence_90(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = modified_var(returns, 0.90)
        assert result > 0


@given(st.floats(0.01, 0.5))
def test_parametric_confidence_ordering(std):
    v90 = parametric_var(0.0, std, 0.90)
    v95 = parametric_var(0.0, std, 0.95)
    v99 = parametric_var(0.0, std, 0.99)
    assert v90 <= v95 <= v99


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_modified_var_nonnegative(returns):
    assume(len(returns) >= 3)
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    try:
        result = modified_var(returns, 0.95)
        assert result >= 0
    except ValueError:
        pass


@given(st.floats(0.01, 0.5))
def test_cornish_fisher_equals_parametric_symmetric(std):
    cf = cornish_fisher_var(0.0, std, 0.0, 0.0, 0.95)
    pv = parametric_var(0.0, std, 0.95)
    assert cf == pv


@given(st.floats(0.01, 0.5))
def test_parametric_var_portfolio_output_type(std):
    weights = [0.5, 0.5]
    cov = [[float(std ** 2), 0.0], [0.0, float(std ** 2)]]
    result = parametric_var_portfolio(weights, cov, 0.95)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=10, max_size=40))
def test_modified_var_output_type(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    try:
        result = modified_var(returns, 0.95)
        assert isinstance(result, Decimal)
    except ValueError:
        pass


@given(st.floats(0.01, 0.3))
def test_parametric_var_positive_result(std):
    result = parametric_var(0.0, std, 0.95)
    assert result > 0


@given(st.floats(0.01, 0.3))
def test_parametric_var_confidence_ordering(std):
    v95 = parametric_var(0.0, std, 0.95)
    v99 = parametric_var(0.0, std, 0.99)
    assert v95 <= v99


@given(st.floats(0.01, 0.5))
def test_cornish_fisher_positive_result(std):
    result = cornish_fisher_var(0.0, std, 0.1, 0.0, 0.95)
    assert result > 0


@given(st.floats(0.0001, 0.1))
def test_parametric_var_ndigits_rounding(std):
    result = parametric_var(0.0, std, 0.95, ndigits=2)
    assert isinstance(result, Decimal)
    assert result.as_tuple().exponent == -2


@given(st.floats(0.01, 0.5))
def test_parametric_var_portfolio_single_asset(std):
    result = parametric_var_portfolio([1.0], [[float(std ** 2)]], 0.95)
    expected = parametric_var(0.0, std, 0.95)
    assert result == pytest.approx(expected, abs=Decimal("1e-10"))


@given(st.floats(0.01, 0.5))
def test_cornish_fisher_ndigits_rounding(std):
    result = cornish_fisher_var(0.0, std, 0.0, 0.0, 0.95, ndigits=3)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_parametric_var_positive_std_result(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    std = var ** 0.5
    result = parametric_var(mean, std, 0.95)
    assert result > 0
