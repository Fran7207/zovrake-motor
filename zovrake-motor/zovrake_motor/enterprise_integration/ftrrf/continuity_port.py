"""Puerto de continuidad — coordinación con el Pipeline Integration Orchestrator."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class IntegrationContinuityPort(Protocol):
    """
    Contrato para coordinar continuidad/finalización mediante el PIO.

    El FTRRF nunca decide la continuidad sin coordinar con el PIO.
    """

    def pipeline_context_snapshot(self, process_id: UUID) -> dict[str, Any] | None:
        """Trazabilidad del proceso conservada por el PIO."""

    def traceability_preserved(self, process_id: UUID) -> bool:
        """Confirma que el proceso conserva su trazabilidad tras el fallo."""
