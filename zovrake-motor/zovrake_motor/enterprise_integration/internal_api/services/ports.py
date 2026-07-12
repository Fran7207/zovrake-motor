"""Interfaces de servicio de la API Interna — Arquitectura Hexagonal."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    CancelAnalysisRequest,
    StartAnalysisRequest,
    ValidateAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisResultResponse,
    AnalysisStatusResponse,
    CancelAnalysisResponse,
    InternalApiErrorResponse,
    StartAnalysisResponse,
    ValidateAnalysisResponse,
)


class AnalysisRequestServicePort(ABC):
    """Servicio de solicitudes de análisis."""

    @abstractmethod
    def start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        """Aceptará solicitudes de inicio — sin ejecución real en 8.2."""


class AnalysisStatusServicePort(ABC):
    """Servicio de consulta de estado."""

    @abstractmethod
    def query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        """Consultará estado — sin ejecución real en 8.2."""


class AnalysisResultServicePort(ABC):
    """Servicio de consulta de resultados."""

    @abstractmethod
    def query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        """Consultará resultado — sin datos reales en 8.2."""


class ValidationServicePort(ABC):
    """Servicio de validación estructural."""

    @abstractmethod
    def validate_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        """Validará estructura de solicitudes."""


class ErrorResponseServicePort(ABC):
    """Servicio de respuestas de error controladas."""

    @abstractmethod
    def build_error(
        self,
        *,
        error: InternalApiErrorResponse,
    ) -> InternalApiErrorResponse:
        """Construirá respuestas de error estandarizadas."""

    @abstractmethod
    def from_validation_errors(
        self,
        *,
        process_id,
        errors: tuple[str, ...],
    ) -> InternalApiErrorResponse:
        """Generará error por fallo de validación estructural."""
