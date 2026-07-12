"""
Asynchronous Processing & Queue Manager — núcleo del procesamiento asíncrono.

Único responsable de administrar el ciclo de vida de solicitudes en cola.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage, ApqmQueueOperation
from zovrake_motor.enterprise_integration.apqm.events import ApqmEventRecorder
from zovrake_motor.enterprise_integration.apqm.execution_port import ApqmExecutionPort
from zovrake_motor.enterprise_integration.apqm.models import (
    EnqueueResult,
    QueueItemContext,
    QueueItemRecord,
)
from zovrake_motor.enterprise_integration.apqm.store import ApqmQueueStore
from zovrake_motor.enterprise_integration.apqm.worker import AsyncQueueWorker
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import StartAnalysisRequest
from zovrake_motor.states.enums import MotorState

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.ftrrf.recovery_port import FaultRecoveryPort
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
    from zovrake_motor.enterprise_integration.ommf.ports import IntegrationObservabilityPort
    from zovrake_motor.enterprise_integration.posf.ports import IntegrationPerformancePort


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AsyncProcessingQueueManager:
    """
    Administrador de cola lógica y procesamiento asíncrono.

    Recibe solicitudes exclusivamente desde el ECG.
    Ejecuta exclusivamente mediante PIO vía ApqmExecutionPort.
    """

    ECG_SOURCE = "ecg"

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        queue_store: ApqmQueueStore | None = None,
        event_recorder: ApqmEventRecorder | None = None,
        worker: AsyncQueueWorker | None = None,
    ) -> None:
        self._integration = integration
        self._store = queue_store or ApqmQueueStore()
        self._event_recorder = event_recorder or ApqmEventRecorder(integration)
        self._execution: ApqmExecutionPort | None = None
        self._worker: AsyncQueueWorker | None = worker
        self._fault_handler: FaultRecoveryPort | None = None
        self._observability: IntegrationObservabilityPort | None = None
        self._performance_optimizer: IntegrationPerformancePort | None = None
        self._initialized = False

    @property
    def queue_store(self) -> ApqmQueueStore:
        return self._store

    def bind_execution(self, execution: ApqmExecutionPort) -> None:
        self._execution = execution

    def bind_fault_handler(self, fault_handler: FaultRecoveryPort) -> None:
        self._fault_handler = fault_handler

    def bind_observability(self, observability: IntegrationObservabilityPort) -> None:
        self._observability = observability

    def bind_performance_optimizer(self, optimizer: IntegrationPerformancePort) -> None:
        self._performance_optimizer = optimizer

    def bind_worker(self, worker: AsyncQueueWorker) -> None:
        self._worker = worker

    def initialize(self) -> None:
        settings = self._settings()
        if self._worker is None:
            self._worker = AsyncQueueWorker(
                self,
                max_concurrent_workers=settings.max_concurrent_workers,
            )
        self._initialized = True

    def is_ready(self) -> bool:
        settings = self._settings()
        return (
            self._initialized
            and self._execution is not None
            and settings.prepared
        )

    def _settings(self):
        return self._integration.enterprise_integration_settings().async_processing_queue_manager

    def _require_execution(self) -> ApqmExecutionPort:
        if self._execution is None:
            raise RuntimeError("APQM execution no vinculado — requiere Coordinator y PIO")
        return self._execution

    def _sync_motor_state(self, process_id: UUID, motor_state: MotorState, reason: str) -> None:
        state_manager = self._integration.state_manager
        record = state_manager.get_process(process_id)
        if record is None:
            return
        state_manager.update_state(process_id, motor_state, reason)
        self._event_recorder.record_state_sync(process_id, motor_state=motor_state.value)

    def enqueue_start_analysis(
        self,
        request: StartAnalysisRequest,
        *,
        source_context: QueueItemContext,
    ) -> EnqueueResult:
        if not self.is_ready():
            raise RuntimeError("Async Processing Queue Manager no está listo")

        if source_context.source != self.ECG_SOURCE:
            return EnqueueResult(
                success=False,
                process_id=request.process_id,
                queue_item_id="",
                stage=ApqmProcessingStage.CONTROLLED_ERROR,
                message="APQM solo acepta solicitudes desde ECG",
                queue_position=0,
                metadata={"rejected_source": source_context.source},
            )

        settings = self._settings()
        if self._store.count() >= settings.max_queue_depth:
            return EnqueueResult(
                success=False,
                process_id=request.process_id,
                queue_item_id="",
                stage=ApqmProcessingStage.CONTROLLED_ERROR,
                message="Cola lógica llena",
                queue_position=0,
            )

        existing = self._store.get_by_process(request.process_id)
        if existing is not None and existing.stage not in {
            ApqmProcessingStage.PROCESSING_COMPLETED,
            ApqmProcessingStage.PROCESSING_CANCELLED,
            ApqmProcessingStage.CONTROLLED_ERROR,
        }:
            return EnqueueResult(
                success=False,
                process_id=request.process_id,
                queue_item_id=existing.item_id,
                stage=existing.stage,
                message="Proceso ya registrado en cola",
                queue_position=self._store.queue_position(existing.item_id),
            )

        record = QueueItemRecord.create(
            context=source_context,
            internal_request=self._serialize_request(request),
        )
        record = record.with_transition(
            ApqmProcessingStage.QUEUED,
            ApqmQueueOperation.ENQUEUE,
            reason="Solicitud encolada",
        )
        self._store.save(record)

        self._sync_motor_state(
            request.process_id,
            MotorState.PROCESAMIENTO_PENDIENTE,
            "Solicitud encolada para procesamiento asíncrono",
        )

        position = self._store.queue_position(record.item_id)
        self._event_recorder.record_enqueued(
            request.process_id,
            queue_item_id=record.item_id,
            position=position,
        )
        if self._observability is not None:
            self._observability.record_queue_event(
                process_id=request.process_id,
                project_id=source_context.project_id,
                quotation_id=source_context.quotation_id,
                event="enqueued",
                queue_item_id=record.item_id,
            )
            self._observability.record_request_received(
                process_id=request.process_id,
                project_id=source_context.project_id,
                quotation_id=source_context.quotation_id,
                component="AsyncProcessingQueueManager",
            )
        if self._performance_optimizer is not None:
            settings = self._settings()
            self._performance_optimizer.record_queue_metrics(
                process_id=request.process_id,
                queue_depth=self.queue_depth(),
                pending_count=self.pending_count(),
                active_count=self.active_count(),
                max_workers=settings.max_concurrent_workers,
            )
            self._performance_optimizer.record_resource_allocation(
                process_id=request.process_id,
                component="AsyncProcessingQueueManager",
                memory_units=1,
                storage_units=1,
            )

        if settings.auto_start_worker and self._worker is not None:
            self._worker.schedule_item(record.item_id)

        return EnqueueResult(
            success=True,
            process_id=request.process_id,
            queue_item_id=record.item_id,
            stage=ApqmProcessingStage.QUEUED,
            message="Solicitud aceptada en cola lógica",
            queue_position=position,
            metadata={"async": True, "executed": False},
        )

    def next_pending_item_id(self) -> str | None:
        pending = self._store.pending_items()
        if not pending:
            return None
        return pending[0].item_id

    def execute_item(self, item_id: str) -> QueueItemRecord | None:
        record = self._store.get(item_id)
        if record is None:
            return None

        if record.stage not in {
            ApqmProcessingStage.REQUEST_RECEIVED,
            ApqmProcessingStage.QUEUED,
        }:
            return record

        settings = self._settings()
        if self._store.active_count() >= settings.max_concurrent_workers:
            return record

        now = utc_now()
        record = record.with_transition(
            ApqmProcessingStage.ASSIGNED,
            ApqmQueueOperation.ASSIGN,
            reason="Worker asignado",
        )
        self._store.save(record)
        self._event_recorder.record_assigned(record.context.process_id, queue_item_id=item_id)

        record = record.with_transition(
            ApqmProcessingStage.PROCESSING_STARTED,
            ApqmQueueOperation.EXECUTE,
            reason="Inicio de procesamiento",
            started_at=now,
        )
        self._store.save(record)
        self._event_recorder.record_processing_started(
            record.context.process_id,
            queue_item_id=item_id,
        )
        if self._observability is not None:
            ctx = record.context
            self._observability.record_queue_event(
                process_id=ctx.process_id,
                project_id=ctx.project_id,
                quotation_id=ctx.quotation_id,
                event="processing_started",
                queue_item_id=item_id,
            )

        self._sync_motor_state(
            record.context.process_id,
            MotorState.PROCESANDO,
            "Procesamiento asíncrono en ejecución",
        )

        record = record.with_transition(
            ApqmProcessingStage.PROCESSING_IN_EXECUTION,
            ApqmQueueOperation.EXECUTE,
            reason="Ejecución vía PIO",
        )
        self._store.save(record)

        request = self._deserialize_request(record.internal_request)
        response = self._require_execution().execute_start_analysis(request)

        if self._is_failure(response):
            return self._handle_execution_failure(record, item_id, response)

        record = record.with_transition(
            ApqmProcessingStage.PROCESSING_COMPLETED,
            ApqmQueueOperation.COMPLETE,
            reason="Procesamiento completado vía PIO",
            completed_at=utc_now(),
            execution_metadata={
                "response_type": type(response).__name__,
                "executed": False,
            },
        )
        self._store.save(record)
        self._event_recorder.record_processing_completed(
            record.context.process_id,
            queue_item_id=item_id,
        )
        if self._observability is not None:
            ctx = record.context
            self._observability.record_queue_event(
                process_id=ctx.process_id,
                project_id=ctx.project_id,
                quotation_id=ctx.quotation_id,
                event="processing_completed",
                queue_item_id=item_id,
            )
            self._observability.record_request_processed(
                process_id=ctx.process_id,
                component="AsyncProcessingQueueManager",
                success=True,
                project_id=ctx.project_id,
                quotation_id=ctx.quotation_id,
            )
        return record

    @staticmethod
    def _is_failure(response: Any) -> bool:
        return hasattr(response, "success") and response.success is False

    def _handle_execution_failure(
        self,
        record: QueueItemRecord,
        item_id: str,
        response: Any,
    ) -> QueueItemRecord:
        error_message = getattr(response, "message", "Error controlado")
        error_code = ""
        error_code_obj = getattr(response, "error_code", None)
        if error_code_obj is not None:
            error_code = getattr(error_code_obj, "value", str(error_code_obj))

        self._event_recorder.record_controlled_error(
            record.context.process_id,
            queue_item_id=item_id,
            error_message=error_message,
        )

        if self._fault_handler is None:
            record = record.with_transition(
                ApqmProcessingStage.CONTROLLED_ERROR,
                ApqmQueueOperation.ERROR,
                reason=error_message,
                completed_at=utc_now(),
                execution_metadata={"response_type": type(response).__name__},
            )
            self._store.save(record)
            return record

        request = self._deserialize_request(record.internal_request)
        attempt = 1
        outcome = self._fault_handler.handle_failure(
            process_id=record.context.process_id,
            item_id=item_id,
            error_message=error_message,
            error_code=error_code,
            requested_by="apqm",
            attempt=attempt,
        )

        while outcome.should_retry:
            attempt += 1
            retry_response = self._require_execution().execute_start_analysis(request)
            if not self._is_failure(retry_response):
                self._fault_handler.recover_process(
                    process_id=record.context.process_id,
                    requested_by="apqm",
                )
                record = record.with_transition(
                    ApqmProcessingStage.PROCESSING_COMPLETED,
                    ApqmQueueOperation.COMPLETE,
                    reason="Procesamiento completado tras recuperación",
                    completed_at=utc_now(),
                    execution_metadata={
                        "response_type": type(retry_response).__name__,
                        "recovered": True,
                        "attempts": attempt,
                    },
                )
                self._store.save(record)
                self._event_recorder.record_processing_completed(
                    record.context.process_id,
                    queue_item_id=item_id,
                )
                return record

            outcome = self._fault_handler.handle_failure(
                process_id=record.context.process_id,
                item_id=item_id,
                error_message=getattr(retry_response, "message", error_message),
                error_code=error_code,
                requested_by="apqm",
                attempt=attempt,
            )

        record = record.with_transition(
            ApqmProcessingStage.CONTROLLED_ERROR,
            ApqmQueueOperation.ERROR,
            reason=outcome.message,
            completed_at=utc_now(),
            execution_metadata={
                "response_type": type(response).__name__,
                "recovery_decision": outcome.decision.value,
                "error_category": outcome.error_record.category.value,
                "attempts": attempt,
            },
        )
        self._store.save(record)
        return record

    def process_all_pending(self) -> int:
        if self._worker is None:
            return 0
        return self._worker.process_pending_synchronously()

    def get_item_by_process(self, process_id: UUID) -> QueueItemRecord | None:
        return self._store.get_by_process(process_id)

    def queue_depth(self) -> int:
        return self._store.count()

    def pending_count(self) -> int:
        return self._store.pending_count()

    def active_count(self) -> int:
        return self._store.active_count()

    @staticmethod
    def _serialize_request(request: StartAnalysisRequest) -> dict[str, Any]:
        return {
            "process_id": str(request.process_id),
            "codigo_req": request.codigo_req,
            "contract_version": request.contract_version,
            "document_ids": list(request.document_ids),
            "metadata": dict(request.metadata),
        }

    @staticmethod
    def _deserialize_request(payload: dict[str, Any]) -> StartAnalysisRequest:
        from uuid import UUID as UuidType

        return StartAnalysisRequest(
            process_id=UuidType(payload["process_id"]),
            codigo_req=payload["codigo_req"],
            contract_version=payload.get("contract_version", "v1"),
            document_ids=tuple(payload.get("document_ids", ())),
            metadata=dict(payload.get("metadata", {})),
        )

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "queue_depth": self.queue_depth(),
            "pending_count": self.pending_count(),
            "active_count": self.active_count(),
            "execution_bound": self._execution is not None,
            "max_concurrent_workers": settings.max_concurrent_workers,
            "max_queue_depth": settings.max_queue_depth,
            "observability_bound": self._observability is not None,
            "performance_optimizer_bound": self._performance_optimizer is not None,
        }
