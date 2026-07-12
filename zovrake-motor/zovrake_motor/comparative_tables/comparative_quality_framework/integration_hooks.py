"""Punto de integración para certificación del módulo PM6 (4.11 completada)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityReport,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)


class ModuleCertificationIntegrationPoint:
    """Expone el estado de certificación del módulo PM6."""

    def __init__(self, *, settings: ComparativeQualityFrameworkSettings) -> None:
        self._settings = settings

    def prepare_for_future_certification(
        self,
        report: ComparativeQualityReport,
    ) -> dict[str, Any]:
        return {
            "prepared": self._settings.module_certification_prepared,
            "checks_executed": report.checks_executed,
            "checks_passed": report.checks_passed,
            "checks_failed": report.checks_failed,
            "status": (
                "certified"
                if self._settings.module_certification_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "module_certification_prepared": self._settings.module_certification_prepared,
            "integration_status": (
                "certified"
                if self._settings.module_certification_prepared
                else "not_prepared"
            ),
        }
