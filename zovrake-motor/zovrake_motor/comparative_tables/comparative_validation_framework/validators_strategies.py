"""Validadores especializados del Comparative Validation Framework."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_validation_framework.checks import (
    build_check_set,
    build_global_consistency_findings,
    validate_model_completeness,
    validate_model_consistency,
    validate_model_integrity,
    validate_model_structure,
    validate_model_traceability,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ValidationValidatorStrategyType,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.gateway import (
    ModelValidationInputView,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeValidationCheckSet,
    ComparativeValidationFinding,
    ValidationValidatorResult,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.port import (
    ValidationValidatorPort,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


class DefinitiveComparativeModelValidator(ValidationValidatorPort):
    """
    Valida integridad, consistencia, completitud y trazabilidad
    de cada Modelo Comparativo Definitivo.
    """

    @property
    def validator_name(self) -> str:
        return "definitive_comparative_model_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Modelo Comparativo Definitivo"

    @property
    def validator_type(self) -> ValidationValidatorStrategyType:
        return ValidationValidatorStrategyType.DEFINITIVE_MODEL

    def validate(
        self,
        input_view: ModelValidationInputView,
        *,
        settings: ComparativeValidationFrameworkSettings,
        start_sequence: int,
    ) -> ValidationValidatorResult:
        check_sets: list[ComparativeValidationCheckSet] = []
        sequence = start_sequence

        for model in input_view.definitive_catalog.models:
            findings: list[ComparativeValidationFinding] = []

            for validate_fn in (
                validate_model_structure,
                validate_model_completeness,
                validate_model_integrity,
                validate_model_consistency,
                validate_model_traceability,
            ):
                step_findings, sequence = validate_fn(
                    model=model,
                    validator_name=self.validator_name,
                    sequence=sequence,
                    settings=settings,
                )
                findings.extend(step_findings)

            check_sets.append(
                build_check_set(model=model, findings=tuple(findings)),
            )

        global_findings_list, sequence = build_global_consistency_findings(
            catalog=input_view.definitive_catalog,
            validator_name=self.validator_name,
            sequence=sequence,
            settings=settings,
        )

        total_findings = sum(len(cs.findings) for cs in check_sets) + len(global_findings_list)
        return ValidationValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            check_sets=tuple(check_sets),
            global_findings=tuple(global_findings_list),
            technical_observations=(
                f"validator_type={self.validator_type.value}",
                f"models_validated={len(input_view.definitive_catalog.models)}",
                f"findings_detected={total_findings}",
            ),
        )
