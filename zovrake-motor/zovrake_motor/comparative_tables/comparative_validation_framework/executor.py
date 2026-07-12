"""Ejecutor de validadores del Comparative Validation Framework."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_validation_framework.checks import (
    build_validation_report,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ComparativeModelValidationStatus,
    ValidationFindingSeverity,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.gateway import (
    ModelValidationInputView,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationResult,
    ComparativeValidationCheckSet,
    ComparativeValidationFinding,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.registry import (
    ValidationValidatorRegistry,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


class ComparativeModelValidationExecutor:
    """Coordina validadores sin modificar catálogos de entrada."""

    def __init__(self, registry: ValidationValidatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ModelValidationInputView,
        *,
        settings: ComparativeValidationFrameworkSettings,
    ) -> ComparativeModelValidationResult:
        check_sets: list[ComparativeValidationCheckSet] = []
        global_findings: list[ComparativeValidationFinding] = []
        observations: list[str] = []
        sequence = 1

        for validator in self._registry.all_validators():
            result = validator.validate(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            check_sets.extend(result.check_sets)
            global_findings.extend(result.global_findings)
            observations.extend(result.technical_observations)
            sequence += sum(len(cs.findings) for cs in result.check_sets) + len(
                result.global_findings,
            )

        all_findings = [
            finding
            for check_set in check_sets
            for finding in check_set.findings
        ] + list(global_findings)

        error_count = sum(
            1 for f in all_findings if f.severity == ValidationFindingSeverity.ERROR
        )
        warning_count = sum(
            1 for f in all_findings if f.severity == ValidationFindingSeverity.WARNING
        )

        if error_count >= settings.max_errors_before_invalid:
            status = ComparativeModelValidationStatus.INVALID
        elif warning_count > 0:
            status = ComparativeModelValidationStatus.PARTIAL
        elif check_sets:
            status = ComparativeModelValidationStatus.VALID
        else:
            status = ComparativeModelValidationStatus.SKIPPED

        report = build_validation_report(
            input_view=input_view,
            check_sets=tuple(check_sets),
            global_findings=tuple(global_findings),
            comparative_quality_framework_prepared=(
                settings.comparative_quality_framework_prepared
            ),
        )

        observations.extend(
            (
                "definitive_catalog_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "findings_count=" + str(len(all_findings)),
                "error_count=" + str(error_count),
                "warning_count=" + str(warning_count),
            ),
        )

        return ComparativeModelValidationResult(
            process_id=input_view.definitive_catalog.process_id,
            document_id=input_view.definitive_catalog.document_id,
            model_id=input_view.definitive_catalog.model_id,
            report=report,
            status=status,
            findings_count=len(all_findings),
            error_count=error_count,
            warning_count=warning_count,
            definitive_catalog_preserved=True,
            domain_model_preserved=input_view.definitive_catalog.domain_model_preserved,
            validators_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
