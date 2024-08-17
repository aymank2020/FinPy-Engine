from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.returns.rolling import rolling_mean, rolling_std, rolling_window, rolling_sum
from finpy.returns.rolling import rolling_min, rolling_max, rolling_median, rolling_var
from finpy.returns.rolling import rolling_cov, rolling_corr, rolling_skew, rolling_kurtosis
from finpy.returns.rolling import ewm_mean, ewm_std
from tests._helpers import approx_decimal


class TestRollingMean:
    def test_basic(self):
        result = rolling_mean([1, 2, 3, 4, 5], 3)
        assert len(result) == 3
        assert result[0] == Decimal("2")

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_mean([1, 2, 3], 5)

    def test_window_size_one(self):
        result = rolling_mean([1, 2, 3], 1)
        assert len(result) == 3
        assert result == [Decimal(1), Decimal(2), Decimal(3)]

    def test_all_same(self):
        result = rolling_mean([5, 5, 5, 5], 2)
        assert all(r == Decimal(5) for r in result)

    def test_float_values(self):
        result = rolling_mean([1.5, 2.5, 3.5], 2)
        assert len(result) == 2


class TestRollingStd:
    def test_basic(self):
        result = rolling_std([1, 2, 3, 4, 5], 3)
        assert len(result) == 3

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_std([1, 2, 3], 5)

    def test_constant(self):
        result = rolling_std([5, 5, 5, 5], 2)
        assert all(r == Decimal(0) for r in result)

    def test_nonnegative(self):
        result = rolling_std([1, 3, 2, 4, 3], 3)
        assert all(r >= 0 for r in result)

    def test_window_size_two(self):
        result = rolling_std([1, 2, 3], 2)
        assert len(result) == 2


class TestRollingWindow:
    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = rolling_window(data, 3, sum)
        assert len(result) == 3

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_window([1, 2], 3, sum)

    def test_with_max(self):
        data = [1, 5, 2, 8, 3]
        result = rolling_window(data, 3, max)
        assert result[0] == Decimal(5)
        assert result[1] == Decimal(8)
        assert result[2] == Decimal(8)

    def test_with_min(self):
        data = [3, 1, 4, 1, 5]
        result = rolling_window(data, 3, min)
        assert len(result) == 3


class TestRollingSum:
    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = rolling_sum(data, 3)
        assert len(result) == 3
        assert result[0] == Decimal(6)

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_sum([1, 2], 3)

    def test_window_one(self):
        data = [1, 2, 3]
        result = rolling_sum(data, 1)
        assert result == [Decimal(1), Decimal(2), Decimal(3)]


class TestRollingMin:
    def test_basic(self):
        data = [3, 1, 4, 1, 5]
        result = rolling_min(data, 3)
        assert len(result) == 3
        assert result[0] == Decimal(1)
        assert result[1] == Decimal(1)

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_min([1, 2], 3)

    def test_monotonic_increasing(self):
        data = [1, 2, 3, 4, 5]
        result = rolling_min(data, 3)
        assert len(result) == 3
        assert result[0] == Decimal(1)


class TestRollingMax:
    def test_basic(self):
        data = [1, 5, 2, 8, 3]
        result = rolling_max(data, 3)
        assert result[0] == Decimal(5)
        assert result[1] == Decimal(8)
        assert result[2] == Decimal(8)

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_max([1, 2], 3)

    def test_monotonic_decreasing(self):
        data = [5, 4, 3, 2, 1]
        result = rolling_max(data, 3)
        assert len(result) == 3
        assert result[0] == Decimal(5)


class TestRollingMedian:
    def test_basic(self):
        data = [1, 3, 2, 4, 5]
        result = rolling_median(data, 3)
        assert len(result) == 3
        assert result[0] == Decimal(2)

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_median([1, 2], 3)

    def test_odd_window(self):
        data = [5, 1, 3, 2, 4]
        result = rolling_median(data, 3)
        assert len(result) == 3

    def test_even_window(self):
        data = [4, 1, 3, 2]
        result = rolling_median(data, 2)
        assert len(result) == 3


class TestRollingVar:
    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = rolling_var(data, 3)
        assert len(result) == 3

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_var([1, 2], 3)

    def test_constant(self):
        data = [5, 5, 5, 5]
        result = rolling_var(data, 2)
        assert all(r == Decimal(0) for r in result)

    def test_nonnegative(self):
        data = [1, 3, 2, 4, 3, 5]
        result = rolling_var(data, 3)
        assert all(r >= 0 for r in result)


class TestRollingCov:
    def test_basic(self):
        data1 = [1, 2, 3, 4, 5]
        data2 = [2, 4, 6, 8, 10]
        result = rolling_cov(data1, data2, 3)
        assert len(result) == 3

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            rolling_cov([1, 2, 3], [1, 2], 2)

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_cov([1, 2], [1, 2], 3)

    def test_perfect_pos_cov(self):
        data1 = [1, 2, 3, 4]
        data2 = [2, 4, 6, 8]
        result = rolling_cov(data1, data2, 2)
        assert all(r >= 0 for r in result)

    def test_identical_series(self):
        data = [1, 3, 2, 4]
        result = rolling_cov(data, data, 3)
        assert len(result) == 2


class TestRollingCorr:
    def test_basic(self):
        data1 = [1, 2, 3, 4, 5]
        data2 = [2, 4, 6, 8, 10]
        result = rolling_corr(data1, data2, 3)
        assert len(result) == 3

    def test_perfect_correlation(self):
        data1 = [1, 2, 3, 4]
        data2 = [2, 4, 6, 8]
        result = rolling_corr(data1, data2, 2)
        assert all(abs(r - Decimal(1)) < Decimal("1e-10") for r in result)

    def test_between_minus_one_and_one(self):
        data1 = [1, 3, 2, 4, 3, 5]
        data2 = [5, 1, 4, 2, 5, 1]
        result = rolling_corr(data1, data2, 3)
        assert all(-1 <= r <= 1 for r in result)

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            rolling_corr([1, 2, 3], [1, 2], 2)

    def test_constant_one_series(self):
        data1 = [1, 1, 1, 1]
        data2 = [1, 2, 3, 4]
        result = rolling_corr(data1, data2, 2)
        assert all(r == Decimal(0) for r in result)


class TestRollingSkew:
    def test_basic(self):
        data = [1, 2, 3, 4, 5, 6]
        result = rolling_skew(data, 4)
        assert len(result) == 3

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_skew([1, 2, 3], 5)

    def test_symmetric(self):
        data = [-2, -1, 0, 1, 2]
        result = rolling_skew(data, 5)
        assert isinstance(result[0], Decimal)

    def test_constant(self):
        data = [5, 5, 5, 5, 5]
        result = rolling_skew(data, 3)
        assert all(r == Decimal(0) for r in result)


class TestRollingKurtosis:
    def test_basic(self):
        data = [1, 2, 3, 4, 5, 6]
        result = rolling_kurtosis(data, 4)
        assert len(result) == 3

    def test_window_too_large(self):
        with pytest.raises(ValueError):
            rolling_kurtosis([1, 2, 3], 5)

    def test_normal_like(self):
        data = [-2, -1, 0, 1, 2]
        result = rolling_kurtosis(data, 5)
        assert isinstance(result[0], Decimal)

    def test_constant(self):
        data = [5, 5, 5, 5, 5]
        result = rolling_kurtosis(data, 3)
        assert all(r == Decimal(0) for r in result)


class TestEwmMean:
    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = ewm_mean(data, 0.5)
        assert len(result) == 5

    def test_empty(self):
        with pytest.raises(ValueError):
            ewm_mean([], 0.5)

    def test_alpha_one(self):
        data = [1, 2, 3]
        result = ewm_mean(data, 1.0)
        assert result == [Decimal(1), Decimal(2), Decimal(3)]

    def test_alpha_zero(self):
        with pytest.raises(ValueError):
            ewm_mean([1, 2, 3], 0.0)

    def test_alpha_gt_one(self):
        with pytest.raises(ValueError):
            ewm_mean([1, 2, 3], 1.5)

    def test_constant_data(self):
        data = [5, 5, 5, 5]
        result = ewm_mean(data, 0.1)
        assert all(r == Decimal(5) for r in result)

    def test_first_equal_first(self):
        data = [10, 20, 30]
        result = ewm_mean(data, 0.5)
        assert result[0] == Decimal(10)

    def test_alpha_half(self):
        data = [1, 3]
        result = ewm_mean(data, 0.5)
        assert result[1] == Decimal(2)


class TestEwmStd:
    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = ewm_std(data, 0.5)
        assert len(result) == 4

    def test_too_short(self):
        with pytest.raises(ValueError):
            ewm_std([1], 0.5)

    def test_constant_data(self):
        data = [5, 5, 5, 5]
        result = ewm_std(data, 0.1)
        assert all(r == Decimal(0) for r in result)

    def test_nonnegative(self):
        data = [1, 3, 2, 4, 3, 5]
        result = ewm_std(data, 0.3)
        assert all(r >= 0 for r in result)


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_window_length(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rm = rolling_mean(data, ws)
        assert len(rm) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_sum_window(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rs = rolling_sum(data, ws)
        assert len(rs) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_var_nonnegative(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rv = rolling_var(data, ws)
        assert all(v >= 0 for v in rv)


@given(st.lists(st.floats(1, 100), min_size=10, max_size=40))
def test_rolling_corr_bounds(data):
    assume(len(data) >= 5)
    mean = sum(data) / len(data)
    var = sum((x - mean) ** 2 for x in data) / (len(data) - 1)
    assume(var > 1e-10)
    ws = 3
    result = rolling_corr(data, data, ws)
    assert all(-Decimal("1.001") <= r <= Decimal("1.001") for r in result)


@given(st.lists(st.floats(0, 100), min_size=5, max_size=30))
def test_ewm_mean_length(data):
    result = ewm_mean(data, 0.2)
    assert len(result) == len(data)


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_std_nonnegative(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rs = rolling_std(data, ws)
        assert all(s >= 0 for s in rs)


@given(st.lists(st.floats(0, 100), min_size=5, max_size=30))
def test_ewm_std_length(data):
    assume(len(data) >= 2)
    result = ewm_std(data, 0.2)
    assert len(result) == len(data) - 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_median_length(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rm = rolling_median(data, ws)
        assert len(rm) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_skew_length(data):
    assume(len(set(data)) > 1)
    for ws in [4, 6]:
        if len(data) < ws:
            continue
        rs = rolling_skew(data, ws)
        assert len(rs) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_kurtosis_length(data):
    assume(len(set(data)) > 1)
    for ws in [4, 6]:
        if len(data) < ws:
            continue
        rk = rolling_kurtosis(data, ws)
        assert len(rk) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_cov_length(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rc = rolling_cov(data, data, ws)
        assert len(rc) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_max_length(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rm = rolling_max(data, ws)
        assert len(rm) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_min_length(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rm = rolling_min(data, ws)
        assert len(rm) == len(data) - ws + 1


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_ewm_mean_first_equal_first(data):
    result = ewm_mean(data, 0.3)
    assert result[0] == Decimal(str(data[0]))


@given(st.lists(st.floats(0, 100), min_size=10, max_size=50))
def test_rolling_mean_reasonable(data):
    for ws in [3, 5]:
        if len(data) < ws:
            continue
        rm = rolling_mean(data, ws)
        for r in rm:
            assert float(r) >= min(data) - 1e-9
            assert float(r) <= max(data) + 1e-9
