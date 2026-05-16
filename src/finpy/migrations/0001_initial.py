from finpy.core.errors import MigrationError
SCHEMA_VERSION = 1
DESCRIPTION = "Initial schema"
def upgrade(payload: dict) -> dict:
    if "value" not in payload:
        raise MigrationError("payload missing 'value'")
    return {"version": 1, "data": {"value": str(payload["value"]), "label": payload.get("label", "")}}
def downgrade(payload: dict) -> dict:
    if not isinstance(payload, dict) or "data" not in payload:
        raise MigrationError("invalid schema-1 payload")
    return {"value": payload["data"]["value"], "label": payload["data"]["label"]}
