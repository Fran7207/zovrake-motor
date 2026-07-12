"""Adaptador de notificación SVAF → FTRRF."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from zovrake_motor.enterprise_integration.svaf.fault_notification_port import (
    ValidationFaultNotificationPort,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.ftrrf.framework import (
        FaultToleranceRetryRecoveryFramework,
    )
    from zovrake_motor.enterprise_integration.ftrrf.models import RecoveryOutcome


class EnterpriseIntegrationSvafFaultNotifier(ValidationFaultNotificationPort):
    """Notifica fallos de validación al FTRRF."""

    def __init__(self, framework: FaultToleranceRetryRecoveryFramework) -> None:
        self._framework = framework

    def notify_validation_failure(
        self,
        *,
        process_id: UUID,
        error_message: str,
        error_code: str = "structural_validation_failed",
        context_metadata: dict | None = None,
    ) -> RecoveryOutcome:
        return self._framework.handle_failure(
            process_id=process_id,
            item_id=f"svaf-{process_id}",
            error_message=error_message,
            error_code=error_code,
            origin_component="security_validation_audit_framework",
            attempt=1,
            requested_by="svaf",
            context_metadata=context_metadata,
        )
