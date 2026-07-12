"""Almacén en memoria de informes de auditoría de calidad."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityReport,
)


class ComparativeQualityReportStore:
    """Almacén temporal de informes — sin persistencia."""

    def __init__(self) -> None:
        self._reports_by_id: dict[str, ComparativeQualityReport] = {}
        self._report_ids_by_process: dict[UUID, list[str]] = {}

    def save(self, report: ComparativeQualityReport) -> None:
        self._reports_by_id[report.report_id] = report
        process_ids = self._report_ids_by_process.setdefault(report.process_id, [])
        if report.report_id not in process_ids:
            process_ids.append(report.report_id)

    def get(self, report_id: str) -> ComparativeQualityReport | None:
        return self._reports_by_id.get(report_id)

    def get_by_process(self, process_id: UUID) -> tuple[ComparativeQualityReport, ...]:
        report_ids = self._report_ids_by_process.get(process_id, [])
        return tuple(
            report
            for report_id in report_ids
            if (report := self._reports_by_id.get(report_id)) is not None
        )

    def count(self) -> int:
        return len(self._reports_by_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "report_entries_count": self.count(),
            "processes_with_reports": len(self._report_ids_by_process),
        }
