"""Registro centralizado de validadores del CVF."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_validation_framework.exceptions import (
    ValidationValidatorNotFoundError,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.port import (
    ValidationValidatorPort,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.validators_strategies import (
    DefinitiveComparativeModelValidator,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


class ValidationValidatorRegistry:
    """Registro único de validadores del Modelo Comparativo Definitivo."""

    def __init__(self) -> None:
        self._validators_by_name: dict[str, ValidationValidatorPort] = {}
        self._validators_ordered: list[ValidationValidatorPort] = []

    def register(self, validator: ValidationValidatorPort) -> None:
        if validator.validator_name in self._validators_by_name:
            raise ValueError(f"Validador ya registrado: {validator.validator_name}")
        self._validators_by_name[validator.validator_name] = validator
        self._validators_ordered.append(validator)

    def register_defaults(
        self,
        *,
        settings: ComparativeValidationFrameworkSettings | None = None,
    ) -> None:
        settings = settings or ComparativeValidationFrameworkSettings.default()
        candidates: list[tuple[bool, ValidationValidatorPort]] = [
            (
                settings.definitive_comparative_model_validator_enabled,
                DefinitiveComparativeModelValidator(),
            ),
        ]
        for enabled, validator in candidates:
            if enabled:
                self.register(validator)

    def get(self, name: str) -> ValidationValidatorPort | None:
        return self._validators_by_name.get(name)

    def require(self, name: str) -> ValidationValidatorPort:
        validator = self.get(name)
        if validator is None:
            raise ValidationValidatorNotFoundError(f"Validador no registrado: {name}")
        return validator

    def all_validators(self) -> tuple[ValidationValidatorPort, ...]:
        return tuple(self._validators_ordered)

    def count(self) -> int:
        return len(self._validators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [validator.snapshot() for validator in self._validators_ordered]
