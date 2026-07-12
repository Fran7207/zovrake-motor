"""Utilidades de construcción del informe de validación."""

from __future__ import annotations

from zovrake_motor.classification.classification_quality.enums import QualityValidationStatus
from zovrake_motor.classification.classification_quality.gateway import ComparativeDomainModelCatalogView
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityReport,
    QualityValidationCheck,
    QualityValidationFinding,
)
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings


def build_report_id(model_id: str) -> str:
    return f"cqf-report://{model_id}"


def resolve_overall_status(
    *,
    checks_failed: int,
    findings: tuple[QualityValidationFinding, ...],
    settings: ClassificationQualityFrameworkSettings,
) -> QualityValidationStatus:
    if checks_failed == 0 and not findings:
        return QualityValidationStatus.PASSED

    has_errors = any(finding.severity == "error" for finding in findings)
    if has_errors and settings.fail_on_error_findings:
        return QualityValidationStatus.FAILED

    has_warnings = any(finding.severity == "warning" for finding in findings)
    if checks_failed > 0 or has_warnings or has_errors:
        return QualityValidationStatus.PASSED_WITH_WARNINGS

    return QualityValidationStatus.PASSED


def build_classification_quality_report(
    *,
    catalog_view: ComparativeDomainModelCatalogView,
    checks: tuple[QualityValidationCheck, ...],
    findings: tuple[QualityValidationFinding, ...],
    settings: ClassificationQualityFrameworkSettings,
) -> ClassificationQualityReport:
    checks_passed = sum(1 for check in checks if check.passed)
    checks_failed = sum(1 for check in checks if not check.passed)
    overall_status = resolve_overall_status(
        checks_failed=checks_failed,
        findings=findings,
        settings=settings,
    )

    return ClassificationQualityReport(
        report_id=build_report_id(catalog_view.model_id),
        process_id=catalog_view.process_id,
        catalog_id=catalog_view.catalog_id,
        document_id=catalog_view.document_id,
        model_id=catalog_view.model_id,
        findings=findings,
        checks=checks,
        checks_executed=len(checks),
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        overall_status=overall_status,
        certification_prepared=settings.certification_prepared,
        source_data_preserved=True,
    )
