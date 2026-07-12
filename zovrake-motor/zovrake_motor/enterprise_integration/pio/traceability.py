"""Trazabilidad del Pipeline de Integración — memoria, sin persistencia."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.pio.models import PipelineExecutionContext


class PipelineTraceabilityStore:
    """Almacén en memoria de contextos de ejecución del Pipeline."""

    def __init__(self) -> None:
        self._contexts: dict[UUID, PipelineExecutionContext] = {}

    def save(self, context: PipelineExecutionContext) -> None:
        self._contexts[context.process_id] = context

    def get(self, process_id: UUID) -> PipelineExecutionContext | None:
        return self._contexts.get(process_id)

    def require(self, process_id: UUID) -> PipelineExecutionContext:
        context = self.get(process_id)
        if context is None:
            raise KeyError(f"Contexto de Pipeline no encontrado: {process_id}")
        return context

    def count(self) -> int:
        return len(self._contexts)

    def snapshot(self) -> list[dict]:
        return [context.to_dict() for context in self._contexts.values()]
