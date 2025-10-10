from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.fx.historical_lookup import convert_as_of, rate_history, latest_rate
from finpy.fx.historical_lookup import rate_range, rate_min_max, rate_mean, rate_volatility
from finpy.core.errors import RateNotAvailableError, UnknownCurrencyError
from tests._helpers import approx_decimal


class TestConvertAsOf:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = convert_as_of(100, "USD", "EUR", "2024-01-01", history)
        assert result == Decimal("85")

    def test_missing_rate(self):
        with pytest.raises(RateNotAvailableError):
            convert_as_of(100, "USD", "EUR", "2099-01-01", {"USD/EUR": {}})

    def test_unknown_from(self):
        with pytest.raises(UnknownCurrencyError):
            convert_as_of(100, "XXX", "EUR", "2024-01-01", {"USD/EUR": {"2024-01-01": Decimal("0.85")}})

    def test_unknown_to(self):
        with pytest.raises(UnknownCurrencyError):
            convert_as_of(100, "USD", "YYY", "2024-01-01", {"USD/EUR": {"2024-01-01": Decimal("0.85")}})

    def test_missing_key_in_history(self):
        with pytest.raises(RateNotAvailableError):
            convert_as_of(100, "USD", "GBP", "2024-01-01", {"USD/EUR": {"2024-01-01": Decimal("0.85")}})

    def test_with_ndigits(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85678")}}
        result = convert_as_of(100, "USD", "EUR", "2024-01-01", history, ndigits=2)
        assert result == Decimal("85.68")

    def test_zero_amount(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = convert_as_of(0, "USD", "EUR", "2024-01-01", history)
        assert result == Decimal(0)

    def test_rate_gt_one(self):
        history = {"USD/JPY": {"2024-01-01": Decimal("110.0")}}
        result = convert_as_of(100, "USD", "JPY", "2024-01-01", history)
        assert result == Decimal("11000")

    def test_large_amount(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = convert_as_of(1e6, "USD", "EUR", "2024-01-01", history)
        assert result == Decimal("850000")


class TestRateHistory:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86")}}
        result = rate_history(history, "USD", "EUR")
        assert len(result) == 2
        assert result["2024-01-01"] == Decimal("0.85")

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            rate_history({"USD/EUR": {}}, "USD", "GBP")

    def test_empty_history(self):
        result = rate_history({"USD/EUR": {}}, "USD", "EUR")
        assert result == {}

    def test_multiple_rates(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86"), "2024-01-03": Decimal("0.87")}}
        result = rate_history(history, "USD", "EUR")
        assert len(result) == 3

    def test_rate_order_preserved(self):
        history = {"USD/EUR": {"b": Decimal("0.86"), "a": Decimal("0.85")}}
        result = rate_history(history, "USD", "EUR")
        assert len(result) == 2


class TestLatestRate:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86")}}
        result = latest_rate(history, "USD", "EUR")
        assert result == Decimal("0.86")

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            latest_rate({"USD/EUR": {}}, "USD", "GBP")

    def test_single_rate(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = latest_rate(history, "USD", "EUR")
        assert result == Decimal("0.85")

    def test_empty_dates(self):
        with pytest.raises(RateNotAvailableError):
            latest_rate({"USD/EUR": {}}, "USD", "EUR")

    def test_unsorted_dates(self):
        history = {"USD/EUR": {"2024-01-03": Decimal("0.87"), "2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86")}}
        result = latest_rate(history, "USD", "EUR")
        assert result == Decimal("0.87")


class TestRateRange:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86"), "2024-01-03": Decimal("0.87")}}
        result = rate_range(history, "USD", "EUR", "2024-01-01", "2024-01-02")
        assert len(result) == 2

    def test_no_rates_in_range(self):
        with pytest.raises(RateNotAvailableError):
            rate_range({"USD/EUR": {"2024-01-01": Decimal("0.85")}}, "USD", "EUR", "2025-01-01", "2025-01-02")

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            rate_range({"USD/EUR": {}}, "USD", "GBP", "2024-01-01", "2024-01-02")

    def test_exact_range(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86")}}
        result = rate_range(history, "USD", "EUR", "2024-01-01", "2024-01-02")
        assert len(result) == 2

    def test_single_date(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.86")}}
        result = rate_range(history, "USD", "EUR", "2024-01-01", "2024-01-01")
        assert len(result) == 1
        assert result["2024-01-01"] == Decimal("0.85")


class TestRateMinMax:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.87"), "2024-01-03": Decimal("0.86")}}
        result = rate_min_max(history, "USD", "EUR")
        assert result["min"] == Decimal("0.85")
        assert result["max"] == Decimal("0.87")

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            rate_min_max({"USD/EUR": {}}, "USD", "GBP")

    def test_single_rate(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = rate_min_max(history, "USD", "EUR")
        assert result["min"] == result["max"]

    def test_min_less_than_max(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.90")}}
        result = rate_min_max(history, "USD", "EUR")
        assert result["min"] < result["max"]

    def test_multiple(self):
        history = {"USD/EUR": {"a": Decimal("0.88"), "b": Decimal("0.85"), "c": Decimal("0.90")}}
        result = rate_min_max(history, "USD", "EUR")
        assert result["min"] == Decimal("0.85")
        assert result["max"] == Decimal("0.90")


class TestRateMean:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.87")}}
        result = rate_mean(history, "USD", "EUR")
        assert result == Decimal("0.86")

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            rate_mean({"USD/EUR": {}}, "USD", "GBP")

    def test_single_rate(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85")}}
        result = rate_mean(history, "USD", "EUR")
        assert result == Decimal("0.85")

    def test_empty_rates(self):
        with pytest.raises(RateNotAvailableError):
            rate_mean({"USD/EUR": {}}, "USD", "EUR")

    def test_three_rates(self):
        history = {"USD/EUR": {"a": Decimal("0.85"), "b": Decimal("0.87"), "c": Decimal("0.86")}}
        result = rate_mean(history, "USD", "EUR")
        assert result == Decimal("0.86")


class TestRateVolatility:
    def test_basic(self):
        history = {"USD/EUR": {"2024-01-01": Decimal("0.85"), "2024-01-02": Decimal("0.87"), "2024-01-03": Decimal("0.86")}}
        result = rate_volatility(history, "USD", "EUR")
        assert isinstance(result, Decimal)

    def test_missing_key(self):
        with pytest.raises(RateNotAvailableError):
            rate_volatility({"USD/EUR": {}}, "USD", "GBP")

    def test_too_few_rates(self):
        with pytest.raises(RateNotAvailableError):
            rate_volatility({"USD/EUR": {"2024-01-01": Decimal("0.85")}}, "USD", "EUR")

    def test_constant_rates(self):
        history = {"USD/EUR": {"a": Decimal("0.85"), "b": Decimal("0.85"), "c": Decimal("0.85")}}
        result = rate_volatility(history, "USD", "EUR")
        assert result == Decimal(0)

    def test_nonnegative(self):
        history = {"USD/EUR": {"a": Decimal("0.85"), "b": Decimal("0.87"), "c": Decimal("0.86"), "d": Decimal("0.88")}}
        result = rate_volatility(history, "USD", "EUR")
        assert result >= 0


@given(st.floats(0.01, 1000), st.floats(0.01, 10))
def test_convert_as_of_roundtrip(amount, rate):
    date_str = "2024-01-01"
    history = {"USD/EUR": {date_str: Decimal(str(rate))}}
    result = convert_as_of(amount, "USD", "EUR", date_str, history)
    inv_history = {"EUR/USD": {date_str: Decimal(1) / Decimal(str(rate))}}
    back = convert_as_of(float(result), "EUR", "USD", date_str, inv_history)
    assert back == pytest.approx(Decimal(str(amount)), abs=0.01)


@given(st.floats(0.01, 1000), st.floats(0.01, 10))
def test_convert_as_of_identity(amount, rate):
    date_str = "2024-01-01"
    history = {"USD/USD": {date_str: Decimal("1.0")}}
    result = convert_as_of(amount, "USD", "USD", date_str, history)
    assert result == Decimal(str(amount))


@given(st.lists(st.floats(0.8, 1.2), min_size=5, max_size=20))
def test_rate_volatility_nonnegative(rates):
    history = {"USD/EUR": {f"2024-01-{i+1:02d}": Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_volatility(history, "USD", "EUR")
    assert result >= 0


@given(st.lists(st.floats(0.8, 1.2), min_size=2, max_size=10))
def test_rate_min_max_correct(rates):
    history = {"USD/EUR": {str(i): Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_min_max(history, "USD", "EUR")
    assert result["min"] == pytest.approx(Decimal(str(min(rates))), abs=Decimal("1e-10"))
    assert result["max"] == pytest.approx(Decimal(str(max(rates))), abs=Decimal("1e-10"))


@given(st.lists(st.floats(0.8, 1.2), min_size=2, max_size=10))
def test_rate_mean_range(rates):
    history = {"USD/EUR": {str(i): Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_mean(history, "USD", "EUR")
    assert min(rates) <= float(result) <= max(rates)


@given(st.lists(st.floats(0.8, 1.2), min_size=2, max_size=10))
def test_rate_range_subset(rates):
    history = {"USD/EUR": {f"2024-01-{i+1:02d}": Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_range(history, "USD", "EUR", "2024-01-01", "2024-01-05")
    assert len(result) <= len(rates)
    if result:
        assert all("2024-01-01" <= d <= "2024-01-05" for d in result)


@given(st.floats(0.01, 1000), st.floats(0.01, 10))
def test_convert_as_of_ndigits(amount, rate):
    date_str = "2024-06-15"
    history = {"USD/EUR": {date_str: Decimal(str(rate))}}
    result = convert_as_of(amount, "USD", "EUR", date_str, history, ndigits=2)
    assert isinstance(result, Decimal)


@given(st.lists(st.floats(0.8, 1.2), min_size=3, max_size=10))
def test_rate_history_key_preserved(rates):
    history = {"USD/EUR": {f"2024-01-{i+1:02d}": Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_history(history, "USD", "EUR")
    assert len(result) == len(rates)


@given(st.lists(st.floats(0.8, 1.2), min_size=3, max_size=10))
def test_latest_rate_is_max_date(rates):
    history = {"USD/EUR": {f"2024-01-{i+1:02d}": Decimal(str(r)) for i, r in enumerate(rates)}}
    result = latest_rate(history, "USD", "EUR")
    assert result == Decimal(str(rates[-1]))


@given(st.lists(st.floats(0.8, 1.2), min_size=2, max_size=10))
def test_rate_range_inclusive_bounds(rates):
    history = {"USD/EUR": {f"2024-01-{i+1:02d}": Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_range(history, "USD", "EUR", "2024-01-01", f"2024-01-{len(rates):02d}")
    assert len(result) == len(rates)


@given(st.lists(st.floats(0.8, 1.2), min_size=2, max_size=10))
def test_rate_mean_within_bounds(rates):
    history = {"USD/EUR": {str(i): Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_mean(history, "USD", "EUR")
    assert min(rates) <= float(result) <= max(rates)


@given(st.lists(st.floats(0.8, 1.2), min_size=3, max_size=10))
def test_rate_volatility_output_type(rates):
    history = {"USD/EUR": {str(i): Decimal(str(r)) for i, r in enumerate(rates)}}
    result = rate_volatility(history, "USD", "EUR")
    assert isinstance(result, Decimal)
    assert result >= 0
