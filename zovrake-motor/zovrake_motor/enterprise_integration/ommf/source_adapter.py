"""Adaptador de fuentes — consolidación desde componentes hermanos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class EnterpriseIntegrationOmmfSourceAdapter:
    """
    Provee snapshots de PIO, APQM, FTRRF y SVAF al OMMF.

    Patrón pull — no invade lógica de negocio.
    """

    def __init__(self, service: EnterpriseIntegrationService) -> None:
        self._service = service

    def pipeline_snapshot(self) -> dict[str, Any] | None:
        return self._service.get_pipeline_orchestrator_snapshot()

    def queue_snapshot(self) -> dict[str, Any] | None:
        return self._service.get_async_processing_queue_snapshot()

    def fault_snapshot(self) -> dict[str, Any] | None:
        return self._service.get_fault_tolerance_snapshot()

    def security_snapshot(self) -> dict[str, Any] | None:
        return self._service.get_security_validation_audit_snapshot()
