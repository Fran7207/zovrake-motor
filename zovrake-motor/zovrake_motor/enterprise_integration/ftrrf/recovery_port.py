"""Puerto de recuperación — único invocado por el APQM."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from zovrake_motor.enterprise_integration.ftrrf.models import RecoveryOutcome


class FaultRecoveryPort(Protocol):
    """
    Contrato de tolerancia a fallos expuesto al APQM.

    El APQM es el único componente autorizado para solicitar recuperación.
    """

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
        context_metadata: dict | None = None,
    ) -> RecoveryOutcome:
        """Detecta, clasifica y decide la continuidad ante un fallo controlado."""

    def recover_process(
        self,
        *,
        process_id: UUID,
        requested_by: str = "apqm",
    ) -> RecoveryOutcome | None:
        """Recupera un proceso interrumpido preservando su trazabilidad."""
