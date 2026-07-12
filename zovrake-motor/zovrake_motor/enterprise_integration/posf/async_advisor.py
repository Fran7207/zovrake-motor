"""Asesor de procesamiento asíncrono — trabaja con APQM sin modificar su lógica."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.posf.enums import OptimizationStrategy
from zovrake_motor.enterprise_integration.posf.models import OptimizationHint


class AsyncProcessingAdvisor:
    """
    Optimiza asignación y congestión de cola de forma consultiva.

    No modifica la lógica del APQM.
    """

    def __init__(self, *, congestion_threshold: int = 100) -> None:
        self._congestion_threshold = congestion_threshold
        self._hints: list[OptimizationHint] = []

    def evaluate_queue(
        self,
        *,
        process_id: UUID | None,
        queue_depth: int,
        pending_count: int,
        active_count: int,
        max_workers: int,
    ) -> OptimizationHint | None:
        hint: OptimizationHint | None = None

        if queue_depth >= self._congestion_threshold:
            hint = OptimizationHint.create(
                process_id=process_id,
                strategy=OptimizationStrategy.ASYNC_QUEUE,
                component="AsyncProcessingQueueManager",
                message="Congestión de cola detectada — evaluar escalado vertical u horizontal",
                metadata={
                    "queue_depth": queue_depth,
                    "pending_count": pending_count,
                    "active_count": active_count,
                },
            )
            self._hints.append(hint)

        if active_count >= max_workers and pending_count > 0:
            hint = OptimizationHint.create(
                process_id=process_id,
                strategy=OptimizationStrategy.ASYNC_QUEUE,
                component="AsyncProcessingQueueManager",
                message="Workers al máximo — minimizar bloqueos mediante escalado",
                metadata={
                    "active_count": active_count,
                    "max_workers": max_workers,
                    "pending_count": pending_count,
                },
            )
            self._hints.append(hint)

        return hint

    def snapshot(self) -> dict[str, Any]:
        return {
            "congestion_threshold": self._congestion_threshold,
            "hints_total": len(self._hints),
            "recent_hints": [h.to_dict() for h in self._hints[-10:]],
        }
