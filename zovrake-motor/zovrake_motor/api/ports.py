"""Puertos hexagonales de la API de Integración Pública."""

from __future__ import annotations

from typing import Protocol

from zovrake_motor.api.models import (
    PublicAnalysisRequest,
    PublicAnalysisResponse,
    PublicResultQuery,
    PublicStatusQuery,
)


class IntegrationGatewayPort(Protocol):
    """
    Puerto hacia la plataforma de integración empresarial (PM8).

    La API pública nunca habla con el Motor Inteligente directamente.
    """

    def submit_analysis(self, request: PublicAnalysisRequest) -> PublicAnalysisResponse:
        """Envía análisis al ECG vía plataforma PM8."""

    def query_status(self, query: PublicStatusQuery) -> PublicAnalysisResponse:
        """Consulta estado del análisis."""

    def query_result(self, query: PublicResultQuery) -> PublicAnalysisResponse:
        """Consulta resultado estructurado del análisis."""


class HttpTransportPort(Protocol):
    """
    Puerto de transporte HTTP — preparado para Implementación 9.2.

    No se implementa en 9.1; solo declara el contrato de extensión.
    """

    def is_prepared(self) -> bool:
        """Indica si el transporte HTTP está preparado."""


class ObservabilityPort(Protocol):
    """Puerto de observabilidad de la API pública — sin herramientas específicas."""

    def record_analysis_event(
        self,
        *,
        analysis_id: str,
        operation: str,
        stage: str,
        success: bool,
        metadata: dict | None = None,
    ) -> None:
        """Registra evento de integración API."""
