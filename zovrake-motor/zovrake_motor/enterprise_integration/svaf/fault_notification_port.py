"""Notificación de fallos de validación al FTRRF."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.ftrrf.models import RecoveryOutcome


class ValidationFaultNotificationPort(Protocol):
    """Contrato para notificar fallos de validación al FTRRF."""

    def notify_validation_failure(
        self,
        *,
        process_id: UUID,
        error_message: str,
        error_code: str = "structural_validation_failed",
        context_metadata: dict | None = None,
    ) -> RecoveryOutcome:
        """Clasifica, registra y bloquea el avance del Pipeline."""
