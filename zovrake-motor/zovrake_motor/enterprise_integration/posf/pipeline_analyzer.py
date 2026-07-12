"""Analizador del Pipeline — detecta redundancias sin modificar el flujo."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.posf.enums import OptimizationStrategy
from zovrake_motor.enterprise_integration.posf.models import OptimizationHint


class PipelineAnalyzer:
    """
    Analiza transiciones del Pipeline para minimizar operaciones redundantes.

    Solo genera recomendaciones — no altera el orden ni la lógica del PIO.
    """

    def __init__(self) -> None:
        self._phase_history: dict[str, list[str]] = {}
        self._hints: list[OptimizationHint] = []

    def record_transition(
        self,
        *,
        process_id: UUID,
        phase: str,
        operation: str,
        transition_count: int,
    ) -> OptimizationHint | None:
        key = str(process_id)
        history = self._phase_history.setdefault(key, [])
        history.append(phase)

        hint: OptimizationHint | None = None
        if len(history) >= 2 and history[-1] == history[-2]:
            hint = OptimizationHint.create(
                process_id=process_id,
                strategy=OptimizationStrategy.PIPELINE_FLOW,
                component="PipelineIntegrationOrchestrator",
                message="Transición de fase repetida detectada — revisar flujo interno",
                metadata={"phase": phase, "operation": operation},
            )
            self._hints.append(hint)

        if transition_count > 12:
            hint = OptimizationHint.create(
                process_id=process_id,
                strategy=OptimizationStrategy.PIPELINE_FLOW,
                component="PipelineIntegrationOrchestrator",
                message="Pipeline con transiciones elevadas — evaluar pasos innecesarios",
                metadata={"transition_count": transition_count, "operation": operation},
            )
            self._hints.append(hint)

        return hint

    def hints_for_process(self, process_id: UUID) -> tuple[OptimizationHint, ...]:
        return tuple(h for h in self._hints if h.process_id == process_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "tracked_processes": len(self._phase_history),
            "hints_total": len(self._hints),
            "recent_hints": [h.to_dict() for h in self._hints[-10:]],
        }
