"""Adaptador de ejecución APQM → Coordinator → PIO."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.enterprise_integration.apqm.execution_port import ApqmExecutionPort
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import StartAnalysisRequest
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    InternalApiErrorResponse,
    StartAnalysisResponse,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class EnterpriseIntegrationApqmExecutor(ApqmExecutionPort):
    """Ejecuta análisis exclusivamente mediante el Integration Coordinator y PIO."""

    def __init__(self, service: EnterpriseIntegrationService) -> None:
        self._service = service

    def execute_start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        return self._service.start_analysis(request)
