"""Almacén en memoria de reportes de validación del CVF."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeValidationReport,
)


class ComparativeValidationReportStore:
    """Persistencia en memoria — sin almacenamiento persistente."""

    def __init__(self) -> None:
        self._reports: list[ComparativeValidationReport] = []

    def save(self, report: ComparativeValidationReport) -> None:
        self._reports.append(report)

    def all_reports(self) -> tuple[ComparativeValidationReport, ...]:
        return tuple(self._reports)

    def count(self) -> int:
        return len(self._reports)

    def snapshot(self) -> dict[str, int]:
        return {"report_entries_count": self.count()}
