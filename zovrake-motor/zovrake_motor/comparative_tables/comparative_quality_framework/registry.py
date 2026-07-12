"""Registro centralizado de auditores del CQF."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_quality_framework.exceptions import (
    ComparativeQualityValidatorNotFoundError,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.port import (
    ComparativeQualityValidatorPort,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.validators import (
    ArchitecturalComplianceValidator,
    DefinitiveModelConsistencyValidator,
    IdentifierUniquenessValidator,
    PipelineFlowValidator,
    TraceabilityChainValidator,
    ValidationReportIntegrityValidator,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)


class ComparativeQualityValidatorRegistry:
    """Registro único de auditores de calidad del PM6."""

    def __init__(self) -> None:
        self._validators_by_name: dict[str, ComparativeQualityValidatorPort] = {}
        self._validators_ordered: list[ComparativeQualityValidatorPort] = []

    def register(self, validator: ComparativeQualityValidatorPort) -> None:
        if validator.validator_name in self._validators_by_name:
            raise ValueError(f"Auditor ya registrado: {validator.validator_name}")
        self._validators_by_name[validator.validator_name] = validator
        self._validators_ordered.append(validator)

    def register_defaults(
        self,
        *,
        settings: ComparativeQualityFrameworkSettings | None = None,
    ) -> None:
        settings = settings or ComparativeQualityFrameworkSettings.default()
        candidates: list[tuple[bool, ComparativeQualityValidatorPort]] = [
            (
                settings.architectural_compliance_validator_enabled,
                ArchitecturalComplianceValidator(),
            ),
            (
                settings.definitive_model_consistency_validator_enabled,
                DefinitiveModelConsistencyValidator(),
            ),
            (
                settings.validation_report_integrity_validator_enabled,
                ValidationReportIntegrityValidator(),
            ),
            (
                settings.identifier_uniqueness_validator_enabled,
                IdentifierUniquenessValidator(),
            ),
            (
                settings.traceability_chain_validator_enabled,
                TraceabilityChainValidator(),
            ),
            (
                settings.pipeline_flow_validator_enabled,
                PipelineFlowValidator(),
            ),
        ]
        for enabled, validator in candidates:
            if enabled:
                self.register(validator)

    def get(self, name: str) -> ComparativeQualityValidatorPort | None:
        return self._validators_by_name.get(name)

    def require(self, name: str) -> ComparativeQualityValidatorPort:
        validator = self.get(name)
        if validator is None:
            raise ComparativeQualityValidatorNotFoundError(
                f"Auditor no registrado: {name}",
            )
        return validator

    def all_validators(self) -> tuple[ComparativeQualityValidatorPort, ...]:
        return tuple(self._validators_ordered)

    def count(self) -> int:
        return len(self._validators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [validator.snapshot() for validator in self._validators_ordered]
