from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.beta import beta, alpha_jensen, tracking_error as tracking_error_risk
from finpy.risk.beta import information_ratio as information_ratio_risk, treynor_ratio, r_squared
from tests._helpers import approx_decimal


class TestBeta:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.005, 0.01, -0.005, 0.01]
        result = beta(asset, market)
        assert isinstance(result, Decimal)

    def test_asset_equals_market(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.01, 0.02, -0.01, 0.015]
        result = beta(asset, market)
        assert result == Decimal(1)

    def test_uncorrelated(self):
        asset = [0.01, -0.01, 0.01, -0.01]
        market = [0.005, 0.005, -0.005, -0.005]
        result = beta(asset, market)
        assert result == Decimal(0)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            beta([0.01, 0.02], [0.01])

    def test_too_short(self):
        with pytest.raises(ValueError):
            beta([0.01], [0.01])

    def test_zero_market_variance(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.01, 0.01]
        result = beta(asset, market)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.005, 0.01, -0.005, 0.01]
        result = beta(asset, market, ndigits=4)
        assert isinstance(result, Decimal)

    def test_negative_beta(self):
        asset = [-0.01, -0.02, -0.01, -0.015]
        market = [0.01, 0.02, 0.01, 0.015]
        result = beta(asset, market)
        assert result < 0

    def test_high_beta(self):
        asset = [0.02, 0.04, -0.02, 0.03]
        market = [0.005, 0.01, -0.005, 0.01]
        result = beta(asset, market)
        assert result > 1


class TestAlphaJensen:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.005, 0.01, -0.005, 0.01]
        result = alpha_jensen(asset, market, 0.0)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            alpha_jensen([0.01, 0.02], [0.01], 0.0)

    def test_too_short(self):
        with pytest.raises(ValueError):
            alpha_jensen([0.01], [0.01], 0.0)

    def test_with_risk_free(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.005, 0.01, -0.005, 0.01]
        result = alpha_jensen(asset, market, 0.005)
        assert isinstance(result, Decimal)

    def test_zero_market_var(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.01, 0.01]
        result = alpha_jensen(asset, market, 0.0)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015]
        market = [0.005, 0.01, -0.005, 0.01]
        result = alpha_jensen(asset, market, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_perfect_tracking(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.02, -0.01]
        result = alpha_jensen(asset, market, 0.0)
        assert result == Decimal(0)

    def test_positive_alpha(self):
        asset = [0.02, 0.03, -0.005, 0.02]
        market = [0.005, 0.01, -0.005, 0.01]
        result = alpha_jensen(asset, market, 0.0)
        assert result > 0

    def test_negative_alpha(self):
        asset = [0.005, 0.01, -0.015, 0.005]
        market = [0.01, 0.02, -0.01, 0.015]
        result = alpha_jensen(asset, market, 0.0)
        assert result < 0


class TestTrackingError:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = tracking_error_risk(asset, bench)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            tracking_error_risk([0.01, 0.02], [0.01])

    def test_too_short(self):
        with pytest.raises(ValueError):
            tracking_error_risk([0.01], [0.01])

    def test_zero_tracking(self):
        asset = [0.01, 0.02, -0.01]
        bench = [0.01, 0.02, -0.01]
        result = tracking_error_risk(asset, bench)
        assert result == Decimal(0)

    def test_with_periods(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = tracking_error_risk(asset, bench, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = tracking_error_risk(asset, bench, ndigits=4)
        assert isinstance(result, Decimal)

    def test_nonnegative(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = tracking_error_risk(asset, bench)
        assert result >= 0

    def test_annualized_larger(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        daily = tracking_error_risk(asset, bench)
        annual = tracking_error_risk(asset, bench, periods_per_year=252)
        assert annual >= daily


class TestInformationRatio:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = information_ratio_risk(asset, bench)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            information_ratio_risk([0.01, 0.02], [0.01])

    def test_too_short(self):
        with pytest.raises(ValueError):
            information_ratio_risk([0.01], [0.01])

    def test_zero_tracking(self):
        asset = [0.01, 0.02, -0.01]
        bench = [0.01, 0.02, -0.01]
        result = information_ratio_risk(asset, bench)
        assert result == Decimal(0)

    def test_with_periods(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = information_ratio_risk(asset, bench, periods_per_year=252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        bench = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = information_ratio_risk(asset, bench, ndigits=4)
        assert isinstance(result, Decimal)

    def test_outperforming(self):
        asset = [0.02, 0.03, 0.0, 0.02]
        bench = [0.005, 0.01, -0.005, 0.01]
        result = information_ratio_risk(asset, bench)
        assert result > 0

    def test_underperforming(self):
        asset = [0.005, 0.01, -0.015, 0.005]
        bench = [0.01, 0.02, -0.01, 0.015]
        result = information_ratio_risk(asset, bench)
        assert result < 0


class TestTreynorRatio:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        market = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = treynor_ratio(asset, market, 0.0)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            treynor_ratio([0.01, 0.02], [0.01], 0.0)

    def test_too_short(self):
        with pytest.raises(ValueError):
            treynor_ratio([0.01], [0.01], 0.0)

    def test_with_risk_free(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        market = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = treynor_ratio(asset, market, 0.005)
        assert isinstance(result, Decimal)

    def test_zero_market_var(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.01, 0.01]
        result = treynor_ratio(asset, market, 0.0)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        market = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = treynor_ratio(asset, market, 0.0, ndigits=4)
        assert isinstance(result, Decimal)

    def test_negative_beta(self):
        asset = [-0.01, -0.02, -0.01, -0.015]
        market = [0.01, 0.02, 0.01, 0.015]
        result = treynor_ratio(asset, market, 0.0)
        assert isinstance(result, Decimal)

    def test_high_ratio(self):
        asset = [0.02, 0.04, -0.02, 0.03]
        market = [0.001, 0.002, -0.001, 0.002]
        result = treynor_ratio(asset, market, 0.0)
        assert isinstance(result, Decimal)


class TestRSquared:
    def test_basic(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        market = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = r_squared(asset, market)
        assert isinstance(result, Decimal)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            r_squared([0.01, 0.02], [0.01])

    def test_too_short(self):
        with pytest.raises(ValueError):
            r_squared([0.01], [0.01])

    def test_perfect_correlation(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.02, -0.01]
        result = r_squared(asset, market)
        assert result == Decimal(1)

    def test_no_correlation(self):
        asset = [0.01, -0.01, 0.01, -0.01]
        market = [0.005, 0.005, -0.005, -0.005]
        result = r_squared(asset, market)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005]
        market = [0.005, 0.01, -0.005, 0.01, 0.003]
        result = r_squared(asset, market, ndigits=4)
        assert isinstance(result, Decimal)

    def test_between_zero_and_one(self):
        asset = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03]
        market = [0.005, 0.01, -0.005, 0.01, 0.003, -0.01, 0.02]
        result = r_squared(asset, market)
        assert 0 <= result <= 1

    def test_zero_asset_var(self):
        asset = [0.01, 0.01, 0.01]
        market = [0.005, 0.01, 0.015]
        result = r_squared(asset, market)
        assert result == Decimal(0)

    def test_zero_market_var(self):
        asset = [0.01, 0.02, -0.01]
        market = [0.01, 0.01, 0.01]
        result = r_squared(asset, market)
        assert result == Decimal(0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_beta_self_is_one(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var_market = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var_market > 1e-20)
    result = beta(returns, returns)
    assert result == pytest.approx(Decimal(1), abs=Decimal("1e-10"))


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_r_squared_perfect_self(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = r_squared(returns, returns)
    assert result == pytest.approx(Decimal(1), abs=Decimal("1e-10"))


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_tracking_error_self_is_zero(returns):
    assume(len(set(returns)) > 1)
    result = tracking_error_risk(returns, returns)
    assert result == Decimal(0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_information_ratio_self_is_zero(returns):
    assume(len(set(returns)) > 1)
    result = information_ratio_risk(returns, returns)
    assert result == Decimal(0)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_r_squared_bounds(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = r_squared(returns, returns)
    assert result == pytest.approx(Decimal(1), abs=Decimal("1e-10"))


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_beta_output_type(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = beta(returns, returns)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_tracking_error_nonnegative(returns):
    assume(len(set(returns)) > 1)
    result = tracking_error_risk(returns, returns)
    assert result >= 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_alpha_jensen_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = alpha_jensen(returns, returns, 0.0, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_tracking_error_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = tracking_error_risk(returns, returns, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_r_squared_ndigits(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = r_squared(returns, returns, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_information_ratio_ndigits(returns):
    assume(len(set(returns)) > 1)
    result = information_ratio_risk(returns, returns, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_treynor_ratio_ndigits(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = treynor_ratio(returns, returns, 0.0, ndigits=4)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(-0.05, 0.05), min_size=4, max_size=20))
def test_beta_ndigits_rounding(returns):
    assume(len(set(returns)) > 1)
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    assume(var > 1e-20)
    result = beta(returns, returns, ndigits=2)
    assert isinstance(result, Decimal)
