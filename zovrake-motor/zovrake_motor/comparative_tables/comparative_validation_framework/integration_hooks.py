"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeValidationReport,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


class ComparativeQualityFrameworkIntegrationPoint:
    """Preparación hacia el Comparative Quality Framework — sin ejecución."""

    def __init__(self, *, settings: ComparativeValidationFrameworkSettings) -> None:
        self._settings = settings

    def prepare_for_future_quality_audit(
        self,
        report: ComparativeValidationReport,
    ) -> dict[str, Any]:
        total_findings = sum(len(cs.findings) for cs in report.check_sets) + len(
            report.global_findings,
        )
        return {
            "prepared": self._settings.comparative_quality_framework_prepared,
            "check_sets_count": len(report.check_sets),
            "findings_count": total_findings,
            "status": (
                "prepared"
                if self._settings.comparative_quality_framework_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "comparative_quality_framework_prepared": (
                self._settings.comparative_quality_framework_prepared
            ),
            "status": (
                "prepared"
                if self._settings.comparative_quality_framework_prepared
                else "not_prepared"
            ),
        }
