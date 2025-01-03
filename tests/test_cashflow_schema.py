from decimal import Decimal
from hypothesis import given, strategies as st, assume
from finpy.core.types import Cashflow
from finpy.schemas.cashflow_schema import (
    dump_cashflow, load_cashflow, validate_cashflow,
    validate_cashflow_list, dump_cashflow_list,
    cashflow_to_json, cashflow_from_json,
    validate_cashflow_schedule,
)
from finpy.core.errors import SchemaValidationError
import pytest
import json


class TestCashflowSchema:
    def test_roundtrip(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        data = dump_cashflow(cf)
        cf2 = load_cashflow(data)
        assert cf == cf2

    def test_validation_error(self):
        with pytest.raises(SchemaValidationError):
            validate_cashflow({"bad": "data"})

    def test_validate_cashflow_list(self):
        data_list = [{"amount": "100", "t": 1.0}, {"amount": "200", "t": 2.0}]
        result = validate_cashflow_list(data_list)
        assert len(result) == 2
        assert result[0] == Cashflow(amount=Decimal("100"), t=1.0)
        assert result[1] == Cashflow(amount=Decimal("200"), t=2.0)

    def test_validate_cashflow_list_error(self):
        with pytest.raises(SchemaValidationError):
            validate_cashflow_list([{"bad": "data"}])

    def test_dump_cashflow_list(self):
        cflist = [Cashflow(amount=Decimal("100"), t=1.0), Cashflow(amount=Decimal("200"), t=2.0)]
        data = dump_cashflow_list(cflist)
        assert len(data) == 2
        assert data[0] == {"amount": "100", "t": 1.0}
        assert data[1] == {"amount": "200", "t": 2.0}

    def test_cashflow_to_json(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        json_str = cashflow_to_json(cf)
        parsed = json.loads(json_str)
        assert parsed["amount"] == "100"
        assert parsed["t"] == 1.0

    def test_cashflow_from_json(self):
        json_str = '{"amount": "150", "t": 2.5}'
        cf = cashflow_from_json(json_str)
        assert cf == Cashflow(amount=Decimal("150"), t=2.5)

    def test_cashflow_json_roundtrip(self):
        cf = Cashflow(amount=Decimal("250"), t=3.0)
        json_str = cashflow_to_json(cf)
        cf2 = cashflow_from_json(json_str)
        assert cf == cf2

    def test_validate_cashflow_schedule_valid(self):
        schedule = [{"amount": "100", "t": 1.0}, {"amount": "200", "t": 2.0}, {"amount": "300", "t": 3.0}]
        flows = validate_cashflow_schedule(schedule)
        assert len(flows) == 3

    def test_validate_cashflow_schedule_non_increasing(self):
        schedule = [{"amount": "100", "t": 2.0}, {"amount": "200", "t": 1.0}]
        with pytest.raises(SchemaValidationError):
            validate_cashflow_schedule(schedule)

    def test_validate_cashflow_schedule_single(self):
        schedule = [{"amount": "100", "t": 1.0}]
        flows = validate_cashflow_schedule(schedule)
        assert len(flows) == 1

    def test_validate_cashflow_missing_amount(self):
        with pytest.raises(SchemaValidationError):
            validate_cashflow({"t": 1.0})

    def test_validate_cashflow_missing_t(self):
        with pytest.raises(SchemaValidationError):
            validate_cashflow({"amount": "100"})

    def test_validate_cashflow_invalid_amount(self):
        with pytest.raises(SchemaValidationError):
            validate_cashflow({"amount": "not_a_number", "t": 1.0})

    def test_cashflow_equality(self):
        cf1 = Cashflow(amount=Decimal("100"), t=1.0)
        cf2 = Cashflow(amount=Decimal("100"), t=1.0)
        cf3 = Cashflow(amount=Decimal("200"), t=1.0)
        assert cf1 == cf2
        assert cf1 != cf3

    def test_cashflow_to_dict(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        d = cf.to_dict()
        assert d["amount"] == "100"
        assert d["t"] == 1.0

    def test_cashflow_from_dict(self):
        cf = Cashflow.from_dict({"amount": "100", "t": 1.0})
        assert cf == Cashflow(amount=Decimal("100"), t=1.0)

    def test_cashflow_negative_t_error(self):
        with pytest.raises(ValueError):
            Cashflow(amount=Decimal("100"), t=-1.0)

    def test_cashflow_is_zero(self):
        cf = Cashflow(amount=Decimal("0"), t=1.0)
        assert cf.is_zero()

    def test_cashflow_is_not_zero(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        assert not cf.is_zero()

    def test_cashflow_hash(self):
        cf1 = Cashflow(amount=Decimal("100"), t=1.0)
        cf2 = Cashflow(amount=Decimal("100"), t=1.0)
        assert hash(cf1) == hash(cf2)

    def test_cashflow_repr(self):
        cf = Cashflow(amount=Decimal("100"), t=1.0)
        r = repr(cf)
        assert "Cashflow" in r
        assert "100" in r

    def test_validate_cashflow_dump_roundtrip_batch(self):
        data_list = [{"amount": "50", "t": 0.5}, {"amount": "75", "t": 1.5}, {"amount": "100", "t": 2.5}]
        cfs = validate_cashflow_list(data_list)
        dumped = dump_cashflow_list(cfs)
        cfs2 = validate_cashflow_list(dumped)
        assert cfs == cfs2

    def test_cashflow_list_to_json_list(self):
        cflist = [Cashflow(amount=Decimal("100"), t=1.0), Cashflow(amount=Decimal("200"), t=2.0)]
        json_list = [cashflow_to_json(cf) for cf in cflist]
        for j, cf in zip(json_list, cflist):
            assert cashflow_from_json(j) == cf

    def test_validate_cashflow_schedule_duplicate_time(self):
        schedule = [{"amount": "100", "t": 1.0}, {"amount": "200", "t": 1.0}]
        with pytest.raises(SchemaValidationError):
            validate_cashflow_schedule(schedule)

    def test_cashflow_from_json_invalid(self):
        with pytest.raises(SchemaValidationError):
            cashflow_from_json('{"bad": "data"}')


@given(st.floats(-10000, 10000), st.floats(0, 10))
def test_cashflow_schema_roundtrip(amount, t):
    cf = Cashflow(amount=Decimal(str(amount)), t=t)
    data = dump_cashflow(cf)
    assert load_cashflow(data) == cf


@given(st.floats(-10000, 10000), st.floats(0, 10))
def test_cashflow_json_roundtrip_hypothesis(amount, t):
    cf = Cashflow(amount=Decimal(str(amount)), t=t)
    j = cashflow_to_json(cf)
    assert cashflow_from_json(j) == cf


@given(st.lists(st.floats(-1000, 1000), min_size=1, max_size=5), st.lists(st.floats(0, 10), min_size=1, max_size=5))
def test_cashflow_list_roundtrip_hypothesis(amounts, times):
    assume(len(amounts) == len(times))
    cflist = [Cashflow(amount=Decimal(str(a)), t=t) for a, t in zip(amounts, times)]
    dumped = dump_cashflow_list(cflist)
    loaded = validate_cashflow_list(dumped)
    assert cflist == loaded
