"""Registro de reutilización segura — nunca datos de procesos distintos."""

from __future__ import annotations

from typing import Any


class SafeReuseRegistry:
    """
    Reutiliza configuraciones, contratos y objetos de infraestructura inmutables.

    Prohibido almacenar datos pertenecientes a procesos distintos.
    """

    def __init__(self) -> None:
        self._infrastructure: dict[str, Any] = {}
        self._contracts: dict[str, Any] = {}
        self._configurations: dict[str, Any] = {}

    def register_infrastructure(self, key: str, value: Any) -> None:
        if not key.startswith("infra:"):
            key = f"infra:{key}"
        self._infrastructure[key] = value

    def register_contract(self, key: str, value: Any) -> None:
        if not key.startswith("contract:"):
            key = f"contract:{key}"
        self._contracts[key] = value

    def register_configuration(self, key: str, value: Any) -> None:
        if not key.startswith("config:"):
            key = f"config:{key}"
        self._configurations[key] = value

    def get_infrastructure(self, key: str) -> Any | None:
        return self._infrastructure.get(f"infra:{key}" if not key.startswith("infra:") else key)

    def get_contract(self, key: str) -> Any | None:
        return self._contracts.get(f"contract:{key}" if not key.startswith("contract:") else key)

    def get_configuration(self, key: str) -> Any | None:
        return self._configurations.get(f"config:{key}" if not key.startswith("config:") else key)

    def snapshot(self) -> dict[str, Any]:
        return {
            "infrastructure_entries": len(self._infrastructure),
            "contract_entries": len(self._contracts),
            "configuration_entries": len(self._configurations),
        }
