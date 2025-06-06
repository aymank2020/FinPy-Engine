import importlib
import pytest
from finpy.migrations import _migration_registry
from finpy.core.errors import MigrationError

upgrade, downgrade = _migration_registry[2]
mod2 = importlib.import_module("finpy.migrations.0002_add_curve")


class TestMigration0002:
    def test_upgrade(self):
        payload = {"version": 1, "data": {"value": "100"}}
        result = upgrade(payload)
        assert result["version"] == 2
        assert result["data"].get("yield_curve") is None

    def test_downgrade(self):
        payload = {"version": 2, "data": {"value": "100", "yield_curve": None}}
        result = downgrade(payload)
        assert "yield_curve" not in result["data"]

    def test_upgrade_with_existing_curve(self):
        payload = {"version": 1, "data": {"value": "100", "yield_curve": {"1y": "0.05"}}}
        result = upgrade(payload)
        assert result["data"]["yield_curve"] == {"1y": "0.05"}

    def test_upgrade_missing_data(self):
        with pytest.raises(MigrationError):
            upgrade({"version": 1})

    def test_upgrade_missing_version(self):
        with pytest.raises(MigrationError):
            upgrade({"data": {"value": "100"}})

    def test_upgrade_invalid_payload(self):
        with pytest.raises(MigrationError):
            upgrade("invalid")

    def test_downgrade_with_curve(self):
        payload = {"version": 2, "data": {"value": "100", "yield_curve": {"1y": "0.05"}, "label": "test"}}
        result = downgrade(payload)
        assert "yield_curve" not in result["data"]
        assert result["data"]["value"] == "100"
        assert result["data"]["label"] == "test"

    def test_downgrade_missing_data(self):
        with pytest.raises(MigrationError):
            downgrade({"version": 2})

    def test_downgrade_invalid_payload_type(self):
        with pytest.raises(MigrationError):
            downgrade("invalid")

    def test_downgrade_non_dict_payload(self):
        with pytest.raises(MigrationError):
            downgrade(123)

    def test_downgrade_preserves_other_fields(self):
        payload = {"version": 2, "data": {"value": "100", "label": "test", "extra": "data"}}
        result = downgrade(payload)
        assert result["data"]["value"] == "100"
        assert result["data"]["label"] == "test"
        assert result["data"]["extra"] == "data"
        assert "yield_curve" not in result["data"]

    def test_schema_version(self):
        assert mod2.SCHEMA_VERSION == 2

    def test_upgrade_empty_data(self):
        payload = {"version": 1, "data": {}}
        result = upgrade(payload)
        assert result["version"] == 2
        assert result["data"] == {"yield_curve": None}

    def test_double_upgrade_idempotent(self):
        payload = {"version": 1, "data": {"value": "100"}}
        v2 = upgrade(payload)
        v2_again = upgrade(v2)
        assert v2_again["version"] == 2
        assert v2_again["data"]["yield_curve"] is None

    def test_upgrade_does_not_remove_existing_fields(self):
        payload = {"version": 1, "data": {"value": "100", "label": "test"}}
        result = upgrade(payload)
        assert result["data"]["value"] == "100"
        assert result["data"]["label"] == "test"
