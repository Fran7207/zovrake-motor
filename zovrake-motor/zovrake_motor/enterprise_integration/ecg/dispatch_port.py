"""Puerto de despacho hacia Coordinator → PIO → API Interna."""

from __future__ import annotations

from typing import Protocol

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


class EcgIntegrationDispatchPort(Protocol):
    """Contrato de despacho interno — únicamente vía Coordinator y PIO."""

    def dispatch_start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse: ...

    def dispatch_query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse: ...

    def dispatch_query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse: ...

    def get_pipeline_context_dict(self, process_id) -> dict | None: ...
