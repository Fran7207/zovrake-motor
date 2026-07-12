"""Modelos inmutables del APQM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage, ApqmQueueOperation


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class QueueItemContext:
    """Contexto aislado de un análisis — nunca compartido entre procesos."""

    process_id: UUID
    project_id: str
    quotation_id: str
    codigo_req: str
    document_ids: tuple[str, ...] = field(default_factory=tuple)
    requirement_metadata: dict[str, Any] = field(default_factory=dict)
    analysis_metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "ecg"

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "codigo_req": self.codigo_req,
            "document_ids": list(self.document_ids),
            "requirement_metadata": self.requirement_metadata,
            "analysis_metadata": self.analysis_metadata,
            "source": self.source,
        }


@dataclass(frozen=True)
class ApqmStageTransition:
    """Transición de etapa registrada para observabilidad."""

    from_stage: ApqmProcessingStage | None
    to_stage: ApqmProcessingStage
    operation: ApqmQueueOperation
    occurred_at: datetime = field(default_factory=utc_now)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_stage": self.from_stage.value if self.from_stage is not None else None,
            "to_stage": self.to_stage.value,
            "operation": self.operation.value,
            "occurred_at": self.occurred_at.isoformat(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class QueueItemRecord:
    """Registro inmutable de un ítem en cola — unidad aislada de procesamiento."""

    item_id: str
    context: QueueItemContext
    internal_request: dict[str, Any]
    stage: ApqmProcessingStage
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    transitions: tuple[ApqmStageTransition, ...] = field(default_factory=tuple)
    execution_metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        *,
        context: QueueItemContext,
        internal_request: dict[str, Any],
    ) -> QueueItemRecord:
        initial_transition = ApqmStageTransition(
            from_stage=None,
            to_stage=ApqmProcessingStage.REQUEST_RECEIVED,
            operation=ApqmQueueOperation.ENQUEUE,
            reason="Solicitud recibida desde ECG",
        )
        return QueueItemRecord(
            item_id=str(uuid4()),
            context=context,
            internal_request=internal_request,
            stage=ApqmProcessingStage.REQUEST_RECEIVED,
            transitions=(initial_transition,),
        )

    def with_transition(
        self,
        to_stage: ApqmProcessingStage,
        operation: ApqmQueueOperation,
        *,
        reason: str = "",
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        execution_metadata: dict[str, Any] | None = None,
    ) -> QueueItemRecord:
        transition = ApqmStageTransition(
            from_stage=self.stage,
            to_stage=to_stage,
            operation=operation,
            reason=reason,
        )
        return QueueItemRecord(
            item_id=self.item_id,
            context=self.context,
            internal_request=self.internal_request,
            stage=to_stage,
            created_at=self.created_at,
            started_at=started_at if started_at is not None else self.started_at,
            completed_at=completed_at if completed_at is not None else self.completed_at,
            transitions=self.transitions + (transition,),
            execution_metadata=(
                dict(execution_metadata)
                if execution_metadata is not None
                else self.execution_metadata
            ),
        )

    def duration_seconds(self) -> float | None:
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "context": self.context.to_dict(),
            "stage": self.stage.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds(),
            "transitions": [item.to_dict() for item in self.transitions],
            "execution_metadata": self.execution_metadata,
        }


@dataclass(frozen=True)
class EnqueueResult:
    """Resultado de encolado — respuesta inmediata al ECG."""

    success: bool
    process_id: UUID
    queue_item_id: str
    stage: ApqmProcessingStage
    message: str
    queue_position: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "process_id": str(self.process_id),
            "queue_item_id": self.queue_item_id,
            "stage": self.stage.value,
            "message": self.message,
            "queue_position": self.queue_position,
            "metadata": self.metadata,
        }
