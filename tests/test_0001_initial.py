import importlib
import pytest
from finpy.migrations import _migration_registry

upgrade, downgrade = _migration_registry[1]
from finpy.core.errors import MigrationError

mod1 = importlib.import_module("finpy.migrations.0001_initial")


class TestMigration0001:
    def test_upgrade(self):
        payload = {"value": "100", "label": "test"}
        result = upgrade(payload)
        assert result["version"] == 1
        assert result["data"]["value"] == "100"

    def test_downgrade(self):
        payload = {"version": 1, "data": {"value": "100", "label": "test"}}
        result = downgrade(payload)
        assert result["value"] == "100"

    def test_upgrade_missing_value(self):
        with pytest.raises(MigrationError):
            upgrade({})

    def test_upgrade_without_label(self):
        payload = {"value": "200"}
        result = upgrade(payload)
        assert result["version"] == 1
        assert result["data"]["value"] == "200"
        assert result["data"]["label"] == ""

    def test_upgrade_with_empty_label(self):
        payload = {"value": "300", "label": ""}
        result = upgrade(payload)
        assert result["data"]["label"] == ""

    def test_upgrade_preserves_label(self):
        payload = {"value": "400", "label": "mylabel"}
        result = upgrade(payload)
        assert result["data"]["label"] == "mylabel"

    def test_downgrade_returns_label(self):
        payload = {"version": 1, "data": {"value": "500", "label": "saved"}}
        result = downgrade(payload)
        assert result["label"] == "saved"

    def test_downgrade_missing_data(self):
        with pytest.raises(MigrationError):
            downgrade({"version": 1})

    def test_downgrade_non_dict(self):
        with pytest.raises(MigrationError):
            downgrade("not a dict")

    def test_downgrade_invalid_payload(self):
        with pytest.raises(MigrationError):
            downgrade(None)

    def test_schema_version(self):
        assert mod1.SCHEMA_VERSION == 1

    def test_upgrade_converts_value_to_string(self):
        payload = {"value": 999}
        result = upgrade(payload)
        assert isinstance(result["data"]["value"], str)
        assert result["data"]["value"] == "999"

    def test_downgrade_empty_label(self):
        payload = {"version": 1, "data": {"value": "", "label": ""}}
        result = downgrade(payload)
        assert result["value"] == ""
        assert result["label"] == ""

    def test_upgrade_numeric_label(self):
        payload = {"value": "123", "label": 456}
        result = upgrade(payload)
        assert result["data"]["label"] == 456
