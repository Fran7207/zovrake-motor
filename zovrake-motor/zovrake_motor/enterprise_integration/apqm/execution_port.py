"""Puerto de ejecución APQM → PIO — nunca acceso directo al Motor."""

from __future__ import annotations

from typing import Protocol

from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    StartAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    InternalApiErrorResponse,
    StartAnalysisResponse,
)


class ApqmExecutionPort(Protocol):
    """Contrato para ejecutar análisis exclusivamente vía PIO."""

    def execute_start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        """Ejecuta StartAnalysis a través del Coordinator y PIO."""
