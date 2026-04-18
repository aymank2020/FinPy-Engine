from decimal import Decimal
from hypothesis import given, strategies as st, assume
import pytest
from finpy.core.utils import (
    is_positive, is_non_negative, is_zero, clamp, sign,
    round_decimal, percentage_change, weighted_average,
    days_in_year, days_in_month, years_between,
    validate_rate, validate_positive, validate_non_negative,
    bucket_date, format_date, safe_divide, normalize_list,
    cumulative_sum, running_max, running_min, deduplicate,
    batch, safe_float, safe_decimal, moving_average, moving_sum,
    difference, lag, lead, rank, percentile, interquartile_range,
    is_outlier, z_score,
)


class TestIsPositive:
    def test_positive(self):
        assert is_positive(Decimal("1")) is True

    def test_zero(self):
        assert is_positive(Decimal("0")) is False

    def test_negative(self):
        assert is_positive(Decimal("-1")) is False


class TestIsNonNegative:
    def test_positive(self):
        assert is_non_negative(Decimal("1")) is True

    def test_zero(self):
        assert is_non_negative(Decimal("0")) is True

    def test_negative(self):
        assert is_non_negative(Decimal("-1")) is False


class TestIsZero:
    def test_zero(self):
        assert is_zero(Decimal("0")) is True

    def test_non_zero(self):
        assert is_zero(Decimal("1")) is False

    def test_negative_zero(self):
        assert is_zero(Decimal("-0")) is True


class TestClamp:
    def test_within_range(self):
        assert clamp(Decimal("5"), Decimal("0"), Decimal("10")) == Decimal("5")

    def test_below_low(self):
        assert clamp(Decimal("-5"), Decimal("0"), Decimal("10")) == Decimal("0")

    def test_above_high(self):
        assert clamp(Decimal("15"), Decimal("0"), Decimal("10")) == Decimal("10")

    def test_at_low(self):
        assert clamp(Decimal("0"), Decimal("0"), Decimal("10")) == Decimal("0")

    def test_at_high(self):
        assert clamp(Decimal("10"), Decimal("0"), Decimal("10")) == Decimal("10")

    def test_equal_bounds(self):
        assert clamp(Decimal("5"), Decimal("5"), Decimal("5")) == Decimal("5")


class TestSign:
    def test_positive(self):
        assert sign(Decimal("5")) == 1

    def test_negative(self):
        assert sign(Decimal("-5")) == -1

    def test_zero(self):
        assert sign(Decimal("0")) == 0

    def test_small_positive(self):
        assert sign(Decimal("0.0001")) == 1

    def test_small_negative(self):
        assert sign(Decimal("-0.0001")) == -1


class TestRoundDecimal:
    def test_basic(self):
        assert round_decimal(Decimal("1.23456"), 2) == Decimal("1.23")

    def test_round_up(self):
        assert round_decimal(Decimal("1.235"), 2) == Decimal("1.24")

    def test_default_ndigits(self):
        assert round_decimal(Decimal("1.2345678")) == Decimal("1.2346")

    def test_no_rounding(self):
        assert round_decimal(Decimal("1.5"), 1) == Decimal("1.5")

    def test_large_value(self):
        assert round_decimal(Decimal("123456.789"), 2) == Decimal("123456.79")


class TestPercentageChange:
    def test_increase(self):
        result = percentage_change(Decimal("100"), Decimal("110"))
        assert result == Decimal("0.1")

    def test_decrease(self):
        result = percentage_change(Decimal("100"), Decimal("90"))
        assert result == Decimal("-0.1")

    def test_no_change(self):
        result = percentage_change(Decimal("100"), Decimal("100"))
        assert result == Decimal("0")

    def test_zero_old(self):
        with pytest.raises(ZeroDivisionError):
            percentage_change(Decimal("0"), Decimal("100"))


class TestWeightedAverage:
    def test_basic(self):
        result = weighted_average([Decimal("10"), Decimal("20")], [Decimal("1"), Decimal("1")])
        assert result == Decimal("15")

    def test_unequal_weights(self):
        result = weighted_average([Decimal("10"), Decimal("20")], [Decimal("3"), Decimal("1")])
        assert result == Decimal("12.5")

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            weighted_average([Decimal("10")], [Decimal("1"), Decimal("2")])

    def test_zero_total_weight(self):
        with pytest.raises(ValueError):
            weighted_average([Decimal("10"), Decimal("20")], [Decimal("0"), Decimal("0")])

    def test_single_value(self):
        result = weighted_average([Decimal("42")], [Decimal("1")])
        assert result == Decimal("42")


class TestDaysInYear:
    def test_leap_year(self):
        assert days_in_year(2024) == 366

    def test_non_leap_year(self):
        assert days_in_year(2023) == 365

    def test_century_non_leap(self):
        assert days_in_year(1900) == 365

    def test_century_leap(self):
        assert days_in_year(2000) == 366


class TestDaysInMonth:
    def test_january(self):
        assert days_in_month(2023, 1) == 31

    def test_february_non_leap(self):
        assert days_in_month(2023, 2) == 28

    def test_february_leap(self):
        assert days_in_month(2024, 2) == 29

    def test_april(self):
        assert days_in_month(2023, 4) == 30

    def test_december(self):
        assert days_in_month(2023, 12) == 31


class TestYearsBetween:
    def test_same_year(self):
        assert years_between(2020, 2020) == 0

    def test_five_years(self):
        assert years_between(2020, 2025) == 5

    def test_negative(self):
        assert years_between(2025, 2020) == -5


class TestValidateRate:
    def test_valid(self):
        validate_rate(Decimal("0.05"))

    def test_negative_not_allowed(self):
        with pytest.raises(ValueError):
            validate_rate(Decimal("-0.05"))

    def test_negative_allowed(self):
        validate_rate(Decimal("-0.05"), allow_negative=True)

    def test_non_decimal(self):
        with pytest.raises(TypeError):
            validate_rate(0.05)


class TestValidatePositive:
    def test_valid(self):
        validate_positive(Decimal("1"))

    def test_zero(self):
        with pytest.raises(ValueError):
            validate_positive(Decimal("0"))

    def test_negative(self):
        with pytest.raises(ValueError):
            validate_positive(Decimal("-1"))


class TestValidateNonNegative:
    def test_valid_positive(self):
        validate_non_negative(Decimal("1"))

    def test_zero(self):
        validate_non_negative(Decimal("0"))

    def test_negative(self):
        with pytest.raises(ValueError):
            validate_non_negative(Decimal("-1"))


class TestBucketDate:
    def test_basic(self):
        result = bucket_date("2023-12-25")
        assert result == {"year": 2023, "month": 12, "day": 25}

    def test_january(self):
        result = bucket_date("2024-01-01")
        assert result == {"year": 2024, "month": 1, "day": 1}


class TestFormatDate:
    def test_basic(self):
        assert format_date(2023, 12, 25) == "2023-12-25"

    def test_single_digits(self):
        assert format_date(2024, 1, 1) == "2024-01-01"


class TestSafeDivide:
    def test_normal(self):
        result = safe_divide(Decimal("10"), Decimal("2"))
        assert result == Decimal("5")

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            safe_divide(Decimal("10"), Decimal("0"))

    def test_with_default(self):
        result = safe_divide(Decimal("10"), Decimal("0"), default=Decimal("0"))
        assert result == Decimal("0")

    def test_negative(self):
        result = safe_divide(Decimal("-10"), Decimal("2"))
        assert result == Decimal("-5")


class TestNormalizeList:
    def test_basic(self):
        result = normalize_list([Decimal("1"), Decimal("2"), Decimal("3")])
        assert sum(result, Decimal(0)) == pytest.approx(Decimal("1"), abs=Decimal("1e-10"))

    def test_all_zero(self):
        result = normalize_list([Decimal("0"), Decimal("0")])
        assert result == [Decimal("0"), Decimal("0")]

    def test_single_element(self):
        result = normalize_list([Decimal("5")])
        assert result == [Decimal("1")]


class TestCumulativeSum:
    def test_basic(self):
        result = cumulative_sum([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result == [Decimal("1"), Decimal("3"), Decimal("6")]

    def test_negative_values(self):
        result = cumulative_sum([Decimal("5"), Decimal("-3"), Decimal("2")])
        assert result == [Decimal("5"), Decimal("2"), Decimal("4")]

    def test_single(self):
        result = cumulative_sum([Decimal("7")])
        assert result == [Decimal("7")]

    def test_empty(self):
        result = cumulative_sum([])
        assert result == []


class TestRunningMax:
    def test_basic(self):
        result = running_max([Decimal("1"), Decimal("3"), Decimal("2")])
        assert result == [Decimal("1"), Decimal("3"), Decimal("3")]

    def test_decreasing(self):
        result = running_max([Decimal("3"), Decimal("2"), Decimal("1")])
        assert result == [Decimal("3"), Decimal("3"), Decimal("3")]

    def test_increasing(self):
        result = running_max([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result == [Decimal("1"), Decimal("2"), Decimal("3")]

    def test_negative(self):
        result = running_max([Decimal("-5"), Decimal("-3"), Decimal("-10")])
        assert result == [Decimal("-5"), Decimal("-3"), Decimal("-3")]


class TestRunningMin:
    def test_basic(self):
        result = running_min([Decimal("3"), Decimal("1"), Decimal("2")])
        assert result == [Decimal("3"), Decimal("1"), Decimal("1")]

    def test_increasing(self):
        result = running_min([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result == [Decimal("1"), Decimal("1"), Decimal("1")]

    def test_decreasing(self):
        result = running_min([Decimal("3"), Decimal("2"), Decimal("1")])
        assert result == [Decimal("3"), Decimal("2"), Decimal("1")]

    def test_negative(self):
        result = running_min([Decimal("-1"), Decimal("-5"), Decimal("-3")])
        assert result == [Decimal("-1"), Decimal("-5"), Decimal("-5")]


class TestDeduplicate:
    def test_basic(self):
        assert deduplicate([1, 2, 2, 3, 1, 3]) == [1, 2, 3]

    def test_no_duplicates(self):
        assert deduplicate([1, 2, 3]) == [1, 2, 3]

    def test_empty(self):
        assert deduplicate([]) == []

    def test_all_same(self):
        assert deduplicate([1, 1, 1]) == [1]

    def test_strings(self):
        assert deduplicate(["a", "b", "a", "c"]) == ["a", "b", "c"]

    def test_mixed_types(self):
        result = deduplicate([1, "1", 1])
        assert result == [1, "1"]


class TestBatch:
    def test_basic(self):
        assert batch([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_exact(self):
        assert batch([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_single_batch(self):
        assert batch([1, 2, 3], 5) == [[1, 2, 3]]

    def test_empty(self):
        assert batch([], 3) == []

    def test_size_one(self):
        assert batch([1, 2, 3], 1) == [[1], [2], [3]]


class TestSafeFloat:
    def test_basic(self):
        assert safe_float("3.14") == 3.14

    def test_integer_string(self):
        assert safe_float("42") == 42.0

    def test_negative(self):
        assert safe_float("-1.5") == -1.5

    def test_scientific(self):
        assert safe_float("1e5") == 100000.0


class TestSafeDecimal:
    def test_basic(self):
        assert safe_decimal("3.14") == Decimal("3.14")

    def test_integer_string(self):
        assert safe_decimal("42") == Decimal("42")


class TestMovingAverage:
    def test_basic(self):
        result = moving_average([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")], 2)
        assert result == [Decimal("1.5"), Decimal("2.5"), Decimal("3.5")]

    def test_window_equals_length(self):
        result = moving_average([Decimal("1"), Decimal("2"), Decimal("3")], 3)
        assert result == [Decimal("2")]

    def test_negative_window(self):
        with pytest.raises(ValueError):
            moving_average([Decimal("1")], 0)

    def test_insufficient_values(self):
        with pytest.raises(ValueError):
            moving_average([Decimal("1")], 5)

    def test_window_one(self):
        result = moving_average([Decimal("1"), Decimal("2"), Decimal("3")], 1)
        assert result == [Decimal("1"), Decimal("2"), Decimal("3")]


class TestMovingSum:
    def test_basic(self):
        result = moving_sum([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")], 2)
        assert result == [Decimal("3"), Decimal("5"), Decimal("7")]

    def test_window_one(self):
        result = moving_sum([Decimal("1"), Decimal("2"), Decimal("3")], 1)
        assert result == [Decimal("1"), Decimal("2"), Decimal("3")]

    def test_negative_window(self):
        with pytest.raises(ValueError):
            moving_sum([Decimal("1")], 0)


class TestDifference:
    def test_basic(self):
        result = difference([Decimal("1"), Decimal("3"), Decimal("6")])
        assert result == [Decimal("2"), Decimal("3")]

    def test_negative_diffs(self):
        result = difference([Decimal("5"), Decimal("3"), Decimal("1")])
        assert result == [Decimal("-2"), Decimal("-2")]

    def test_too_few_values(self):
        with pytest.raises(ValueError):
            difference([Decimal("1")])


class TestLag:
    def test_basic(self):
        result = lag([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result == [None, Decimal("1"), Decimal("2")]

    def test_two_periods(self):
        result = lag([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")], 2)
        assert result == [None, None, Decimal("1"), Decimal("2")]

    def test_invalid_periods(self):
        with pytest.raises(ValueError):
            lag([Decimal("1")], 0)


class TestLead:
    def test_basic(self):
        result = lead([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result == [Decimal("2"), Decimal("3"), None]

    def test_two_periods(self):
        result = lead([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")], 2)
        assert result == [Decimal("3"), Decimal("4"), None, None]

    def test_invalid_periods(self):
        with pytest.raises(ValueError):
            lead([Decimal("1")], 0)


class TestRank:
    def test_basic(self):
        result = rank([Decimal("3"), Decimal("1"), Decimal("2")])
        assert result == [1, 3, 2]

    def test_all_equal(self):
        result = rank([Decimal("5"), Decimal("5"), Decimal("5")])
        assert result == [1, 1, 1]

    def test_descending(self):
        result = rank([Decimal("10"), Decimal("20"), Decimal("30")])
        assert result == [3, 2, 1]


class TestPercentile:
    def test_median(self):
        result = percentile([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")], Decimal("0.5"))
        assert result == Decimal("3")

    def test_min(self):
        result = percentile([Decimal("1"), Decimal("2"), Decimal("3")], Decimal("0"))
        assert result == Decimal("1")

    def test_max(self):
        result = percentile([Decimal("1"), Decimal("2"), Decimal("3")], Decimal("1"))
        assert result == Decimal("3")

    def test_empty(self):
        with pytest.raises(ValueError):
            percentile([], Decimal("0.5"))

    def test_invalid_pct_low(self):
        with pytest.raises(ValueError):
            percentile([Decimal("1")], Decimal("-0.1"))

    def test_invalid_pct_high(self):
        with pytest.raises(ValueError):
            percentile([Decimal("1")], Decimal("1.1"))


class TestInterquartileRange:
    def test_basic(self):
        result = interquartile_range([Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")])
        assert result == Decimal("2")

    def test_small_dataset(self):
        result = interquartile_range([Decimal("1"), Decimal("2"), Decimal("3")])
        assert result >= Decimal("0")


class TestIsOutlier:
    def test_not_outlier(self):
        result = is_outlier(Decimal("3"), [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")])
        assert result is False

    def test_outlier(self):
        result = is_outlier(Decimal("100"), [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")])
        assert result is True

    def test_custom_factor(self):
        result = is_outlier(Decimal("6"), [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4"), Decimal("5")], factor=Decimal("10"))
        assert result is False


class TestZScore:
    def test_at_mean(self):
        result = z_score(Decimal("0"), Decimal("0"), Decimal("1"))
        assert result == Decimal("0")

    def test_one_std_above(self):
        result = z_score(Decimal("1"), Decimal("0"), Decimal("1"))
        assert result == Decimal("1")

    def test_zero_std(self):
        result = z_score(Decimal("5"), Decimal("5"), Decimal("0"))
        assert result == Decimal("0")

    def test_negative_value(self):
        result = z_score(Decimal("-2"), Decimal("0"), Decimal("1"))
        assert result == Decimal("-2")


@given(st.decimals(min_value=-1000, max_value=1000))
def test_sign_always_minus_one_zero_or_one(value):
    result = sign(value)
    assert result in (-1, 0, 1)


@given(st.decimals(min_value=-100, max_value=100), st.decimals(min_value=-100, max_value=100), st.decimals(min_value=-100, max_value=100))
def test_clamp_within_bounds(low, val, high):
    assume(low <= high)
    result = clamp(val, low, high)
    assert low <= result <= high


@given(st.decimals(min_value=1, max_value=1000))
def test_is_positive_always_true(value):
    assert is_positive(value) is True


@given(st.decimals(min_value=-1000, max_value=-1))
def test_is_positive_always_false(value):
    assert is_positive(value) is False
