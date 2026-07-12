"""Puertos del OMMF — integración transversal con PIO, APQM, FTRRF y SVAF."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class IntegrationObservabilityPort(Protocol):
    """
    Contrato transversal de observabilidad.

    Implementado exclusivamente por el OMMF.
    """

    def record_request_received(
        self,
        *,
        process_id: UUID,
        project_id: str = "",
        quotation_id: str = "",
        component: str,
    ) -> None:
        """Registra solicitud recibida."""

    def record_request_processed(
        self,
        *,
        process_id: UUID,
        component: str,
        success: bool,
        duration_ms: float = 0.0,
        project_id: str = "",
        quotation_id: str = "",
    ) -> None:
        """Registra solicitud procesada."""

    def record_pipeline_transition(
        self,
        *,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        component: str,
        pipeline_phase: str,
        operation: str,
        duration_ms: float,
    ) -> None:
        """Registra transición del Pipeline."""

    def record_queue_event(
        self,
        *,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        event: str,
        queue_item_id: str = "",
        duration_ms: float = 0.0,
    ) -> None:
        """Registra evento de cola APQM."""

    def record_fault_event(
        self,
        *,
        process_id: UUID,
        event: str,
        category: str = "",
        attempt: int = 1,
        duration_ms: float = 0.0,
    ) -> None:
        """Registra error, reintento o recuperación FTRRF."""

    def record_validation_event(
        self,
        *,
        process_id: UUID,
        event: str,
        approved: bool,
        duration_ms: float = 0.0,
        operation: str = "",
    ) -> None:
        """Registra validación o auditoría SVAF."""

    def record_process_cancelled(self, *, process_id: UUID) -> None:
        """Registra proceso cancelado."""


class ObservabilitySourcePort(Protocol):
    """Puerto de lectura para consolidar snapshots de componentes hermanos."""

    def pipeline_snapshot(self) -> dict[str, Any] | None:
        """Snapshot del PIO."""

    def queue_snapshot(self) -> dict[str, Any] | None:
        """Snapshot del APQM."""

    def fault_snapshot(self) -> dict[str, Any] | None:
        """Snapshot del FTRRF."""

    def security_snapshot(self) -> dict[str, Any] | None:
        """Snapshot del SVAF."""
