"""Utilidades de construcción del informe de auditoría de calidad."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityValidationStatus,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.gateway import (
    ComparativeQualityInputView,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityCheck,
    ComparativeQualityFinding,
    ComparativeQualityReport,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)


def build_report_id(model_id: str) -> str:
    return f"pm6-cqf-report://{model_id}"


def resolve_overall_status(
    *,
    checks_failed: int,
    findings: tuple[ComparativeQualityFinding, ...],
    settings: ComparativeQualityFrameworkSettings,
) -> ComparativeQualityValidationStatus:
    if checks_failed == 0 and not findings:
        return ComparativeQualityValidationStatus.PASSED

    has_errors = any(finding.severity == "error" for finding in findings)
    if has_errors and settings.fail_on_error_findings:
        return ComparativeQualityValidationStatus.FAILED

    has_warnings = any(finding.severity == "warning" for finding in findings)
    if checks_failed > 0 or has_warnings or has_errors:
        return ComparativeQualityValidationStatus.PASSED_WITH_WARNINGS

    return ComparativeQualityValidationStatus.PASSED


def build_comparative_quality_report(
    *,
    input_view: ComparativeQualityInputView,
    checks: tuple[ComparativeQualityCheck, ...],
    findings: tuple[ComparativeQualityFinding, ...],
    settings: ComparativeQualityFrameworkSettings,
) -> ComparativeQualityReport:
    checks_passed = sum(1 for check in checks if check.passed)
    checks_failed = sum(1 for check in checks if not check.passed)
    overall_status = resolve_overall_status(
        checks_failed=checks_failed,
        findings=findings,
        settings=settings,
    )

    return ComparativeQualityReport(
        report_id=build_report_id(input_view.model_id),
        process_id=input_view.process_id,
        catalog_id=input_view.catalog_id,
        document_id=input_view.document_id,
        model_id=input_view.model_id,
        validation_report_id=input_view.validation_report_id,
        findings=findings,
        checks=checks,
        checks_executed=len(checks),
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        overall_status=overall_status,
        module_certification_prepared=settings.module_certification_prepared,
        definitive_catalog_preserved=True,
        validation_report_preserved=True,
        domain_model_preserved=input_view.domain_model_preserved,
    )
