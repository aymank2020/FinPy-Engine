from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.risk.max_drawdown import max_drawdown, drawdown_series, average_drawdown
from finpy.risk.max_drawdown import drawdown_duration, calmar_ratio, ulcer_index
from tests._helpers import approx_decimal


class TestMaxDrawdown:
    def test_basic(self):
        prices = [100, 110, 105, 120, 115, 130]
        result = max_drawdown(prices)
        assert result > 0

    def test_uptrend(self):
        prices = [100, 110, 120, 130]
        result = max_drawdown(prices)
        assert result == Decimal("0")

    def test_downtrend(self):
        prices = [130, 120, 110, 100]
        result = max_drawdown(prices)
        assert result > 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            max_drawdown([100])

    def test_with_ndigits(self):
        prices = [100, 110, 105, 120]
        result = max_drawdown(prices, ndigits=3)
        assert isinstance(result, Decimal)

    def test_single_drop(self):
        prices = [100, 90, 100, 110]
        result = max_drawdown(prices)
        assert result == Decimal("0.1")

    def test_multiple_drops(self):
        prices = [100, 95, 100, 90, 100]
        result = max_drawdown(prices)
        assert result == Decimal("0.1")

    def test_recovery_to_new_high(self):
        prices = [100, 90, 110]
        result = max_drawdown(prices)
        assert result == Decimal("0.1")

    def test_flat_prices(self):
        prices = [100, 100, 100, 100]
        result = max_drawdown(prices)
        assert result == Decimal("0")


class TestDrawdownSeries:
    def test_basic(self):
        prices = [100, 110, 105, 120]
        result = drawdown_series(prices)
        assert len(result) == len(prices)

    def test_too_short(self):
        with pytest.raises(ValueError):
            drawdown_series([100])

    def test_uptrend_all_zero(self):
        prices = [100, 110, 120, 130]
        result = drawdown_series(prices)
        assert all(dd == Decimal(0) for dd in result)

    def test_first_entry_zero(self):
        prices = [100, 90, 80]
        result = drawdown_series(prices)
        assert result[0] == Decimal(0)

    def test_with_ndigits(self):
        prices = [100, 110, 105, 120]
        result = drawdown_series(prices, ndigits=3)
        assert all(isinstance(d, Decimal) for d in result)

    def test_nonnegative(self):
        prices = [100, 90, 80, 110, 105]
        result = drawdown_series(prices)
        assert all(d >= 0 for d in result)

    def test_length(self):
        prices = [100, 110, 105, 120, 115, 130]
        result = drawdown_series(prices)
        assert len(result) == len(prices)

    def test_decreasing_then_increasing(self):
        prices = [100, 90, 80, 100, 110]
        result = drawdown_series(prices)
        assert result[-1] == 0


class TestAverageDrawdown:
    def test_basic(self):
        prices = [100, 110, 105, 120, 115, 130]
        result = average_drawdown(prices)
        assert result >= 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            average_drawdown([100])

    def test_uptrend(self):
        prices = [100, 110, 120, 130]
        result = average_drawdown(prices)
        assert result == Decimal(0)

    def test_with_ndigits(self):
        prices = [100, 110, 105, 120]
        result = average_drawdown(prices, ndigits=3)
        assert isinstance(result, Decimal)

    def test_downtrend(self):
        prices = [130, 120, 110, 100]
        result = average_drawdown(prices)
        assert result > 0

    def test_nonnegative(self):
        prices = [100, 95, 90, 110, 105]
        result = average_drawdown(prices)
        assert result >= 0

    def test_single_drop_then_recover(self):
        prices = [100, 90, 100]
        result = average_drawdown(prices)
        assert result >= 0


class TestDrawdownDuration:
    def test_basic(self):
        prices = [100, 110, 105, 120, 115, 130]
        result = drawdown_duration(prices)
        assert isinstance(result, int)

    def test_too_short(self):
        with pytest.raises(ValueError):
            drawdown_duration([100])

    def test_uptrend(self):
        prices = [100, 110, 120, 130]
        result = drawdown_duration(prices)
        assert result == 0

    def test_constant_drawdown(self):
        prices = [100, 90, 80, 70]
        result = drawdown_duration(prices)
        assert result > 0

    def test_nonnegative(self):
        prices = [100, 110, 105, 120, 115, 100, 130]
        result = drawdown_duration(prices)
        assert result >= 0

    def test_recovery_resets(self):
        prices = [100, 90, 100, 95, 100]
        result = drawdown_duration(prices)
        assert result >= 0

    def test_short_series_two(self):
        prices = [100, 90]
        result = drawdown_duration(prices)
        assert result == 1


class TestCalmarRatio:
    def test_basic(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = calmar_ratio(returns, 252)
        assert isinstance(result, Decimal)

    def test_too_short(self):
        with pytest.raises(ValueError):
            calmar_ratio([0.01], 252)

    def test_zero_drawdown(self):
        returns = [0.01, 0.02, 0.03, 0.04]
        result = calmar_ratio(returns, 252)
        assert result == Decimal(0)

    def test_positive_returns(self):
        returns = [0.05, -0.02, 0.03, -0.01]
        result = calmar_ratio(returns, 252)
        assert isinstance(result, Decimal)

    def test_with_ndigits(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        result = calmar_ratio(returns, 252, ndigits=4)
        assert isinstance(result, Decimal)

    def test_annual_different_periods(self):
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        monthly = calmar_ratio(returns, 12)
        daily = calmar_ratio(returns, 252)
        assert isinstance(monthly, Decimal)
        assert isinstance(daily, Decimal)

    def test_negative_returns(self):
        returns = [-0.01, -0.02, -0.01]
        result = calmar_ratio(returns, 252)
        assert isinstance(result, Decimal)

    def test_nonzero_mdd(self):
        returns = [0.1, -0.1, 0.05, -0.05, 0.1]
        result = calmar_ratio(returns, 252)
        assert isinstance(result, Decimal)


class TestUlcerIndex:
    def test_basic(self):
        prices = [100, 110, 105, 120, 115, 130]
        result = ulcer_index(prices)
        assert result >= 0

    def test_too_short(self):
        with pytest.raises(ValueError):
            ulcer_index([100])

    def test_uptrend(self):
        prices = [100, 110, 120, 130]
        result = ulcer_index(prices)
        assert result == Decimal(0)

    def test_downtrend(self):
        prices = [130, 120, 110, 100]
        result = ulcer_index(prices)
        assert result > 0

    def test_with_ndigits(self):
        prices = [100, 110, 105, 120]
        result = ulcer_index(prices, ndigits=3)
        assert isinstance(result, Decimal)

    def test_nonnegative(self):
        prices = [100, 95, 90, 110, 105]
        result = ulcer_index(prices)
        assert result >= 0

    def test_constant_drawdown(self):
        prices = [100, 80, 80, 80]
        result = ulcer_index(prices)
        assert result > 0

    def test_recovery(self):
        prices = [100, 80, 100, 120]
        result = ulcer_index(prices)
        assert result >= 0


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_max_drawdown_sign(prices):
    mdd = max_drawdown(prices)
    assert mdd >= 0


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_drawdown_series_length(prices):
    ds = drawdown_series(prices)
    assert len(ds) == len(prices)


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_ulcer_index_nonnegative(prices):
    result = ulcer_index(prices)
    assert result >= 0


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_drawdown_duration_nonnegative(prices):
    duration = drawdown_duration(prices)
    assert duration >= 0


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_average_drawdown_nonnegative(prices):
    avg = average_drawdown(prices)
    assert avg >= 0


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_max_drawdown_gte_average(prices):
    mdd = max_drawdown(prices)
    avg = average_drawdown(prices)
    assert mdd >= avg


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_ulcer_index_vs_max_drawdown(prices):
    ui = ulcer_index(prices)
    mdd = max_drawdown(prices)
    assert ui <= mdd


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_drawdown_series_first_zero(prices):
    ds = drawdown_series(prices)
    assert ds[0] == Decimal(0)


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_calmar_ratio_type(returns):
    result = calmar_ratio(returns, 252)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_max_drawdown_bounds(prices):
    mdd = max_drawdown(prices)
    assert mdd <= 1


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_average_drawdown_lte_max(prices):
    avg = average_drawdown(prices)
    mdd = max_drawdown(prices)
    assert avg <= mdd


@given(st.lists(st.floats(1, 200), min_size=3, max_size=30))
def test_ulcer_index_squared_form(prices):
    ui = ulcer_index(prices)
    assert ui >= 0


@given(st.lists(st.floats(-0.05, 0.05), min_size=5, max_size=30))
def test_calmar_ratio_nonnegative(returns):
    result = calmar_ratio(returns, 252)
    assert isinstance(result, Decimal)
