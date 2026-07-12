"""Puntos de integración preparatorios hacia componentes posteriores del PM6."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.group_integrity_engine.models import GroupIntegrityReport
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


class TraceabilityMetadataEngineIntegrationPoint:
    """Preparación hacia el Traceability & Metadata Engine — sin ejecución."""

    def __init__(self, *, settings: GroupIntegrityEngineSettings) -> None:
        self._settings = settings

    def prepare_for_future_enrichment(
        self,
        report: GroupIntegrityReport,
    ) -> dict[str, Any]:
        total_findings = sum(len(cs.findings) for cs in report.check_sets) + len(
            report.global_findings,
        )
        return {
            "prepared": self._settings.traceability_metadata_engine_prepared,
            "check_sets_count": len(report.check_sets),
            "findings_count": total_findings,
            "status": (
                "prepared"
                if self._settings.traceability_metadata_engine_prepared
                else "not_prepared"
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "traceability_metadata_engine_prepared": (
                self._settings.traceability_metadata_engine_prepared
            ),
            "status": (
                "prepared"
                if self._settings.traceability_metadata_engine_prepared
                else "not_prepared"
            ),
        }
