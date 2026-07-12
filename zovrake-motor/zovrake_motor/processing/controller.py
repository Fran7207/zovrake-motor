"""
Controlador del Pipeline Interno.

Únicamente el Coordinator debe utilizar este componente para controlar el flujo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.processing.enums import PipelineExecutionState, PipelineStageType
from zovrake_motor.processing.exceptions import InvalidStageTransitionError, PipelineError
from zovrake_motor.processing.models import (
    PipelineContext,
    PipelineExecution,
    PipelineResult,
    StageRecord,
    StageTransition,
)
from zovrake_motor.processing.pipeline import InternalPipeline


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineController:
    """
    Controla el recorrido secuencial de solicitudes por el Pipeline Interno.

    No ejecuta lógica de negocio ni invoca módulos directamente.
    """

    def __init__(self, pipeline: InternalPipeline | None = None) -> None:
        self._pipeline = pipeline or InternalPipeline()
        self._executions: dict[UUID, PipelineExecution] = {}

    @property
    def pipeline(self) -> InternalPipeline:
        return self._pipeline

    def start(
        self,
        process_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineContext:
        if process_id in self._executions:
            raise PipelineError(f"El Pipeline ya fue iniciado para el proceso: {process_id}")

        first_stage = self._pipeline.first_stage()
        context = PipelineContext(
            process_id=process_id,
            current_stage=first_stage,
            metadata=dict(metadata or {}),
        )
        self._executions[process_id] = PipelineExecution(
            context=context,
            state=PipelineExecutionState.EN_CURSO,
        )
        self._enter_stage(context, first_stage, message="Pipeline iniciado")
        return context

    def advance(self, process_id: UUID) -> PipelineContext:
        execution = self._require_execution(process_id)
        context = execution.context

        if execution.state.is_terminal():
            raise InvalidStageTransitionError(
                f"No se puede avanzar un Pipeline en estado terminal: {execution.state.value}"
            )

        current = context.current_stage
        if current is None:
            raise PipelineError("El contexto no tiene etapa actual")

        next_stage = self._pipeline.next_stage(current)
        if next_stage is None:
            raise InvalidStageTransitionError("No existen etapas posteriores en el Pipeline")

        self._complete_stage(context, current, message=f"Etapa {current.value} completada")
        self._transition(context, from_stage=current, to_stage=next_stage)
        self._enter_stage(context, next_stage, message=f"Etapa {next_stage.value} preparada")
        return context

    def run_sequential(
        self,
        process_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Recorre todas las etapas en orden sin ejecutar procesamiento real."""
        context = self.start(process_id, metadata=metadata)
        completed: list[PipelineStageType] = []

        ordered = self._pipeline.ordered_stage_types()
        completed.append(ordered[0])

        for _ in range(len(ordered) - 1):
            self.advance(process_id)
            completed.append(self._executions[process_id].context.current_stage)  # type: ignore[arg-type]

        final_stage = ordered[-1]
        self._complete_stage(
            context,
            final_stage,
            message=f"Etapa {final_stage.value} completada",
        )
        execution = self._executions[process_id]
        execution.state = PipelineExecutionState.COMPLETADA
        context.updated_at = _utc_now()

        return PipelineResult(
            process_id=process_id,
            success=True,
            state=PipelineExecutionState.COMPLETADA,
            message="Recorrido secuencial del Pipeline completado sin lógica de negocio",
            stages_completed=completed,
            context=context,
        )

    def stop(self, process_id: UUID, *, reason: str) -> PipelineContext:
        execution = self._require_execution(process_id)
        execution.state = PipelineExecutionState.DETENIDA
        execution.stop_reason = reason
        execution.context.updated_at = _utc_now()
        return execution.context

    def finalize(self, process_id: UUID) -> PipelineContext:
        execution = self._require_execution(process_id)
        context = execution.context

        if context.current_stage is not None:
            self._complete_stage(
                context,
                context.current_stage,
                message="Pipeline finalizado por el Coordinator",
            )

        execution.state = PipelineExecutionState.FINALIZADA
        context.updated_at = _utc_now()
        return context

    def get_context(self, process_id: UUID) -> PipelineContext | None:
        execution = self._executions.get(process_id)
        return execution.context if execution else None

    def get_execution(self, process_id: UUID) -> PipelineExecution | None:
        return self._executions.get(process_id)

    def _require_execution(self, process_id: UUID) -> PipelineExecution:
        execution = self._executions.get(process_id)
        if execution is None:
            raise PipelineError(f"Pipeline no iniciado para el proceso: {process_id}")
        return execution

    def _enter_stage(
        self,
        context: PipelineContext,
        stage: PipelineStageType,
        *,
        message: str,
    ) -> None:
        context.current_stage = stage
        context.stage_records.append(StageRecord(stage=stage, message=message))
        context.updated_at = _utc_now()

    def _complete_stage(
        self,
        context: PipelineContext,
        stage: PipelineStageType,
        *,
        message: str,
    ) -> None:
        for record in reversed(context.stage_records):
            if record.stage == stage and record.completed_at is None:
                record.completed_at = _utc_now()
                record.message = message
                break
        context.updated_at = _utc_now()

    def _transition(
        self,
        context: PipelineContext,
        *,
        from_stage: PipelineStageType | None,
        to_stage: PipelineStageType,
        reason: str = "Avance secuencial",
    ) -> None:
        context.transitions.append(
            StageTransition(
                from_stage=from_stage,
                to_stage=to_stage,
                reason=reason,
            )
        )
        context.updated_at = _utc_now()
