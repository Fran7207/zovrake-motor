"""Registro centralizado de validadores del GIE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.group_integrity_engine.exceptions import (
    IntegrityValidatorNotFoundError,
)
from zovrake_motor.comparative_tables.group_integrity_engine.port import IntegrityValidatorPort
from zovrake_motor.comparative_tables.group_integrity_engine.validators_strategies import (
    ComparativeTableIntegrityValidator,
)
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


class IntegrityValidatorRegistry:
    """Registro único de validadores de integridad estructural."""

    def __init__(self) -> None:
        self._validators_by_name: dict[str, IntegrityValidatorPort] = {}
        self._validators_ordered: list[IntegrityValidatorPort] = []

    def register(self, validator: IntegrityValidatorPort) -> None:
        if validator.validator_name in self._validators_by_name:
            raise ValueError(f"Validador ya registrado: {validator.validator_name}")
        self._validators_by_name[validator.validator_name] = validator
        self._validators_ordered.append(validator)

    def register_defaults(
        self,
        *,
        settings: GroupIntegrityEngineSettings | None = None,
    ) -> None:
        settings = settings or GroupIntegrityEngineSettings.default()
        candidates: list[tuple[bool, IntegrityValidatorPort]] = [
            (settings.comparative_table_integrity_validator_enabled, ComparativeTableIntegrityValidator()),
        ]
        for enabled, validator in candidates:
            if enabled:
                self.register(validator)

    def get(self, name: str) -> IntegrityValidatorPort | None:
        return self._validators_by_name.get(name)

    def require(self, name: str) -> IntegrityValidatorPort:
        validator = self.get(name)
        if validator is None:
            raise IntegrityValidatorNotFoundError(f"Validador no registrado: {name}")
        return validator

    def all_validators(self) -> tuple[IntegrityValidatorPort, ...]:
        return tuple(self._validators_ordered)

    def count(self) -> int:
        return len(self._validators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [validator.snapshot() for validator in self._validators_ordered]
