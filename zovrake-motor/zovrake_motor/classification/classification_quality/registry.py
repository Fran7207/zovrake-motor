"""Registro centralizado de validadores del CQF."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.classification_quality.exceptions import QualityValidatorNotFoundError
from zovrake_motor.classification.classification_quality.port import QualityValidatorPort
from zovrake_motor.classification.classification_quality.validators import (
    DataIntegrityValidator,
    IdentifierUniquenessValidator,
    ModelConsistencyValidator,
    PipelineFlowValidator,
    TraceabilityChainValidator,
)
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings


class QualityValidatorRegistry:
    """Registro único de validadores de calidad."""

    def __init__(self) -> None:
        self._validators_by_name: dict[str, QualityValidatorPort] = {}
        self._validators_ordered: list[QualityValidatorPort] = []

    def register(self, validator: QualityValidatorPort) -> None:
        if validator.validator_name in self._validators_by_name:
            raise ValueError(f"Validador ya registrado: {validator.validator_name}")
        self._validators_by_name[validator.validator_name] = validator
        self._validators_ordered.append(validator)

    def register_defaults(self, *, settings: ClassificationQualityFrameworkSettings | None = None) -> None:
        settings = settings or ClassificationQualityFrameworkSettings.default()
        candidates: list[tuple[bool, QualityValidatorPort]] = [
            (settings.model_consistency_validator_enabled, ModelConsistencyValidator()),
            (settings.data_integrity_validator_enabled, DataIntegrityValidator()),
            (settings.identifier_uniqueness_validator_enabled, IdentifierUniquenessValidator()),
            (settings.traceability_chain_validator_enabled, TraceabilityChainValidator()),
            (settings.pipeline_flow_validator_enabled, PipelineFlowValidator()),
        ]
        for enabled, validator in candidates:
            if enabled:
                self.register(validator)

    def get(self, name: str) -> QualityValidatorPort | None:
        return self._validators_by_name.get(name)

    def require(self, name: str) -> QualityValidatorPort:
        validator = self.get(name)
        if validator is None:
            raise QualityValidatorNotFoundError(f"Validador no registrado: {name}")
        return validator

    def all_validators(self) -> tuple[QualityValidatorPort, ...]:
        return tuple(self._validators_ordered)

    def count(self) -> int:
        return len(self._validators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [validator.snapshot() for validator in self._validators_ordered]
