import importlib
import pytest
from finpy.migrations import _migration_registry

upgrade, downgrade = _migration_registry[4]
from finpy.core.errors import MigrationError
from finpy.migrations import get_latest_version, run_migrations, migrate_to_latest

mod4 = importlib.import_module("finpy.migrations.0004_add_types")


class TestMigration0004Upgrade:
    def test_upgrade_cashflow(self):
        payload = {"version": 3, "data": {"amount": 100.0, "t": "2024-01-01"}}
        result = upgrade(payload)
        assert result["version"] == 4
        assert result["data"]["type"] == "cashflow"

    def test_upgrade_instrument(self):
        payload = {"version": 3, "data": {"face_value": 1000}}
        result = upgrade(payload)
        assert result["version"] == 4
        assert result["data"]["type"] == "instrument"

    def test_upgrade_result_default(self):
        payload = {"version": 3, "data": {}}
        result = upgrade(payload)
        assert result["version"] == 4
        assert result["data"]["type"] == "result"

    def test_upgrade_result_preserves_existing_type(self):
        payload = {"version": 3, "data": {"type": "custom_result"}}
        result = upgrade(payload)
        assert result["version"] == 4
        assert result["data"]["type"] == "custom_result"

    def test_upgrade_cashflow_overrides_existing_type(self):
        payload = {"version": 3, "data": {"amount": 100, "t": "2024-01-01", "type": "custom"}}
        result = upgrade(payload)
        assert result["data"]["type"] == "cashflow"

    def test_upgrade_instrument_overrides_existing_type(self):
        payload = {"version": 3, "data": {"face_value": 1000, "type": "custom"}}
        result = upgrade(payload)
        assert result["data"]["type"] == "instrument"

    def test_upgrade_cashflow_priority_over_instrument(self):
        payload = {"version": 3, "data": {"amount": 100, "t": "2024-01-01", "face_value": 1000}}
        result = upgrade(payload)
        assert result["data"]["type"] == "cashflow"

    def test_upgrade_instrument_priority_over_result(self):
        payload = {"version": 3, "data": {"face_value": 1000}}
        result = upgrade(payload)
        assert result["data"]["type"] == "instrument"

    def test_upgrade_preserves_other_fields(self):
        payload = {"version": 3, "data": {"amount": 100, "label": "test", "yield_curve": "YC001"}}
        result = upgrade(payload)
        assert result["data"]["amount"] == 100
        assert result["data"]["label"] == "test"
        assert result["data"]["yield_curve"] == "YC001"

    def test_upgrade_missing_data(self):
        with pytest.raises(MigrationError, match="invalid payload for migration 0004"):
            upgrade({"version": 3})

    def test_upgrade_missing_version(self):
        with pytest.raises(MigrationError, match="invalid payload for migration 0004"):
            upgrade({"data": {}})

    def test_upgrade_missing_data_and_version(self):
        with pytest.raises(MigrationError, match="invalid payload for migration 0004"):
            upgrade({})


class TestMigration0004Downgrade:
    def test_downgrade_removes_type(self):
        payload = {"version": 4, "data": {"amount": 100.0, "type": "cashflow"}}
        result = downgrade(payload)
        assert result["version"] == 3
        assert "type" not in result["data"]

    def test_downgrade_no_type_present(self):
        payload = {"version": 4, "data": {"amount": 100.0}}
        result = downgrade(payload)
        assert result["version"] == 3
        assert "type" not in result["data"]

    def test_downgrade_preserves_other_fields(self):
        payload = {
            "version": 4,
            "data": {"amount": 100.0, "t": "2024-01-01", "type": "cashflow", "yield_curve": None},
        }
        result = downgrade(payload)
        assert result["version"] == 3
        assert "type" not in result["data"]
        assert result["data"]["amount"] == 100.0
        assert result["data"]["t"] == "2024-01-01"
        assert result["data"]["yield_curve"] is None

    def test_downgrade_missing_data_key(self):
        with pytest.raises(MigrationError, match="invalid schema-4 payload"):
            downgrade({"version": 4})

    def test_downgrade_non_dict_string(self):
        with pytest.raises(MigrationError, match="invalid schema-4 payload"):
            downgrade("not a dict")

    def test_downgrade_non_dict_list(self):
        with pytest.raises(MigrationError, match="invalid schema-4 payload"):
            downgrade(["a", "b"])

    def test_downgrade_none(self):
        with pytest.raises(MigrationError, match="invalid schema-4 payload"):
            downgrade(None)


class TestMigration0004Metadata:
    def test_schema_version(self):
        assert mod4.SCHEMA_VERSION == 4

    def test_description_is_nonempty_string(self):
        assert isinstance(mod4.DESCRIPTION, str)
        assert len(mod4.DESCRIPTION) > 0

    def test_registered_in_registry(self):
        assert 4 in _migration_registry
        assert _migration_registry[4] == (upgrade, downgrade)


class TestMigrationsInit:
    def test_get_latest_version(self):
        assert get_latest_version() == 4

    def test_run_migrations_same_version_returns_payload_unchanged(self):
        payload = {"custom": "data"}
        result = run_migrations(payload, 2, 2)
        assert result is payload
        assert result == {"custom": "data"}

    def test_run_migrations_upgrade_missing_version(self):
        with pytest.raises(ValueError, match="No migration for version 5"):
            run_migrations({"value": "100", "label": "test"}, 0, 5)

    def test_run_migrations_downgrade_missing_version(self):
        with pytest.raises(ValueError, match="No migration for version 5"):
            run_migrations({}, 5, 0)

    def test_run_migrations_full_upgrade_from_zero(self):
        payload = {"value": "100", "label": "test"}
        result = run_migrations(payload, 0, 4)
        assert result["version"] == 4
        assert result["data"]["amount"] == "100"
        assert result["data"]["label"] == "test"
        assert result["data"]["yield_curve"] is None
        assert result["data"]["type"] == "result"

    def test_run_migrations_single_step_upgrade_v3_to_v4(self):
        payload = {"version": 3, "data": {"amount": "100", "label": "test"}}
        result = run_migrations(payload, 3, 4)
        assert result["version"] == 4
        assert result["data"]["type"] == "result"

    def test_run_migrations_single_step_downgrade_v4_to_v3(self):
        payload = {"version": 4, "data": {"amount": "100", "type": "cashflow"}}
        result = run_migrations(payload, 4, 3)
        assert result["version"] == 3
        assert "type" not in result["data"]

    def test_run_migrations_full_downgrade(self):
        payload = {
            "version": 4,
            "data": {"amount": "100", "label": "test", "yield_curve": None, "type": "result"},
        }
        result = run_migrations(payload, 4, 0)
        assert "version" not in result
        assert result["value"] == "100"
        assert result["label"] == "test"

    def test_migrate_to_latest_from_v0(self):
        payload = {"value": "100", "label": "test"}
        result = migrate_to_latest(payload)
        assert result["version"] == 4

    def test_migrate_to_latest_already_latest(self):
        payload = {"version": 4, "data": {"amount": "100", "type": "result"}}
        result = migrate_to_latest(payload)
        assert result is payload
        assert result["version"] == 4

    def test_migrate_to_latest_no_version_defaults_to_zero(self):
        payload = {"value": "200"}
        result = migrate_to_latest(payload)
        assert result["version"] == 4

    def test_migrate_to_latest_version_above_latest_raises(self):
        payload = {"version": 10, "data": {}}
        with pytest.raises(ValueError, match="No migration for version 10"):
            migrate_to_latest(payload)
