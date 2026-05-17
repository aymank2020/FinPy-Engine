from decimal import Decimal
from hypothesis import given, strategies as st
from finpy.core.types import Result
from finpy.schemas.result_schema import (
    dump_result, load_result, validate_result,
    validate_result_list, dump_result_list,
    result_to_json, result_from_json, result_table,
)
from finpy.core.errors import SchemaValidationError
import pytest
import json


class TestResultSchema:
    def test_roundtrip(self):
        r = Result(value=Decimal("100"), label="test")
        data = dump_result(r)
        r2 = load_result(data)
        assert r == r2

    def test_validate_result_list(self):
        data_list = [{"value": "100", "label": "a"}, {"value": "200", "label": "b"}]
        results = validate_result_list(data_list)
        assert len(results) == 2
        assert results[0] == Result(value=Decimal("100"), label="a")
        assert results[1] == Result(value=Decimal("200"), label="b")

    def test_validate_result_list_error(self):
        with pytest.raises(SchemaValidationError):
            validate_result_list([{"bad": "data"}])

    def test_dump_result_list(self):
        rlist = [Result(value=Decimal("100"), label="a"), Result(value=Decimal("200"), label="b")]
        data = dump_result_list(rlist)
        assert len(data) == 2
        assert data[0] == {"value": "100", "label": "a"}
        assert data[1] == {"value": "200", "label": "b"}

    def test_result_to_json(self):
        r = Result(value=Decimal("150.25"), label="test")
        j = result_to_json(r)
        parsed = json.loads(j)
        assert parsed["value"] == "150.25"
        assert parsed["label"] == "test"

    def test_result_from_json(self):
        j = '{"value": "250.50", "label": "myresult"}'
        r = result_from_json(j)
        assert r == Result(value=Decimal("250.50"), label="myresult")

    def test_result_json_roundtrip(self):
        r = Result(value=Decimal("99.99"), label="roundtrip")
        j = result_to_json(r)
        r2 = result_from_json(j)
        assert r == r2

    def test_result_table(self):
        results = [Result(value=Decimal("100"), label="first"), Result(value=Decimal("200"), label="second")]
        table = result_table(results)
        assert "first" in table
        assert "second" in table
        assert "Label" in table
        assert "Value" in table

    def test_result_table_empty_labels(self):
        results = [Result(value=Decimal("100")), Result(value=Decimal("200"), label="labeled")]
        table = result_table(results)
        assert "labeled" in table
        assert "100" in table

    def test_result_table_single(self):
        table = result_table([Result(value=Decimal("50"), label="single")])
        assert "single" in table

    def test_result_missing_value(self):
        with pytest.raises(SchemaValidationError):
            validate_result({"label": "test"})

    def test_result_validation_error(self):
        with pytest.raises(SchemaValidationError):
            validate_result({"value": "not_a_number"})

    def test_result_invalid_type(self):
        with pytest.raises(SchemaValidationError):
            validate_result({"value": {}})

    def test_result_equality(self):
        r1 = Result(value=Decimal("100"), label="a")
        r2 = Result(value=Decimal("100"), label="a")
        r3 = Result(value=Decimal("200"), label="a")
        assert r1 == r2
        assert r1 != r3

    def test_result_to_dict(self):
        r = Result(value=Decimal("100"), label="test")
        d = r.to_dict()
        assert d["value"] == "100"
        assert d["label"] == "test"

    def test_result_from_dict(self):
        r = Result.from_dict({"value": "100", "label": "test"})
        assert r == Result(value=Decimal("100"), label="test")

    def test_result_add(self):
        r1 = Result(value=Decimal("100"))
        r2 = Result(value=Decimal("200"))
        r3 = r1 + r2
        assert r3.value == Decimal("300")

    def test_result_sub(self):
        r1 = Result(value=Decimal("200"))
        r2 = Result(value=Decimal("50"))
        r3 = r1 - r2
        assert r3.value == Decimal("150")

    def test_result_mul(self):
        r = Result(value=Decimal("100"))
        r2 = r * Decimal("2")
        assert r2.value == Decimal("200")

    def test_result_truediv(self):
        r = Result(value=Decimal("100"))
        r2 = r / Decimal("2")
        assert r2.value == Decimal("50")

    def test_result_truediv_zero(self):
        r = Result(value=Decimal("100"))
        with pytest.raises(ZeroDivisionError):
            r / Decimal("0")

    def test_result_hash(self):
        r1 = Result(value=Decimal("100"), label="a")
        r2 = Result(value=Decimal("100"), label="a")
        assert hash(r1) == hash(r2)

    def test_result_repr(self):
        r = Result(value=Decimal("100"), label="test")
        rep = repr(r)
        assert "Result" in rep
        assert "100" in rep

    def test_result_default_label(self):
        r = Result(value=Decimal("100"))
        assert r.label == ""

    def test_result_list_roundtrip(self):
        rlist = [Result(value=Decimal("100"), label="a"), Result(value=Decimal("200"), label="b")]
        dumped = dump_result_list(rlist)
        loaded = validate_result_list(dumped)
        assert rlist == loaded

    def test_result_from_json_invalid(self):
        with pytest.raises(SchemaValidationError):
            result_from_json('{"bad": "data"}')


@given(st.floats(-1e6, 1e6), st.text())
def test_result_schema_roundtrip(value, label):
    r = Result(value=Decimal(str(value)), label=label)
    data = dump_result(r)
    assert load_result(data) == r


@given(st.floats(-1e6, 1e6), st.text())
def test_result_json_roundtrip_hypothesis(value, label):
    r = Result(value=Decimal(str(value)), label=label)
    j = result_to_json(r)
    assert result_from_json(j) == r


@given(st.lists(st.floats(-1e5, 1e5), min_size=1, max_size=10), st.lists(st.text(), min_size=1, max_size=10))
def test_result_list_roundtrip_hypothesis(values, labels):
    rlist = [Result(value=Decimal(str(v)), label=l) for v, l in zip(values, labels)]
    dumped = dump_result_list(rlist)
    loaded = validate_result_list(dumped)
    assert rlist == loaded
