"""Puertos del POSF — integración con PIO, APQM y OMMF."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class IntegrationPerformancePort(Protocol):
    """
    Contrato transversal de optimización de rendimiento.

    Implementado exclusivamente por el POSF.
    """

    def record_pipeline_transition(
        self,
        *,
        process_id: UUID,
        phase: str,
        operation: str,
        transition_count: int,
        project_id: str = "",
        quotation_id: str = "",
    ) -> None:
        """Registra transición del Pipeline para análisis."""

    def record_queue_metrics(
        self,
        *,
        process_id: UUID | None,
        queue_depth: int,
        pending_count: int,
        active_count: int,
        max_workers: int,
    ) -> None:
        """Registra métricas de cola para optimización asíncrona."""

    def record_resource_allocation(
        self,
        *,
        process_id: UUID | None,
        component: str,
        memory_units: int = 0,
        cpu_units: int = 0,
        storage_units: int = 0,
    ) -> None:
        """Registra asignación lógica de recursos."""


class PerformanceMetricsSourcePort(Protocol):
    """Puerto de lectura de métricas desde el OMMF."""

    def observability_snapshot(self) -> dict[str, Any]:
        """Snapshot de métricas operativas del OMMF."""

    def traces_for_process(self, process_id: UUID) -> tuple[dict[str, Any], ...]:
        """Trazas del proceso para evaluación de rendimiento."""
