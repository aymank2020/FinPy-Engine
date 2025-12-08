from decimal import Decimal
from hypothesis import given, strategies as st, assume
from finpy.core.types import Instrument
from finpy.schemas.instrument_schema import (
    dump_instrument, load_instrument, validate_instrument,
    validate_instrument_list, dump_instrument_list,
    instrument_to_json, instrument_from_json,
    validate_instrument_partial,
)
from finpy.core.errors import SchemaValidationError
import pytest
import json


class TestInstrumentSchema:
    def test_roundtrip(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        data = dump_instrument(inst)
        inst2 = load_instrument(data)
        assert inst == inst2

    def test_validate_instrument_missing_fields(self):
        with pytest.raises(SchemaValidationError):
            validate_instrument({"face_value": "1000"})

    def test_validate_instrument_list(self):
        data_list = [
            {"face_value": "1000", "coupon_rate": "0.05", "maturity_years": 5.0, "payments_per_year": 2},
            {"face_value": "500", "coupon_rate": "0.03", "maturity_years": 3.0, "payments_per_year": 12},
        ]
        result = validate_instrument_list(data_list)
        assert len(result) == 2
        assert result[0].face_value == Decimal("1000")
        assert result[1].face_value == Decimal("500")

    def test_validate_instrument_list_error(self):
        with pytest.raises(SchemaValidationError):
            validate_instrument_list([{"bad": "data"}])

    def test_dump_instrument_list(self):
        inst_list = [
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0),
            Instrument(face_value=Decimal("500"), coupon_rate=Decimal("0.03"), maturity_years=3.0),
        ]
        data = dump_instrument_list(inst_list)
        assert len(data) == 2
        assert data[0]["face_value"] == "1000"
        assert data[1]["face_value"] == "500"

    def test_instrument_to_json(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        j = instrument_to_json(inst)
        parsed = json.loads(j)
        assert parsed["face_value"] == "1000"
        assert parsed["coupon_rate"] == "0.05"

    def test_instrument_from_json(self):
        j = '{"face_value": "2000", "coupon_rate": "0.04", "maturity_years": 10.0, "payments_per_year": 4}'
        inst = instrument_from_json(j)
        assert inst.face_value == Decimal("2000")
        assert inst.coupon_rate == Decimal("0.04")

    def test_instrument_json_roundtrip(self):
        inst = Instrument(face_value=Decimal("5000"), coupon_rate=Decimal("0.06"), maturity_years=7.0)
        j = instrument_to_json(inst)
        inst2 = instrument_from_json(j)
        assert inst == inst2

    def test_validate_instrument_partial(self):
        inst = validate_instrument_partial({"face_value": "2000"})
        assert inst.face_value == Decimal("2000")
        assert inst.coupon_rate == Decimal("0")
        assert inst.maturity_years == 1.0
        assert inst.payments_per_year == 2

    def test_validate_instrument_partial_defaults(self):
        inst = validate_instrument_partial({})
        assert inst.face_value == Decimal("1000")
        assert inst.coupon_rate == Decimal("0")
        assert inst.maturity_years == 1.0
        assert inst.payments_per_year == 2

    def test_instrument_equality(self):
        inst1 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst2 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst3 = Instrument(face_value=Decimal("2000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst1 == inst2
        assert inst1 != inst3

    def test_instrument_to_dict(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        d = inst.to_dict()
        assert d["face_value"] == "1000"
        assert d["coupon_rate"] == "0.05"
        assert d["maturity_years"] == 5.0

    def test_instrument_from_dict(self):
        inst = Instrument.from_dict({"face_value": "1000", "coupon_rate": "0.05", "maturity_years": 5.0})
        assert inst.face_value == Decimal("1000")

    def test_instrument_coupon_amount(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst.coupon_amount() == Decimal("25")

    def test_instrument_total_payments(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert inst.total_payments() == 10

    def test_instrument_cashflows(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=1.0, payments_per_year=2)
        flows = inst.cashflows()
        assert len(flows) == 2
        assert flows[0].amount == Decimal("25")
        assert flows[1].amount == Decimal("1025")

    def test_instrument_invalid_face_value(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("-100"), coupon_rate=Decimal("0.05"), maturity_years=5.0)

    def test_instrument_invalid_coupon_rate(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("-0.05"), maturity_years=5.0)

    def test_instrument_invalid_maturity(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=0)

    def test_instrument_invalid_payments_per_year(self):
        with pytest.raises(ValueError):
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0, payments_per_year=3)

    def test_instrument_hash(self):
        inst1 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        inst2 = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        assert hash(inst1) == hash(inst2)

    def test_instrument_repr(self):
        inst = Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0)
        r = repr(inst)
        assert "Instrument" in r
        assert "1000" in r

    def test_instrument_list_roundtrip(self):
        inst_list = [
            Instrument(face_value=Decimal("1000"), coupon_rate=Decimal("0.05"), maturity_years=5.0),
            Instrument(face_value=Decimal("2000"), coupon_rate=Decimal("0.03"), maturity_years=10.0),
        ]
        dumped = dump_instrument_list(inst_list)
        loaded = validate_instrument_list(dumped)
        assert inst_list == loaded

    def test_instrument_from_json_invalid(self):
        with pytest.raises(SchemaValidationError):
            instrument_from_json('{"bad": "data"}')


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.floats(1, 20))
def test_instrument_schema_roundtrip(fv, cr, mat):
    inst = Instrument(face_value=Decimal(str(fv)), coupon_rate=Decimal(str(cr)), maturity_years=mat)
    data = dump_instrument(inst)
    assert load_instrument(data) == inst


@given(st.floats(100, 10000), st.floats(0.01, 0.15), st.floats(1, 20))
def test_instrument_json_roundtrip_hypothesis(fv, cr, mat):
    inst = Instrument(face_value=Decimal(str(fv)), coupon_rate=Decimal(str(cr)), maturity_years=mat)
    j = instrument_to_json(inst)
    assert instrument_from_json(j) == inst


@given(
    st.lists(st.floats(100, 5000), min_size=1, max_size=5),
    st.lists(st.floats(0.01, 0.12), min_size=1, max_size=5),
    st.lists(st.floats(1, 15), min_size=1, max_size=5),
)
def test_instrument_list_roundtrip_hypothesis(fvs, crs, mats):
    assume(len(fvs) == len(crs) == len(mats))
    inst_list = [Instrument(face_value=Decimal(str(fv)), coupon_rate=Decimal(str(cr)), maturity_years=mat) for fv, cr, mat in zip(fvs, crs, mats)]
    dumped = dump_instrument_list(inst_list)
    loaded = validate_instrument_list(dumped)
    assert inst_list == loaded
