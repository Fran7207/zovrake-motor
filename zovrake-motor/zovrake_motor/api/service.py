"""
Servicio de la API de Integración Pública.

Fachada preparada para que el ERP (Centro de Evidencias) invoque el Motor
sin acoplarse a su arquitectura interna. El transporte HTTP REST se expone en 9.2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.api.adapters.ecg_adapter import EcgGatewayAdapter
from zovrake_motor.api.enums import (
    IntegrationApiErrorCode,
    IntegrationApiLifecycleStage,
    IntegrationApiOperation,
)
from zovrake_motor.api.models import (
    AnalysisStatusPayload,
    ControlledErrorPayload,
    PublicAnalysisRequest,
    PublicAnalysisResponse,
    PublicResultQuery,
    PublicStatusQuery,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService
from zovrake_motor.events import EventManager, EventType
from zovrake_motor.states import StateManager


class IntegrationApiService:
    """
    Punto de entrada arquitectónico de la API de Integración Pública.

    Responsabilidades:
    - validar el contrato público;
    - delegar exclusivamente en ECG (PM8);
    - registrar eventos de ciclo de vida;
    - devolver respuestas estructuradas al ERP.

    No ejecuta inteligencia ni modifica el ERP.
    """

    MODULE_NAME = "integration_api"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        enterprise_service: EnterpriseIntegrationService | None = None,
    ) -> None:
        self._config = config_provider or ConfigurationProvider.default()
        self._state_manager = state_manager or StateManager()
        self._event_manager = event_manager or EventManager()
        self._enterprise_service = enterprise_service or EnterpriseIntegrationService(
            config_provider=self._config,
            state_manager=self._state_manager,
            event_manager=self._event_manager,
        )
        self._gateway = EcgGatewayAdapter(self._enterprise_service)
        self._initialized = False
        self._events: list[dict[str, Any]] = []

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def initialize(self) -> None:
        self._enterprise_service.initialize()
        self._initialized = True

    def is_available(self) -> bool:
        return self._initialized and self._enterprise_service.is_available()

    def start_analysis(self, request: PublicAnalysisRequest) -> PublicAnalysisResponse:
        self.initialize()
        validation_error = self._validate_start_request(request)
        if validation_error is not None:
            response = PublicAnalysisResponse(
                analysis_id=request.analysis_id,
                codigo_req=request.codigo_req,
                project_id=request.project_id,
                quotation_id=request.quotation_id,
                success=False,
                status=AnalysisStatusPayload(
                    stage=IntegrationApiLifecycleStage.FAILED,
                    processing_status="validation_failed",
                    message=validation_error.message,
                ),
                error=validation_error,
            )
            self._record_event(
                request.analysis_id,
                IntegrationApiOperation.START_ANALYSIS,
                IntegrationApiLifecycleStage.FAILED,
                success=False,
            )
            return response

        self._record_event(
            request.analysis_id,
            IntegrationApiOperation.START_ANALYSIS,
            IntegrationApiLifecycleStage.ANALYSIS_CREATED,
            success=True,
        )
        response = self._gateway.submit_analysis(request)
        self._record_event(
            request.analysis_id,
            IntegrationApiOperation.START_ANALYSIS,
            response.status.stage,
            success=response.success,
        )
        return response

    def query_status(self, query: PublicStatusQuery) -> PublicAnalysisResponse:
        self.initialize()
        response = self._gateway.query_status(query)
        self._record_event(
            query.analysis_id,
            IntegrationApiOperation.QUERY_STATUS,
            response.status.stage,
            success=response.success,
        )
        return response

    def query_result(self, query: PublicResultQuery) -> PublicAnalysisResponse:
        self.initialize()
        response = self._gateway.query_result(query)
        self._record_event(
            query.analysis_id,
            IntegrationApiOperation.QUERY_RESULT,
            response.status.stage,
            success=response.success,
        )
        return response

    def process_pending(self) -> int:
        """Procesa cola asíncrona de la plataforma PM8 (útil en pruebas y workers)."""
        self.initialize()
        return self._enterprise_service.process_async_queue_pending()

    def snapshot(self) -> dict[str, Any]:
        settings = self._config.integration_api()
        return {
            "module": self.MODULE_NAME,
            "initialized": self._initialized,
            "available": self.is_available(),
            "http_transport_prepared": settings.http_transport_prepared,
            "authentication_prepared": settings.authentication_prepared,
            "authorization_prepared": settings.authorization_prepared,
            "public_contract_version": settings.public_contract_version,
            "events_recorded": len(self._events),
            "enterprise_integration_bound": self._enterprise_service.is_available(),
        }

    def events_for_analysis(self, analysis_id: UUID) -> tuple[dict[str, Any], ...]:
        return tuple(event for event in self._events if event["analysis_id"] == str(analysis_id))

    @staticmethod
    def _validate_start_request(request: PublicAnalysisRequest) -> ControlledErrorPayload | None:
        if not request.codigo_req.strip():
            return ControlledErrorPayload(
                error_code=IntegrationApiErrorCode.INCOMPLETE_REQUEST,
                message="codigo_req es obligatorio",
                recoverable=True,
            )
        if not request.project_id.strip():
            return ControlledErrorPayload(
                error_code=IntegrationApiErrorCode.INCOMPLETE_REQUEST,
                message="project_id es obligatorio",
                recoverable=True,
            )
        if not request.documents:
            return ControlledErrorPayload(
                error_code=IntegrationApiErrorCode.INCOMPLETE_REQUEST,
                message="Se requiere al menos un documento del Centro de Evidencias",
                recoverable=True,
            )
        for document in request.documents:
            if not document.document_id.strip():
                return ControlledErrorPayload(
                    error_code=IntegrationApiErrorCode.INVALID_DOCUMENT,
                    message="document_id inválido",
                    recoverable=True,
                )
        return None

    def _record_event(
        self,
        analysis_id: UUID,
        operation: IntegrationApiOperation,
        stage: IntegrationApiLifecycleStage,
        *,
        success: bool,
    ) -> None:
        record = {
            "analysis_id": str(analysis_id),
            "operation": operation.value,
            "stage": stage.value,
            "success": success,
        }
        self._events.append(record)
        self._event_manager.create_and_register(
            process_id=analysis_id,
            module=self.MODULE_NAME,
            event_type=EventType.SYSTEM,
            message=f"{operation.value}:{stage.value}",
            metadata=record,
        )
