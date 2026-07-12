"""Puertos del SVAF — integración con ECG, PIO y FTRRF."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import StartAnalysisRequest
from zovrake_motor.enterprise_integration.svaf.models import SecurityValidationOutcome


class EcgSecurityPort(Protocol):
    """Contrato de seguridad expuesto al ERP Communication Gateway."""

    def validate_inbound_analysis_request(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> SecurityValidationOutcome:
        """Valida solicitud ERP antes de ingresar al Pipeline."""

    def validate_inbound_status_query(
        self,
        request: EvidenceCenterStatusQuery,
    ) -> SecurityValidationOutcome:
        """Valida consulta de estado ERP."""

    def validate_inbound_result_query(
        self,
        request: EvidenceCenterResultQuery,
    ) -> SecurityValidationOutcome:
        """Valida consulta de resultado ERP."""

    def validate_outbound_delivery(
        self,
        delivery: ErpAnalysisDelivery,
        *,
        operation: str,
    ) -> SecurityValidationOutcome:
        """Valida respuesta antes de entregarla al ERP."""


class PipelineValidationGatePort(Protocol):
    """Contrato de compuerta de validación para el PIO."""

    def authorize_pipeline_entry(
        self,
        *,
        process_id: UUID,
        operation: str,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityValidationOutcome:
        """Autoriza entrada al Pipeline solo si la validación es exitosa."""

    def validate_internal_request(
        self,
        request: StartAnalysisRequest,
    ) -> SecurityValidationOutcome:
        """Valida contrato interno antes de orquestación."""
