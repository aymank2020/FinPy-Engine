import importlib
import pytest
from hypothesis import given, strategies as st
from finpy.migrations import _migration_registry
from finpy.core.errors import MigrationError

upgrade_3, downgrade_3 = _migration_registry[3]
upgrade_2, downgrade_2 = _migration_registry[2]
upgrade_1, downgrade_1 = _migration_registry[1]
mod3 = importlib.import_module("finpy.migrations.0003_rename_field")


class TestMigration0003:
    def test_upgrade(self):
        payload = {"version": 2, "data": {"value": "100"}}
        result = upgrade_3(payload)
        assert result["data"]["amount"] == "100"
        assert "value" not in result["data"]

    def test_downgrade(self):
        payload = {"version": 3, "data": {"amount": "100"}}
        result = downgrade_3(payload)
        assert result["data"]["value"] == "100"

    def test_missing_fields(self):
        with pytest.raises(MigrationError):
            upgrade_3({"version": 2, "data": {}})

    def test_upgrade_when_already_amount(self):
        payload = {"version": 2, "data": {"amount": "200", "value": "100"}}
        result = upgrade_3(payload)
        assert result["data"]["amount"] == "100"
        assert "value" not in result["data"]

    def test_upgrade_with_only_amount(self):
        payload = {"version": 2, "data": {"amount": "300"}}
        result = upgrade_3(payload)
        assert result["data"]["amount"] == "300"
        assert "value" not in result["data"]

    def test_downgrade_when_no_amount(self):
        payload = {"version": 3, "data": {"value": "400"}}
        result = downgrade_3(payload)
        assert result["data"]["value"] == "400"

    def test_downgrade_preserves_other_fields(self):
        payload = {"version": 3, "data": {"amount": "100", "label": "test", "yield_curve": None}}
        result = downgrade_3(payload)
        assert result["data"]["value"] == "100"
        assert result["data"]["label"] == "test"
        assert "yield_curve" in result["data"]

    def test_migration_error_no_data(self):
        with pytest.raises(MigrationError):
            upgrade_3({"version": 2})

    def test_migration_error_no_version(self):
        with pytest.raises(MigrationError):
            upgrade_3({"data": {"value": "100"}})

    def test_downgrade_invalid_payload(self):
        with pytest.raises(MigrationError):
            downgrade_3(None)

    def test_downgrade_non_dict_payload(self):
        with pytest.raises(MigrationError):
            downgrade_3("invalid")

    def test_full_migration_chain(self):
        v0 = {"value": "500"}
        v1 = upgrade_1(v0)
        v2 = upgrade_2(v1)
        v3 = upgrade_3(v2)
        assert v3["data"]["amount"] == "500"
        assert "value" not in v3["data"]
        u2 = downgrade_3(v3)
        assert u2["data"]["value"] == "500"
        u1 = downgrade_2(u2)
        assert u1["data"]["value"] == "500"
        u0 = downgrade_1(u1)
        assert u0["value"] == "500"

    def test_schema_version(self):
        assert mod3.SCHEMA_VERSION == 3

    def test_downgrade_missing_data_field(self):
        with pytest.raises(MigrationError):
            downgrade_3({"version": 3})

    def test_upgrade_extra_fields_preserved(self):
        payload = {"version": 2, "data": {"value": "100", "extra": "data"}}
        result = upgrade_3(payload)
        assert result["data"]["amount"] == "100"
        assert result["data"]["extra"] == "data"

    def test_downgrade_with_extra_fields(self):
        payload = {"version": 3, "data": {"amount": "100", "extra": "data"}}
        result = downgrade_3(payload)
        assert result["data"]["value"] == "100"
        assert result["data"]["extra"] == "data"

    def test_upgrade_missing_both_value_and_amount(self):
        with pytest.raises(MigrationError):
            upgrade_3({"version": 2, "data": {"label": "test"}})


@given(st.text())
def test_migration_roundtrip(value):
    v1 = upgrade_1({"value": value})
    v2 = upgrade_2(v1)
    v3 = upgrade_3(v2)
    assert v3["data"]["amount"] == value
    u2 = downgrade_3(v3)
    assert u2["data"]["value"] == value
    u1 = downgrade_2(u2)
    assert u1["data"]["value"] == value
    u0 = downgrade_1(u1)
    assert u0["value"] == value


@given(st.text(), st.text())
def test_migration_roundtrip_with_label(value, label):
    v1 = upgrade_1({"value": value, "label": label})
    v2 = upgrade_2(v1)
    v3 = upgrade_3(v2)
    assert v3["data"]["amount"] == value
    assert v3["data"]["label"] == label
    u2 = downgrade_3(v3)
    assert u2["data"]["value"] == value
    assert u2["data"]["label"] == label
    u1 = downgrade_2(u2)
    u0 = downgrade_1(u1)
    assert u0["value"] == value
    assert u0["label"] == label


@given(st.text(min_size=1))
def test_migration_roundtrip_with_curve(value):
    v1 = upgrade_1({"value": value})
    v2 = upgrade_2(v1)
    v2["data"]["yield_curve"] = {"1y": "0.05"}
    v3 = upgrade_3(v2)
    assert v3["data"]["amount"] == value
    assert v3["data"]["yield_curve"] == {"1y": "0.05"}
