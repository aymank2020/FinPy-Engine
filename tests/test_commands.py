import pytest
from hypothesis import given, strategies as st
from finpy.cli.commands import _parse_floats


class TestParseFloats:
    def test_basic(self):
        result = _parse_floats("1,2,3")
        assert result == [1.0, 2.0, 3.0]

    def test_single_value(self):
        result = _parse_floats("42")
        assert result == [42.0]

    def test_negative_values(self):
        result = _parse_floats("-1,-2.5,3")
        assert result == [-1.0, -2.5, 3.0]

    def test_decimal_values(self):
        result = _parse_floats("1.5,2.75,3.0")
        assert result == [1.5, 2.75, 3.0]

    def test_with_spaces(self):
        result = _parse_floats("1, 2, 3")
        assert result == [1.0, 2.0, 3.0]

    def test_scientific_notation(self):
        result = _parse_floats("1e0,2e1,3e-1")
        assert result == [1.0, 20.0, 0.3]

    def test_trailing_comma(self):
        result = _parse_floats("1,2,")
        assert result == [1.0, 2.0]

    def test_empty_string_raises(self):
        import pytest
        with pytest.raises(ValueError):
            _parse_floats("")

    def test_whitespace_only_raises(self):
        import pytest
        with pytest.raises(ValueError):
            _parse_floats("   ")

    def test_non_numeric_raises(self):
        import pytest
        with pytest.raises(ValueError):
            _parse_floats("abc")

    def test_mixed_valid_invalid_raises(self):
        import pytest
        with pytest.raises(ValueError):
            _parse_floats("1,abc,3")

    def test_large_numbers(self):
        result = _parse_floats("1000000,0.000001")
        assert result == [1000000.0, 0.000001]

    def test_leading_zeros(self):
        result = _parse_floats("001,002.5")
        assert result == [1.0, 2.5]

    def test_multiple_commas(self):
        result = _parse_floats("10,20,30,40,50")
        assert result == [10.0, 20.0, 30.0, 40.0, 50.0]

    def test_commas_with_extra_whitespace(self):
        result = _parse_floats("  1 ,  2 ,  3  ")
        assert result == [1.0, 2.0, 3.0]

    def test_zero_values(self):
        result = _parse_floats("0,0.0,-0")
        assert result == [0.0, 0.0, 0.0]


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=10))
def test_parse_floats_roundtrip(values):
    csv = ",".join(str(v) for v in values)
    parsed = _parse_floats(csv)
    assert len(parsed) == len(values)
    for p, v in zip(parsed, values):
        assert p == pytest.approx(v)


@given(st.text())
def test_parse_floats_random_string(s):
    import pytest
    try:
        result = _parse_floats(s)
        assert all(isinstance(x, float) for x in result)
        assert len(result) >= 1
    except ValueError:
        pass
