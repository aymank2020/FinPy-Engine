from decimal import Decimal, DecimalException
from finpy.core.types import Instrument
from finpy.core.errors import SchemaValidationError


def validate_instrument(data: dict) -> Instrument:
    required = {"face_value", "coupon_rate", "maturity_years", "payments_per_year"}
    if not required.issubset(data.keys()):
        raise SchemaValidationError(f"instrument must have {required}")
    try:
        return Instrument(
            face_value=Decimal(str(data["face_value"])),
            coupon_rate=Decimal(str(data["coupon_rate"])),
            maturity_years=float(data["maturity_years"]),
            payments_per_year=int(data["payments_per_year"]),
        )
    except (ValueError, TypeError, DecimalException) as e:
        raise SchemaValidationError(str(e))


def dump_instrument(inst: Instrument) -> dict:
    return {
        "face_value": str(inst.face_value),
        "coupon_rate": str(inst.coupon_rate),
        "maturity_years": inst.maturity_years,
        "payments_per_year": inst.payments_per_year,
    }


def load_instrument(data: dict) -> Instrument:
    return validate_instrument(data)


def validate_instrument_list(data_list: list[dict]) -> list[Instrument]:
    return [validate_instrument(d) for d in data_list]


def dump_instrument_list(inst_list: list[Instrument]) -> list[dict]:
    return [dump_instrument(inst) for inst in inst_list]


def instrument_to_json(inst: Instrument) -> str:
    import json
    return json.dumps(dump_instrument(inst))


def instrument_from_json(json_str: str) -> Instrument:
    import json
    data = json.loads(json_str)
    return validate_instrument(data)


def validate_instrument_partial(data: dict) -> Instrument:
    face_value = Decimal(str(data.get("face_value", 1000)))
    coupon_rate = Decimal(str(data.get("coupon_rate", 0)))
    maturity_years = float(data.get("maturity_years", 1))
    payments_per_year = int(data.get("payments_per_year", 2))
    return Instrument(
        face_value=face_value,
        coupon_rate=coupon_rate,
        maturity_years=maturity_years,
        payments_per_year=payments_per_year,
    )
