"""Adaptador de continuidad FTRRF → PIO (vía servicio de integración)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ftrrf.continuity_port import IntegrationContinuityPort

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class EnterpriseIntegrationFtrrfContinuityAdapter(IntegrationContinuityPort):
    """Coordina la continuidad del proceso exclusivamente mediante el PIO."""

    def __init__(self, service: EnterpriseIntegrationService) -> None:
        self._service = service

    def pipeline_context_snapshot(self, process_id: UUID) -> dict[str, Any] | None:
        context = self._service.get_pipeline_context(process_id)
        if context is None:
            return None
        return context.to_dict() if hasattr(context, "to_dict") else None

    def traceability_preserved(self, process_id: UUID) -> bool:
        context = self._service.get_pipeline_context(process_id)
        if context is None:
            return False
        transitions = getattr(context, "transitions", None)
        return bool(transitions)
