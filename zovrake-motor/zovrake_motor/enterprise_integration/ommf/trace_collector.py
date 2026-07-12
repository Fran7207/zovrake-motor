"""Recopilador de trazas — continuidad por proceso."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ommf.models import IntegrationTraceSpan


class TraceCollector:
    """
    Almacena trazas del flujo de integración preservando continuidad.

    Cada process_id mantiene un trace_id único compartido por todos sus spans.
    """

    def __init__(self) -> None:
        self._spans: list[IntegrationTraceSpan] = []
        self._trace_ids: dict[str, str] = {}

    def _trace_id_for(self, process_id: UUID) -> str:
        key = str(process_id)
        if key not in self._trace_ids:
            self._trace_ids[key] = key
        return self._trace_ids[key]

    def record(
        self,
        *,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        component: str,
        pipeline_phase: str,
        operation: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> IntegrationTraceSpan:
        span = IntegrationTraceSpan.create(
            trace_id=self._trace_id_for(process_id),
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase=pipeline_phase,
            operation=operation,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        self._spans.append(span)
        return span

    def by_process(self, process_id: UUID) -> tuple[IntegrationTraceSpan, ...]:
        return tuple(span for span in self._spans if span.process_id == process_id)

    def count(self) -> int:
        return len(self._spans)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_spans": self.count(),
            "active_traces": len(self._trace_ids),
            "recent_spans": [span.to_dict() for span in self._spans[-20:]],
        }
