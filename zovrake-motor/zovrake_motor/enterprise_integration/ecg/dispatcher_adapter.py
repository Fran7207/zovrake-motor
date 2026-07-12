"""Adaptador de despacho ECG → Coordinator → PIO → API Interna."""

from __future__ import annotations

from typing import TYPE_CHECKING

from zovrake_motor.enterprise_integration.ecg.dispatch_port import EcgIntegrationDispatchPort
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    StartAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisResultResponse,
    AnalysisStatusResponse,
    InternalApiErrorResponse,
    StartAnalysisResponse,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class EnterpriseIntegrationEcgDispatcher(EcgIntegrationDispatchPort):
    """Enruta exclusivamente a través del Integration Coordinator y PIO."""

    def __init__(self, service: EnterpriseIntegrationService) -> None:
        self._service = service

    def dispatch_start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        return self._service.start_analysis(request)

    def dispatch_query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        return self._service.query_analysis_status(request)

    def dispatch_query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        return self._service.query_analysis_result(request)

    def get_pipeline_context_dict(self, process_id):
        return self._service.get_pipeline_context(process_id)
