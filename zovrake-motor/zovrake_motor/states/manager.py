"""
Sistema Central de Gestión de Estados del Motor Inteligente.

Única autoridad para crear, consultar y actualizar el estado de cada solicitud.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.exceptions import ProcessNotFoundError, StateManagementError
from zovrake_motor.states.lifecycle import StateLifecycle
from zovrake_motor.states.models import ProcessStateRecord, StateTransition
from zovrake_motor.states.observability import StateChangeObserver
from zovrake_motor.states.store import StateStore


class StateManager:
    """
    Administrador central de estados del Motor.

    No ejecuta procesamiento, no interpreta documentos ni toma decisiones.
    """

    def __init__(
        self,
        *,
        store: StateStore | None = None,
        lifecycle: StateLifecycle | None = None,
    ) -> None:
        self._store = store or StateStore()
        self._lifecycle = lifecycle or StateLifecycle()
        self._observers: list[StateChangeObserver] = []

    @property
    def store(self) -> StateStore:
        return self._store

    @property
    def lifecycle(self) -> StateLifecycle:
        return self._lifecycle

    def register_observer(self, observer: StateChangeObserver) -> None:
        """Preparado para observabilidad — eventos y métricas en etapas futuras."""
        self._observers.append(observer)

    def create_process(
        self,
        process_id: UUID,
        codigo_req: str,
        *,
        metadata: dict[str, Any] | None = None,
        initial_state: MotorState = MotorState.INICIALIZADO,
    ) -> ProcessStateRecord:
        if self._store.exists(process_id):
            raise StateManagementError(f"El proceso ya existe: {process_id}")

        self._lifecycle.validate_state(initial_state)
        record = ProcessStateRecord(
            process_id=process_id,
            current_state=initial_state,
            codigo_req=codigo_req,
            metadata=dict(metadata or {}),
        )
        self._store.save(record)
        return record

    def get_process(self, process_id: UUID) -> ProcessStateRecord | None:
        return self._store.get(process_id)

    def require_process(self, process_id: UUID) -> ProcessStateRecord:
        return self._store.require(process_id)

    def update_state(
        self,
        process_id: UUID,
        to_state: MotorState,
        reason: str,
    ) -> ProcessStateRecord:
        self._lifecycle.validate_state(to_state)
        record = self._store.require(process_id)

        transition = StateTransition(
            from_state=record.current_state,
            to_state=to_state,
            reason=reason,
        )
        record.current_state = to_state
        record.history.append(transition)
        record.updated_at = transition.occurred_at
        self._store.save(record)
        self._notify_observers(record, transition)
        return record

    def list_process_ids(self) -> list[UUID]:
        return self._store.list_process_ids()

    def count(self) -> int:
        return self._store.count()

    def snapshot(self) -> dict[str, Any]:
        return {
            "process_count": self.count(),
            "official_states": [state.value for state in self._lifecycle.OFFICIAL_STATES],
            "processes": [
                self._store.get(process_id).to_dict()  # type: ignore[union-attr]
                for process_id in self._store.list_process_ids()
            ],
        }

    def _notify_observers(
        self,
        record: ProcessStateRecord,
        transition: StateTransition,
    ) -> None:
        for observer in self._observers:
            observer.on_state_change(record, transition)
