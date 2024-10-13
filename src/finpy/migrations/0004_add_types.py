from finpy.core.errors import MigrationError

SCHEMA_VERSION = 4
DESCRIPTION = "Adds 'type' discriminator field to data payload to distinguish between Cashflow, Instrument, and Result schemas"


def upgrade(payload: dict) -> dict:
    if "data" not in payload or "version" not in payload:
        raise MigrationError("invalid payload for migration 0004")
    data = payload["data"]
    if "amount" in data and "t" in data:
        data["type"] = "cashflow"
    elif "face_value" in data:
        data["type"] = "instrument"
    else:
        data.setdefault("type", "result")
    return {"version": 4, "data": data}


def downgrade(payload: dict) -> dict:
    if not isinstance(payload, dict) or "data" not in payload:
        raise MigrationError("invalid schema-4 payload")
    data = payload["data"]
    data.pop("type", None)
    return {"version": 3, "data": data}
