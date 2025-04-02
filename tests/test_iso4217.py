from decimal import Decimal
import pytest
from hypothesis import given, strategies as st, assume
from finpy.fx.iso4217 import is_valid_currency, list_currencies, currency_name
from finpy.fx.iso4217 import currency_symbol, add_currency
from tests._helpers import approx_decimal


class TestISO4217:
    def test_valid(self):
        assert is_valid_currency("USD") is True
        assert is_valid_currency("eur") is True

    def test_invalid(self):
        assert is_valid_currency("XYZ") is False

    def test_case_insensitivity(self):
        assert is_valid_currency("usd") is True
        assert is_valid_currency("UsD") is True

    def test_empty_string(self):
        assert is_valid_currency("") is False

    def test_numeric_code(self):
        assert is_valid_currency("123") is False

    def test_partial_code(self):
        assert is_valid_currency("US") is False
        assert is_valid_currency("USDD") is False


class TestListCurrencies:
    def test_basic(self):
        currencies = list_currencies()
        assert isinstance(currencies, list)
        assert len(currencies) > 0

    def test_contains_major(self):
        currencies = list_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies

    def test_sorted(self):
        currencies = list_currencies()
        assert currencies == sorted(currencies)

    def test_all_uppercase(self):
        currencies = list_currencies()
        assert all(c == c.upper() for c in currencies)

    def test_all_three_letters(self):
        currencies = list_currencies()
        assert all(len(c) == 3 for c in currencies)


class TestCurrencyName:
    def test_usd(self):
        assert currency_name("USD") == "US Dollar"

    def test_eur(self):
        assert currency_name("EUR") == "Euro"

    def test_case_insensitive(self):
        assert currency_name("usd") == "US Dollar"
        assert currency_name("UsD") == "US Dollar"

    def test_unknown(self):
        with pytest.raises(ValueError):
            currency_name("XYZ")

    def test_jpy(self):
        assert currency_name("JPY") == "Japanese Yen"

    def test_gbp(self):
        assert currency_name("GBP") == "British Pound"

    def test_all_valid_have_names(self):
        for code in list_currencies():
            name = currency_name(code)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_empty_string(self):
        with pytest.raises(ValueError):
            currency_name("")


class TestCurrencySymbol:
    def test_usd(self):
        assert currency_symbol("USD") == "$"

    def test_eur(self):
        assert currency_symbol("EUR") == "\u20ac"

    def test_case_insensitive(self):
        assert currency_symbol("usd") == "$"
        assert currency_symbol("UsD") == "$"

    def test_unknown(self):
        with pytest.raises(ValueError):
            currency_symbol("XYZ")

    def test_gbp(self):
        assert currency_symbol("GBP") == "\u00a3"

    def test_jpy(self):
        assert currency_symbol("JPY") == "\u00a5"

    def test_all_valid_have_symbol(self):
        for code in list_currencies():
            symbol = currency_symbol(code)
            assert isinstance(symbol, str)
            assert len(symbol) > 0

    def test_empty_string(self):
        with pytest.raises(ValueError):
            currency_symbol("")


class TestAddCurrency:
    def test_add_new(self):
        add_currency("ABC", "Test Currency", "T")
        assert is_valid_currency("ABC")
        assert currency_name("ABC") == "Test Currency"
        assert currency_symbol("ABC") == "T"

    def test_add_without_symbol(self):
        add_currency("DEF", "Another Currency")
        assert is_valid_currency("DEF")
        assert currency_name("DEF") == "Another Currency"
        with pytest.raises(ValueError):
            currency_symbol("DEF")

    def test_add_without_name(self):
        add_currency("GHI", "")
        assert is_valid_currency("GHI")
        with pytest.raises(ValueError):
            currency_name("GHI")

    def test_case_normalized(self):
        add_currency("xyz", "Test", "$")
        assert is_valid_currency("XYZ")

    def test_duplicate_add(self):
        add_currency("ZZZ", "Dup Currency", "D")
        add_currency("zzz", "Overwritten", "O")
        assert is_valid_currency("ZZZ")
        assert currency_name("ZZZ") == "Overwritten"
        assert currency_symbol("ZZZ") == "O"


@given(st.text(alphabet=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), min_size=3, max_size=3))
def test_currency_validation_random(code):
    valid = is_valid_currency(code)
    assert isinstance(valid, bool)


@given(st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]))
def test_currency_name_not_empty(code):
    name = currency_name(code)
    assert len(name) > 0


@given(st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]))
def test_currency_symbol_not_empty(code):
    symbol = currency_symbol(code)
    assert len(symbol) > 0


@given(st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF"]))
def test_currency_case_roundtrip(code):
    assert is_valid_currency(code.lower())
    assert is_valid_currency(code)


@given(st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]))
def test_currency_name_lookup_stable(code):
    name1 = currency_name(code)
    name2 = currency_name(code)
    assert name1 == name2


@given(st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF"]))
def test_currency_symbol_not_numeric(code):
    symbol = currency_symbol(code)
    assert not symbol.isdigit()


@given(st.text(alphabet=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), min_size=4, max_size=4))
def test_invalid_currency_long(code):
    assert is_valid_currency(code) is False


@given(st.text(alphabet=list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"), min_size=2, max_size=2))
def test_invalid_currency_short(code):
    assert is_valid_currency(code) is False


def test_currency_name_all_major():
    for code in ["USD", "EUR", "GBP", "JPY", "CHF"]:
        name = currency_name(code)
        assert isinstance(name, str)


def test_currency_symbol_all_major():
    for code in ["USD", "EUR", "GBP", "JPY", "CHF"]:
        symbol = currency_symbol(code)
        assert isinstance(symbol, str)


def test_list_currencies_all_valid():
    for code in list_currencies():
        assert is_valid_currency(code)


def test_add_currency_then_remove():
    add_currency("ZZZ", "Test Currency", "$")
    assert is_valid_currency("ZZZ")


def test_list_currencies_after_add():
    before = set(list_currencies())
    add_currency("QQQ", "New Currency")
    after = set(list_currencies())
    assert "QQQ" in after
    assert before.issubset(after)


def test_currency_name_all_listed():
    for code in list_currencies():
        try:
            name = currency_name(code)
            assert name
        except ValueError:
            pass


def test_currency_symbol_all_listed():
    for code in list_currencies():
        try:
            symbol = currency_symbol(code)
            assert symbol
        except ValueError:
            pass


def test_currency_name_jpy_yen():
    assert currency_name("JPY") == "Japanese Yen"


def test_currency_symbol_gbp_pound():
    assert currency_symbol("GBP") == "\u00a3"


def test_currency_symbol_eur_euro():
    assert currency_symbol("EUR") == "\u20ac"


def test_currency_symbol_jpy_yen():
    assert currency_symbol("JPY") == "\u00a5"


def test_currency_symbol_chf():
    assert currency_symbol("CHF") == "Fr"
