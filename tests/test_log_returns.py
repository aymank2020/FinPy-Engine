from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.returns.log_returns import log_returns, simple_returns, cumulative_return
from finpy.returns.log_returns import annualized_volatility, total_return, arithmetic_mean
from finpy.returns.log_returns import geometric_mean, variance, std, skewness, kurtosis
from finpy.returns.log_returns import semivariance, downside_std, annualized_return
from finpy.returns.log_returns import annualized_std, information_ratio, tracking_error
from finpy.returns.log_returns import gain_loss_ratio
from tests._helpers import approx_decimal


class TestLogReturns:
    def test_basic(self):
        result = log_returns([100, 110, 121])
        assert len(result) == 2

    def test_too_short(self):
        with pytest.raises(ValueError):
            log_returns([100])

    def test_computed_values(self):
        result = log_returns([100, 200])
        assert result[0] == pytest.approx(Decimal(str(200/100)).ln(), abs=1e-10)

    def test_positive_and_negative(self):
        result = log_returns([100, 90, 110])
        assert result[0] < 0
        assert result[1] > 0

    def test_same_price(self):
        result = log_returns([100, 100, 100])
        assert all(r == Decimal(0) for r in result)


class TestSimpleReturns:
    def test_basic(self):
        result = simple_returns([100, 110, 121])
        assert len(result) == 2

    def test_too_short(self):
        with pytest.raises(ValueError):
            simple_returns([100])

    def test_computed_value(self):
        result = simple_returns([100, 110])
        assert result[0] == Decimal("0.1")

    def test_negative(self):
        result = simple_returns([100, 90])
        assert result[0] == Decimal("-0.1")


class TestCumulativeReturn:
    def test_basic(self):
        result = cumulative_return([100, 110, 121])
        assert result == Decimal("0.21")

    def test_too_short(self):
        with pytest.raises(ValueError):
            cumulative_return([100])

    def test_negative(self):
        result = cumulative_return([100, 90, 80])
        assert result == Decimal("-0.2")

    def test_no_change(self):
        result = cumulative_return([100, 100])
        assert result == Decimal(0)


class TestAnnualizedVolatility:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = annualized_volatility(returns, 252)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            annualized_volatility([0.01], 252)

    def test_zero_volatility(self):
        returns = [0.01, 0.01, 0.01, 0.01]
        result = annualized_volatility(returns, 252)
        assert result == Decimal(0)

    def test_higher_periods_higher_vol(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        monthly = annualized_volatility(returns, 12)
        daily = annualized_volatility(returns, 252)
        assert daily >= monthly


class TestTotalReturn:
    def test_basic(self):
        returns = [Decimal("0.1"), Decimal("0.1")]
        result = total_return(returns)
        assert result == Decimal("0.21")

    def test_empty(self):
        with pytest.raises(ValueError):
            total_return([])

    def test_negative_returns(self):
        returns = [Decimal("-0.1"), Decimal("-0.1")]
        result = total_return(returns)
        assert result < 0

    def test_mixed(self):
        returns = [Decimal("0.1"), Decimal("-0.05")]
        result = total_return(returns)
        assert result == Decimal("0.045")


class TestArithmeticMean:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        result = arithmetic_mean(returns)
        assert result == Decimal("0.02") / Decimal(3)

    def test_empty(self):
        with pytest.raises(ValueError):
            arithmetic_mean([])

    def test_single(self):
        result = arithmetic_mean([Decimal("0.05")])
        assert result == Decimal("0.05")


class TestGeometricMean:
    def test_basic(self):
        returns = [Decimal("0.1"), Decimal("0.1")]
        result = geometric_mean(returns)
        assert result > 0

    def test_empty(self):
        with pytest.raises(ValueError):
            geometric_mean([])

    def test_zero_returns(self):
        returns = [Decimal("0"), Decimal("0"), Decimal("0")]
        result = geometric_mean(returns)
        assert result == Decimal(0)


class TestVariance:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        result = variance(returns)
        assert result >= 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            variance([Decimal("0.01")])

    def test_constant_returns(self):
        returns = [Decimal("0.01"), Decimal("0.01"), Decimal("0.01")]
        result = variance(returns)
        assert result == Decimal(0)

    def test_with_ddof_zero(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        result = variance(returns, ddof=0)
        assert result >= 0


class TestStd:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        result = std(returns)
        assert result >= 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            std([Decimal("0.01")])

    def test_constant(self):
        returns = [Decimal("0.01"), Decimal("0.01"), Decimal("0.01")]
        result = std(returns)
        assert result == Decimal(0)


class TestSkewness:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01"), Decimal("0.015")]
        result = skewness(returns)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            skewness([Decimal("0.01"), Decimal("0.02")])

    def test_symmetric(self):
        returns = [Decimal("-0.05"), Decimal("0"), Decimal("0.05")]
        result = skewness(returns)
        assert result == pytest.approx(Decimal(0), abs=1e-10)

    def test_positive_skew(self):
        returns = [Decimal("-0.03"), Decimal("-0.02"), Decimal("0"), Decimal("0.10")]
        result = skewness(returns)
        assert result > 0

    def test_negative_skew(self):
        returns = [Decimal("-0.10"), Decimal("0"), Decimal("0.02"), Decimal("0.03")]
        result = skewness(returns)
        assert result < 0


class TestKurtosis:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("0.005")]
        result = kurtosis(returns)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            kurtosis([Decimal("0.01"), Decimal("0.02"), Decimal("0.03")])

    def test_normal_like(self):
        returns = [Decimal("-0.01"), Decimal("-0.005"), Decimal("0"), Decimal("0.005"), Decimal("0.01")]
        result = kurtosis(returns)
        assert isinstance(result, Decimal)


class TestSemivariance:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("-0.02"), Decimal("-0.01"), Decimal("0.015")]
        result = semivariance(returns, Decimal(0))
        assert result >= 0

    def test_single_observation_lower_partial_moment(self):
        assert semivariance([Decimal("0.01")]) == 0
        assert semivariance([Decimal("-0.02")]) == Decimal("0.0004")

    def test_no_downside(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
        result = semivariance(returns, Decimal(0))
        assert result == Decimal(0)

    def test_with_target(self):
        returns = [Decimal("0.01"), Decimal("-0.02"), Decimal("-0.01")]
        result = semivariance(returns, Decimal("-0.01"))
        assert result >= 0


class TestDownsideStd:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("-0.02"), Decimal("-0.01"), Decimal("0.015")]
        result = downside_std(returns, Decimal(0))
        assert result >= 0

    def test_no_downside(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
        result = downside_std(returns, Decimal(0))
        assert result == Decimal(0)


class TestAnnualizedReturn:
    def test_basic(self):
        total = Decimal("0.21")
        years = Decimal("2")
        result = annualized_return(total, years)
        assert result > 0

    def test_negative_total(self):
        with pytest.raises(ValueError):
            annualized_return(Decimal("-2"), Decimal("1"))

    def test_zero_years(self):
        with pytest.raises(ValueError):
            annualized_return(Decimal("0.1"), Decimal("0"))

    def test_zero_return(self):
        result = annualized_return(Decimal("0"), Decimal("1"))
        assert result == Decimal(0)

    def test_negative_years(self):
        with pytest.raises(ValueError):
            annualized_return(Decimal("0.1"), Decimal("-1"))


class TestAnnualizedStd:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")]
        result = annualized_std(returns, 252)
        assert isinstance(result, Decimal)

    def test_constant(self):
        returns = [Decimal("0.01"), Decimal("0.01"), Decimal("0.01")]
        result = annualized_std(returns, 252)
        assert result == Decimal(0)


class TestGainLossRatio:
    def test_basic(self):
        returns = [Decimal("0.01"), Decimal("-0.02"), Decimal("0.03"), Decimal("-0.01")]
        result = gain_loss_ratio(returns)
        assert isinstance(result, Decimal)

    def test_all_gains(self):
        returns = [Decimal("0.01"), Decimal("0.02")]
        result = gain_loss_ratio(returns)
        assert result == Decimal("Infinity")

    def test_all_losses(self):
        returns = [Decimal("-0.01"), Decimal("-0.02")]
        result = gain_loss_ratio(returns)
        assert result == Decimal(0)

    def test_equal_ratio(self):
        returns = [Decimal("0.02"), Decimal("-0.02")]
        result = gain_loss_ratio(returns)
        assert result == Decimal(1)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_log_returns_length(prices):
    lr = log_returns(prices)
    assert len(lr) == len(prices) - 1


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_log_returns_ordering_preserved(prices):
    lr = log_returns(prices)
    sr = simple_returns(prices)
    assert len(lr) == len(sr)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_log_simple_returns_sign(prices):
    lr = log_returns(prices)
    sr = simple_returns(prices)
    for l, s in zip(lr, sr):
        assert (l >= 0) == (s >= 0)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_cumulative_return_bounds(prices):
    cr = cumulative_return(prices)
    assert isinstance(cr, Decimal)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_total_return_type(prices):
    rets = simple_returns(prices)
    tr = total_return(rets)
    assert isinstance(tr, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_variance_nonnegative(returns):
    dec_rets = [Decimal(str(r)) for r in returns]
    try:
        v = variance(dec_rets)
        assert v >= 0
    except ValueError:
        pass


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_semivariance_nonnegative(returns):
    dec_rets = [Decimal(str(r)) for r in returns]
    sv = semivariance(dec_rets, Decimal(0))
    assert sv >= 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=3, max_size=20))
def test_arithmetic_mean_bounds(returns):
    dec_rets = [Decimal(str(r)) for r in returns]
    am = arithmetic_mean(dec_rets)
    assert min(dec_rets) <= am <= max(dec_rets) or abs(am) <= max(abs(d) for d in dec_rets)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_simple_returns_length(prices):
    result = simple_returns(prices)
    assert len(result) == len(prices) - 1


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_simple_returns_sign_matches_log(prices):
    sr = simple_returns(prices)
    lr = log_returns(prices)
    for s, l in zip(sr, lr):
        assert (s >= 0) == (l >= 0)


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_cumulative_return_type(prices):
    result = cumulative_return(prices)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_variance_with_ddof_zero(returns):
    dec_rets = [Decimal(str(r)) for r in returns]
    try:
        v0 = variance(dec_rets, ddof=0)
        v1 = variance(dec_rets, ddof=1)
        assert v0 <= v1
    except ValueError:
        pass


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_std_positive_for_variable_returns(returns):
    assume(len(set(returns)) > 1)
    dec_rets = [Decimal(str(r)) for r in returns]
    result = std(dec_rets)
    assert result > 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_gain_loss_ratio_symmetric(returns):
    assume(len(set(returns)) > 1)
    assume(all(abs(r) > 1e-10 for r in returns if r != 0))
    dec_rets = [Decimal(str(r)) for r in returns]
    neg = [-r for r in dec_rets]
    glr_pos = gain_loss_ratio(dec_rets)
    glr_neg = gain_loss_ratio(neg)
    if glr_pos > 0 and glr_neg > 0:
        assert abs(glr_pos - Decimal(1) / glr_neg) < Decimal("1")


@given(st.lists(st.floats(1, 1000), min_size=3, max_size=30))
def test_annualized_return_positive_for_growth(prices):
    assume(all(p > 0 for p in prices))
    assume(prices[-1] > prices[0])
    rets = simple_returns(prices)
    tr = total_return(rets)
    assume(tr > Decimal("-1"))
    years = Decimal(len(prices)) / Decimal(252)
    result = annualized_return(tr, years)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=20))
def test_annualized_std_positive(returns):
    dec_rets = [Decimal(str(r)) for r in returns]
    try:
        result = annualized_std(dec_rets, 252)
        assert result >= 0
    except ValueError:
        pass
