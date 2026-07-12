"""Ejecutor de validadores del Classification Quality Framework."""

from __future__ import annotations

from zovrake_motor.classification.classification_quality.builders import build_classification_quality_report
from zovrake_motor.classification.classification_quality.enums import QualityValidationStatus
from zovrake_motor.classification.classification_quality.gateway import ComparativeDomainModelCatalogView
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationResult,
    QualityValidationCheck,
    QualityValidationFinding,
)
from zovrake_motor.classification.classification_quality.registry import QualityValidatorRegistry
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings


class ClassificationQualityExecutor:
    """Coordina validadores sin modificar datos evaluados."""

    def __init__(self, registry: QualityValidatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> ClassificationQualityValidationResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []
        observations: list[str] = []

        for validator in self._registry.all_validators():
            result = validator.validate(catalog_view, settings=settings)
            checks.extend(result.checks)
            findings.extend(result.findings)
            observations.extend(result.technical_observations)

        report = build_classification_quality_report(
            catalog_view=catalog_view,
            checks=tuple(checks),
            findings=tuple(findings),
            settings=settings,
        )

        status = report.overall_status
        if not catalog_view.models and settings.allow_empty_catalog_validation:
            status = QualityValidationStatus.SKIPPED

        observations.extend(
            (
                "source_data_preserved=True",
                "original_documents_unaccessed=True",
                f"checks_executed={report.checks_executed}",
                f"checks_passed={report.checks_passed}",
                f"checks_failed={report.checks_failed}",
                f"overall_status={status.value}",
            ),
        )

        return ClassificationQualityValidationResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            report=report,
            status=status,
            source_data_preserved=True,
            validators_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
