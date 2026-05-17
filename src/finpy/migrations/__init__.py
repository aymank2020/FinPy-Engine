"""Migration registry and orchestration utilities.

The migration framework treats every numbered module under
``finpy.migrations`` as an ordered pair ``(upgrade, downgrade)`` keyed by its
schema version. ``run_migrations`` walks the registry in either direction and
applies the appropriate transformation to the payload.
"""

from __future__ import annotations

import importlib
from typing import Any, Callable

# (upgrade, downgrade) callable pairs keyed by target schema version.
_migration_registry: dict[int, tuple[Callable[[dict], dict], Callable[[dict], dict]]] = {}


def _register(version: int, module_name: str) -> None:
    module = importlib.import_module(f"finpy.migrations.{module_name}")
    _migration_registry[version] = (module.upgrade, module.downgrade)


_register(1, "0001_initial")
_register(2, "0002_add_curve")
_register(3, "0003_rename_field")
_register(4, "0004_add_types")


def get_latest_version() -> int:
    """Return the highest registered schema version."""
    return max(_migration_registry)


def run_migrations(payload: Any, current: int, target: int) -> Any:
    """Walk the registry between ``current`` and ``target`` schema versions.

    When ``current == target`` the payload is returned unchanged. When the
    direction is forward, each upgrade callable is applied in ascending order;
    when the direction is backward, each downgrade callable is applied in
    descending order.
    """

    if current == target:
        return payload

    if current < target:
        for version in range(current + 1, target + 1):
            if version not in _migration_registry:
                raise ValueError(f"No migration for version {version}")
            upgrade, _ = _migration_registry[version]
            payload = upgrade(payload)
        return payload

    for version in range(current, target, -1):
        if version not in _migration_registry:
            raise ValueError(f"No migration for version {version}")
        _, downgrade = _migration_registry[version]
        payload = downgrade(payload)
    return payload


def migrate_to_latest(payload: Any) -> Any:
    """Upgrade ``payload`` from its declared version to the latest schema."""
    latest = get_latest_version()
    if isinstance(payload, dict):
        current = payload.get("version", 0)
    else:
        current = 0

    if current > latest:
        raise ValueError(f"No migration for version {current}")

    if current == latest:
        return payload

    return run_migrations(payload, current, latest)


__all__ = [
    "_migration_registry",
    "get_latest_version",
    "run_migrations",
    "migrate_to_latest",
]
