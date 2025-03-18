from decimal import Decimal
from hypothesis import given, strategies as st
from finpy.cli.formatters import (
    format_decimal, format_percent, format_currency,
    format_with_commas, format_table, format_bold,
    format_green, format_red, format_yellow, format_header,
)


class TestFormatDecimal:
    def test_basic(self):
        result = format_decimal(Decimal("123.4567"), 2)
        assert result == "123.46"

    def test_zero(self):
        result = format_decimal(Decimal("0"), 2)
        assert result == "0.00"

    def test_negative(self):
        result = format_decimal(Decimal("-123.456"), 2)
        assert result == "-123.46"

    def test_large_number(self):
        result = format_decimal(Decimal("1234567.891"), 2)
        assert result == "1234567.89"

    def test_small_number(self):
        result = format_decimal(Decimal("0.00012345"), 6)
        assert result == "0.000123"

    def test_no_rounding(self):
        result = format_decimal(Decimal("42"), 0)
        assert result == "42"

    def test_default_ndigits(self):
        result = format_decimal(Decimal("1.23456789"))
        assert result == "1.2346"

    def test_rounding_up(self):
        result = format_decimal(Decimal("9.9999"), 2)
        assert result == "10.00"


class TestFormatPercent:
    def test_basic(self):
        result = format_percent(Decimal("0.05"), 2)
        assert result == "5.00%"

    def test_hundred_percent(self):
        result = format_percent(Decimal("1"), 0)
        assert result == "100%"

    def test_zero(self):
        result = format_percent(Decimal("0"), 2)
        assert result == "0.00%"

    def test_large_percent(self):
        result = format_percent(Decimal("2.5"), 2)
        assert result == "250.00%"

    def test_negative(self):
        result = format_percent(Decimal("-0.10"), 2)
        assert result == "-10.00%"


class TestFormatCurrency:
    def test_basic(self):
        result = format_currency(Decimal("123.45"), "$", 2)
        assert result == "$123.45"

    def test_default_symbol(self):
        result = format_currency(Decimal("99.99"))
        assert result == "$99.99"

    def test_euro_symbol(self):
        result = format_currency(Decimal("50"), chr(8364), 2)
        assert chr(8364) in result

    def test_zero(self):
        result = format_currency(Decimal("0"), "$", 2)
        assert result == "$0.00"

    def test_negative(self):
        result = format_currency(Decimal("-50"), "$", 2)
        assert result == "$-50.00"


class TestFormatWithCommas:
    def test_basic(self):
        result = format_with_commas(Decimal("1234567.89"), 2)
        assert result == "1,234,567.89"

    def test_no_decimals(self):
        result = format_with_commas(Decimal("1000"), 0)
        assert result == "1,000"

    def test_small_number(self):
        result = format_with_commas(Decimal("12.34"), 2)
        assert result == "12.34"

    def test_negative(self):
        result = format_with_commas(Decimal("-1000"), 2)
        assert result == "-1,000.00"

    def test_zero(self):
        result = format_with_commas(Decimal("0"), 2)
        assert result == "0.00"

    def test_large(self):
        result = format_with_commas(Decimal("1000000000"), 2)
        assert result == "1,000,000,000.00"

    def test_many_decimals(self):
        result = format_with_commas(Decimal("1234.5678"), 4)
        assert result == "1,234.5678"


class TestFormatTable:
    def test_basic(self):
        result = format_table(["Name", "Value"], [["A", "1"], ["B", "2"]])
        assert "Name" in result
        assert "Value" in result
        assert "A" in result

    def test_empty_rows(self):
        result = format_table(["Name", "Value"], [])
        assert result == ""

    def test_single_row(self):
        result = format_table(["X"], [["Y"]])
        assert "X" in result
        assert "Y" in result

    def test_column_alignment(self):
        result = format_table(["A", "B"], [["1", "2"]], padding=1)
        assert "A" in result
        assert "1" in result

    def test_uneven_cells(self):
        result = format_table(["A"], [["1", "2"]], padding=1)
        assert result


class TestStyleFormatters:
    def test_format_bold(self):
        result = format_bold("text")
        assert "\033[1m" in result
        assert "text" in result
        assert "\033[0m" in result

    def test_format_green(self):
        result = format_green("text")
        assert "\033[92m" in result

    def test_format_red(self):
        result = format_red("text")
        assert "\033[91m" in result

    def test_format_yellow(self):
        result = format_yellow("text")
        assert "\033[93m" in result

    def test_format_header(self):
        result = format_header("Hello", 20)
        assert "=" in result
        assert "Hello" in result

    def test_format_header_default_width(self):
        result = format_header("Test")
        assert len(result.split("\n")[0]) == 60


@given(st.floats(-1e6, 1e6), st.integers(0, 10))
def test_format_decimal_roundtrip(value, ndigits):
    d = Decimal(str(value))
    formatted = format_decimal(d, ndigits)
    assert isinstance(formatted, str)
    assert len(formatted) > 0


@given(st.floats(0, 1))
def test_format_percent_range(value):
    d = Decimal(str(value))
    result = format_percent(d, 2)
    assert "%" in result
    assert float(result.replace("%", "")) >= 0
