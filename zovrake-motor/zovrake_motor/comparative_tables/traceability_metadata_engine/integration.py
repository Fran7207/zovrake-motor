"""Integración del TME con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration


class TraceabilityMetadataMotorIntegration:
    """Puente de integración del TME con StateManager y EventManager."""

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
    ) -> TraceabilityMetadataMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_traceability_metadata_enrichment(
        self,
        process_id: UUID,
        *,
        document_id: str,
        model_id: str,
        integrity_report_id: str,
    ) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando enriquecimiento de trazabilidad y metadatos: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Enriquecimiento de trazabilidad iniciado para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "integrity_report_id": integrity_report_id,
                "phase": "traceability_metadata_enrichment",
            },
        )

    def complete_traceability_metadata_enrichment(
        self,
        process_id: UUID,
        result: TraceabilityMetadataEnrichmentResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Enriquecimiento de trazabilidad completado: {result.document_id}",
        )
        event = self._register_event(
            process_id=process_id,
            message=f"Enriquecimiento de trazabilidad completado para {result.document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "model_id": result.model_id,
                "catalog_id": result.catalog.catalog_id,
                "status": result.status.value,
                "enriched_tables_count": result.enriched_tables_count,
                "enrichers_executed": result.enrichers_executed,
                "structure_catalog_preserved": result.structure_catalog_preserved,
                "provider_catalog_preserved": result.provider_catalog_preserved,
                "integrity_report_preserved": result.integrity_report_preserved,
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
