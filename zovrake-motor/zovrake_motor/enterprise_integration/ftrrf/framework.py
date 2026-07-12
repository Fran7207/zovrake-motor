"""
Fault Tolerance, Retry & Recovery Framework — núcleo de resiliencia.

Único responsable de detectar, clasificar, registrar y administrar fallos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ftrrf.classifier import ErrorClassifier
from zovrake_motor.enterprise_integration.ftrrf.continuity_port import IntegrationContinuityPort
from zovrake_motor.enterprise_integration.ftrrf.enums import (
    ErrorCategory,
    RecoveryDecision,
    RecoveryStage,
    RecoveryStatus,
)
from zovrake_motor.enterprise_integration.ftrrf.events import FtrrfEventRecorder
from zovrake_motor.enterprise_integration.ftrrf.models import (
    ErrorRecord,
    RecoveryOutcome,
    RetryPolicy,
)
from zovrake_motor.enterprise_integration.ftrrf.retry_policy import RetryPolicyRegistry
from zovrake_motor.enterprise_integration.ftrrf.store import ErrorRegistryStore
from zovrake_motor.states.enums import MotorState

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
    from zovrake_motor.enterprise_integration.ommf.ports import IntegrationObservabilityPort


class FaultToleranceRetryRecoveryFramework:
    """
    Framework de tolerancia a fallos, reintentos y recuperación.

    Solo el APQM está autorizado a solicitar acciones de recuperación.
    Coordina la continuidad exclusivamente mediante el PIO.
    """

    AUTHORIZED_REQUESTER = "apqm"
    SVAF_REQUESTER = "svaf"

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        classifier: ErrorClassifier | None = None,
        retry_registry: RetryPolicyRegistry | None = None,
        error_store: ErrorRegistryStore | None = None,
        event_recorder: FtrrfEventRecorder | None = None,
    ) -> None:
        self._integration = integration
        self._classifier = classifier or ErrorClassifier()
        self._retry_registry = retry_registry or self._build_registry()
        self._store = error_store or ErrorRegistryStore()
        self._event_recorder = event_recorder or FtrrfEventRecorder(integration)
        self._continuity: IntegrationContinuityPort | None = None
        self._observability: IntegrationObservabilityPort | None = None
        self._initialized = False

    @property
    def error_store(self) -> ErrorRegistryStore:
        return self._store

    def bind_continuity(self, continuity: IntegrationContinuityPort) -> None:
        self._continuity = continuity

    def bind_observability(self, observability: IntegrationObservabilityPort) -> None:
        self._observability = observability

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized and self._settings().prepared

    def _settings(self):
        return (
            self._integration.enterprise_integration_settings().fault_tolerance_retry_recovery_framework
        )

    def _build_registry(self) -> RetryPolicyRegistry:
        settings = self._settings()
        return RetryPolicyRegistry(
            default_max_retries=settings.default_max_retries,
            default_interval_seconds=settings.default_retry_interval_seconds,
        )

    def _authorize(self, requested_by: str) -> None:
        if requested_by not in {self.AUTHORIZED_REQUESTER, self.SVAF_REQUESTER}:
            raise PermissionError(
                "Solo APQM o SVAF pueden solicitar acciones de recuperación al FTRRF"
            )

    def _sync_motor_state(self, process_id: UUID, motor_state: MotorState, reason: str) -> None:
        state_manager = self._integration.state_manager
        record = state_manager.get_process(process_id)
        if record is None:
            return
        state_manager.update_state(process_id, motor_state, reason)
        self._event_recorder.record_state_sync(process_id, motor_state=motor_state.value)

    def _terminal_state_for(self, category: ErrorCategory) -> MotorState:
        if category == ErrorCategory.VALIDATION:
            return MotorState.ERROR_VALIDACION
        return MotorState.ERROR_INTERNO

    def handle_failure(
        self,
        *,
        process_id: UUID,
        item_id: str,
        error_message: str,
        error_code: str = "",
        origin_component: str = "pipeline_integration_orchestrator",
        attempt: int = 1,
        requested_by: str = "apqm",
        context_metadata: dict[str, Any] | None = None,
    ) -> RecoveryOutcome:
        self._authorize(requested_by)
        if not self.is_ready():
            raise RuntimeError("Fault Tolerance Framework no está listo")

        classification = self._classifier.classify(
            error_code=error_code,
            description=error_message,
            origin_component=origin_component,
        )
        policy = self._retry_registry.policy_for(classification.category)

        record = ErrorRecord.create(
            process_id=process_id,
            classification=classification,
            error_code=error_code,
            recovery_status=RecoveryStatus.PENDING,
            retry_count=attempt - 1,
            metadata={"item_id": item_id, **(context_metadata or {})},
        )
        self._store.save(record)
        self._event_recorder.record_fault_detected(
            process_id,
            error_id=record.error_id,
            category=classification.category.value,
            severity=self._event_severity(classification.severity.value),
        )
        if self._observability is not None:
            self._observability.record_fault_event(
                process_id=process_id,
                event="failure",
                category=classification.category.value,
                attempt=attempt,
            )

        traceability_preserved = self._traceability_preserved(process_id)

        if policy.allows_retry(attempt):
            return self._schedule_retry(
                process_id=process_id,
                record=record,
                policy=policy,
                attempt=attempt,
                traceability_preserved=traceability_preserved,
            )

        return self._finalize_failure(
            process_id=process_id,
            record=record,
            policy=policy,
            classification_category=classification.category,
            traceability_preserved=traceability_preserved,
        )

    def _schedule_retry(
        self,
        *,
        process_id: UUID,
        record: ErrorRecord,
        policy: RetryPolicy,
        attempt: int,
        traceability_preserved: bool,
    ) -> RecoveryOutcome:
        retries_remaining = max(policy.max_retries - attempt, 0)
        updated = record.with_status(RecoveryStatus.RETRY_SCHEDULED, retry_count=attempt)
        self._store.save(updated)

        self._event_recorder.record_recovery_started(process_id, error_id=record.error_id)
        self._event_recorder.record_retry_scheduled(
            process_id,
            error_id=record.error_id,
            attempt=attempt,
            retries_remaining=retries_remaining,
        )
        self._sync_motor_state(
            process_id,
            MotorState.PROCESANDO,
            "Reintento programado por fallo recuperable",
        )
        if self._observability is not None:
            self._observability.record_fault_event(
                process_id=process_id,
                event="retry",
                attempt=attempt,
            )
        return RecoveryOutcome(
            process_id=process_id,
            decision=RecoveryDecision.RETRY,
            stage=RecoveryStage.RETRY_SCHEDULED,
            error_record=updated,
            retry_policy=policy,
            retries_remaining=retries_remaining,
            message="Reintento programado — error recuperable",
            traceability_preserved=traceability_preserved,
            metadata={"attempt": attempt},
        )

    def _finalize_failure(
        self,
        *,
        process_id: UUID,
        record: ErrorRecord,
        policy: RetryPolicy,
        classification_category: ErrorCategory,
        traceability_preserved: bool,
    ) -> RecoveryOutcome:
        if policy.recoverable:
            decision = RecoveryDecision.CANCEL
            stage = RecoveryStage.PROCESS_CANCELLED
            status = RecoveryStatus.CANCELLED
            message = "Reintentos agotados — proceso cancelado"
        else:
            decision = RecoveryDecision.TERMINAL_FAILURE
            stage = RecoveryStage.FINALIZED_WITH_ERROR
            status = RecoveryStatus.FAILED
            message = "Error no recuperable — finalización controlada"

        updated = record.with_status(status)
        self._store.save(updated)

        if decision == RecoveryDecision.CANCEL:
            self._event_recorder.record_process_cancelled(
                process_id,
                error_id=record.error_id,
                reason=message,
            )
        else:
            self._event_recorder.record_finalized_with_error(
                process_id,
                error_id=record.error_id,
            )

        self._sync_motor_state(
            process_id,
            self._terminal_state_for(classification_category),
            message,
        )
        if self._observability is not None:
            event = "permanent_failure" if decision == RecoveryDecision.TERMINAL_FAILURE else "cancelled"
            self._observability.record_fault_event(
                process_id=process_id,
                event=event,
                category=classification_category.value,
            )
            if decision == RecoveryDecision.CANCEL:
                self._observability.record_process_cancelled(process_id=process_id)
        return RecoveryOutcome(
            process_id=process_id,
            decision=decision,
            stage=stage,
            error_record=updated,
            retry_policy=policy,
            retries_remaining=0,
            message=message,
            traceability_preserved=traceability_preserved,
        )

    def recover_process(
        self,
        *,
        process_id: UUID,
        requested_by: str = "apqm",
    ) -> RecoveryOutcome | None:
        self._authorize(requested_by)
        record = self._store.latest_for_process(process_id)
        if record is None:
            return None
        if not record.recoverable:
            return None

        self._event_recorder.record_recovery_started(process_id, error_id=record.error_id)
        traceability_preserved = self._traceability_preserved(process_id)
        updated = record.with_status(RecoveryStatus.RECOVERED)
        self._store.save(updated)
        self._event_recorder.record_recovery_completed(process_id, error_id=record.error_id)
        self._sync_motor_state(
            process_id,
            MotorState.PROCESANDO,
            "Proceso recuperado preservando trazabilidad",
        )
        if self._observability is not None:
            self._observability.record_fault_event(
                process_id=process_id,
                event="recovery",
            )
        policy = self._retry_registry.policy_for(record.category)
        return RecoveryOutcome(
            process_id=process_id,
            decision=RecoveryDecision.RECOVER,
            stage=RecoveryStage.RECOVERY_COMPLETED,
            error_record=updated,
            retry_policy=policy,
            retries_remaining=max(policy.max_retries - record.retry_count, 0),
            message="Proceso recuperado sin reiniciar desde cero",
            traceability_preserved=traceability_preserved,
        )

    def mark_recovered(self, process_id: UUID) -> None:
        record = self._store.latest_for_process(process_id)
        if record is None:
            return
        updated = record.with_status(RecoveryStatus.RECOVERED)
        self._store.save(updated)
        self._event_recorder.record_recovery_completed(process_id, error_id=record.error_id)

    def _traceability_preserved(self, process_id: UUID) -> bool:
        if self._continuity is None:
            return False
        return self._continuity.traceability_preserved(process_id)

    @staticmethod
    def _event_severity(value: str):
        from zovrake_motor.events.enums import EventSeverity

        mapping = {
            "info": EventSeverity.INFO,
            "warning": EventSeverity.WARNING,
            "error": EventSeverity.ERROR,
            "critical": EventSeverity.ERROR,
        }
        return mapping.get(value, EventSeverity.ERROR)

    def errors_for_process(self, process_id: UUID) -> tuple[ErrorRecord, ...]:
        return self._store.by_process(process_id)

    def observability_snapshot(self) -> dict[str, Any]:
        return {
            "total_errors": self._store.count(),
            "by_category": self._store.count_by_category(),
            "by_status": self._store.count_by_status(),
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "continuity_bound": self._continuity is not None,
            "observability_bound": self._observability is not None,
            "retry_policies": self._retry_registry.snapshot(),
            "observability": self.observability_snapshot(),
        }
