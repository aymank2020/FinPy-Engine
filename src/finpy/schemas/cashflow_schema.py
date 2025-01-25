"""JSON ↔ Cashflow conversion + schedule validators."""

from decimal import Decimal, InvalidOperation
import json

from finpy.core.types import Cashflow
from finpy.core.errors import SchemaValidationError


def validate_cashflow(data: dict) -> Cashflow:
    if not isinstance(data, dict):
        raise SchemaValidationError("cashflow payload must be a mapping")
    if "amount" not in data or "t" not in data:
        raise SchemaValidationError("cashflow must have 'amount' and 't' fields")
    try:
        return Cashflow(amount=Decimal(str(data["amount"])), t=float(data["t"]))
    except (ValueError, TypeError, InvalidOperation) as e:
        raise SchemaValidationError(str(e))


def dump_cashflow(cf: Cashflow) -> dict:
    return {"amount": str(cf.amount), "t": cf.t}


def load_cashflow(data: dict) -> Cashflow:
    return validate_cashflow(data)


def validate_cashflow_list(items: list):
    if not isinstance(items, list):
        raise SchemaValidationError("expected a list of cashflow payloads")
    return [validate_cashflow(item) for item in items]


def dump_cashflow_list(cflist):
    return [dump_cashflow(c) for c in cflist]


def cashflow_to_json(cf: Cashflow) -> str:
    return json.dumps(dump_cashflow(cf))


def cashflow_from_json(text: str) -> Cashflow:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"invalid JSON: {e}")
    return validate_cashflow(data)


def validate_cashflow_schedule(items: list):
    """Like validate_cashflow_list but enforces strictly increasing t."""
    flows = validate_cashflow_list(items)
    for i in range(1, len(flows)):
        if flows[i].t <= flows[i - 1].t:
            raise SchemaValidationError(
                f"cashflow times must be strictly increasing; "
                f"got t[{i - 1}]={flows[i - 1].t} t[{i}]={flows[i].t}"
            )
    return flows
