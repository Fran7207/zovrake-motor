"""Contrato del Módulo de Integración Empresarial."""

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
from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.models import (
    EnterpriseIntegrationRequest,
    EnterpriseIntegrationResult,
)


class EnterpriseIntegrationPort(ABC):
    """Punto de entrada del Módulo de Integración Empresarial."""

    @abstractmethod
    def prepare(self, request: EnterpriseIntegrationRequest) -> EnterpriseIntegrationResult:
        """Preparará la integración empresarial — sin procesamiento en esta etapa."""

    @abstractmethod
    def start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        """Enrutará inicio de análisis a través del Integration Coordinator."""

    @abstractmethod
    def query_analysis_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        """Enrutará consulta de estado a través del Integration Coordinator."""

    @abstractmethod
    def query_analysis_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        """Enrutará consulta de resultado a través del Integration Coordinator."""

    @abstractmethod
    def cancel_analysis(
        self,
        request: CancelAnalysisRequest,
    ) -> CancelAnalysisResponse | InternalApiErrorResponse:
        """Enrutará cancelación a través del Integration Coordinator."""

    @abstractmethod
    def validate_analysis_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        """Enrutará validación estructural a través del Integration Coordinator."""

    @abstractmethod
    def submit_evidence_center_analysis(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> ErpAnalysisDelivery:
        """Punto de entrada oficial ERP — exclusivamente vía ECG."""

    @abstractmethod
    def query_evidence_center_status(
        self,
        request: EvidenceCenterStatusQuery,
    ) -> ErpAnalysisDelivery:
        """Consulta de estado ERP — exclusivamente vía ECG."""

    @abstractmethod
    def query_evidence_center_result(
        self,
        request: EvidenceCenterResultQuery,
    ) -> ErpAnalysisDelivery:
        """Consulta de resultado ERP — exclusivamente vía ECG."""
