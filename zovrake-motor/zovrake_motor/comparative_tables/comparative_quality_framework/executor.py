"""Ejecutor de auditores del Comparative Quality Framework."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_quality_framework.builders import (
    build_comparative_quality_report,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityValidationStatus,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.gateway import (
    ComparativeQualityInputView,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityCheck,
    ComparativeQualityFinding,
    ComparativeQualityValidationResult,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.registry import (
    ComparativeQualityValidatorRegistry,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)


class ComparativeQualityExecutor:
    """Coordina auditores sin modificar datos evaluados."""

    def __init__(self, registry: ComparativeQualityValidatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidationResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []
        observations: list[str] = []

        for validator in self._registry.all_validators():
            result = validator.validate(input_view, settings=settings)
            checks.extend(result.checks)
            findings.extend(result.findings)
            observations.extend(result.technical_observations)

        report = build_comparative_quality_report(
            input_view=input_view,
            checks=tuple(checks),
            findings=tuple(findings),
            settings=settings,
        )

        status = report.overall_status
        if not input_view.models and settings.allow_empty_catalog_validation:
            status = ComparativeQualityValidationStatus.SKIPPED

        observations.extend(
            (
                "definitive_catalog_preserved=True",
                "validation_report_preserved=True",
                "source_files_unaccessed=True",
                f"checks_executed={report.checks_executed}",
                f"checks_passed={report.checks_passed}",
                f"checks_failed={report.checks_failed}",
                f"overall_status={status.value}",
            ),
        )

        return ComparativeQualityValidationResult(
            process_id=input_view.process_id,
            document_id=input_view.document_id,
            model_id=input_view.model_id,
            report=report,
            status=status,
            definitive_catalog_preserved=True,
            validation_report_preserved=True,
            domain_model_preserved=input_view.domain_model_preserved,
            validators_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
