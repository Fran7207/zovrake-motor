"""Integración del CMB con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildResult,
)
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration


class ComparativeModelMotorIntegration:
    """Puente de integración del CMB con StateManager y EventManager."""

    MODULE_NAME = "comparative_tables"

    def __init__(
        self,
        *,
        state_manager: StateManager,
        event_manager: EventManager,
    ) -> None:
        self._state_manager = state_manager
        self._event_manager = event_manager

    @classmethod
    def from_comparative_tables_integration(
        cls,
        integration: ComparativeTablesMotorIntegration,
    ) -> ComparativeModelMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_comparative_model_build(
        self,
        process_id: UUID,
        *,
        document_id: str,
        model_id: str,
        enriched_catalog_id: str,
    ) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando construcción del Modelo Comparativo Definitivo: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Construcción de modelo comparativo iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "enriched_catalog_id": enriched_catalog_id,
                "phase": "comparative_model_build",
            },
        )

    def complete_comparative_model_build(
        self,
        process_id: UUID,
        result: ComparativeModelBuildResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Modelo Comparativo Definitivo construido: {result.document_id}",
        )
        event = self._register_event(
            process_id=process_id,
            message=(
                f"Modelo Comparativo Definitivo construido para {result.document_id}"
            ),
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "model_id": result.model_id,
                "catalog_id": result.catalog.catalog_id,
                "status": result.status.value,
                "models_built_count": result.models_built_count,
                "builders_executed": result.builders_executed,
                "pm6_definitive_output_contract": result.catalog.pm6_definitive_output_contract,
                "pm7_input_contract_prepared": result.catalog.pm7_input_contract_prepared,
                "enriched_catalog_preserved": result.enriched_catalog_preserved,
                "domain_model_preserved": result.domain_model_preserved,
            },
        )

        return {
            "process_state": state.to_dict(),
            "event": event.to_dict(),
        }

    def _transition_state(self, process_id: UUID, to_state: MotorState, reason: str):
        if self._state_manager.get_process(process_id) is None:
            self._state_manager.create_process(process_id, str(process_id))
        return self._state_manager.update_state(process_id, to_state, reason)

    def _register_event(
        self,
        *,
        process_id: UUID,
        message: str,
        event_type: EventType,
        severity: EventSeverity,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return self._event_manager.create_and_register(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=EventCategory.PROCESSING,
            severity=severity,
        )
