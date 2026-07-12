"""Puerto de encolado ECG → APQM — único punto de entrada de solicitudes."""

from __future__ import annotations

from typing import Protocol

from zovrake_motor.enterprise_integration.apqm.models import EnqueueResult, QueueItemContext
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    StartAnalysisRequest,
)


class EcgEnqueuePort(Protocol):
    """Contrato de encolado exclusivo desde el ERP Communication Gateway."""

    def enqueue_start_analysis(
        self,
        request: StartAnalysisRequest,
        *,
        source_context: QueueItemContext,
    ) -> EnqueueResult:
        """Encola solicitud de análisis — respuesta no bloqueante."""

    def queue_depth(self) -> int:
        """Profundidad actual de la cola lógica."""

    def pending_count(self) -> int:
        """Solicitudes pendientes de procesamiento."""
