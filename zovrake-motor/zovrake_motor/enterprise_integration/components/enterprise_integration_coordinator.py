"""Coordinator de Integración Empresarial — enrutamiento hacia el PIO."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.api_gateway_internal import ApiGatewayInternal
from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.components.pipeline_integration_orchestrator import (
    PipelineIntegrationOrchestratorComponent,
)
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
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiErrorCode
from zovrake_motor.enterprise_integration.registry import ComponentRegistry

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class EnterpriseIntegrationCoordinator(EnterpriseIntegrationComponentPort):
    """
    Coordinator único de la comunicación ERP ↔ Motor Inteligente.

    Toda solicitud se enruta exclusivamente al Pipeline Integration Orchestrator.
    """

    def __init__(
        self,
        registry: ComponentRegistry,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
    ) -> None:
        self._registry = registry
        self._integration = integration
        self._initialized = False

    @property
    def component_name(self) -> str:
        return "enterprise_integration_coordinator"

    @property
    def component_label(self) -> str:
        return "Enterprise Integration Coordinator"

    @property
    def internal_api_gateway(self) -> ApiGatewayInternal | None:
        component = self._registry.get("api_gateway_internal")
        if isinstance(component, ApiGatewayInternal):
            return component
        return None

    @property
    def pipeline_orchestrator(self) -> PipelineIntegrationOrchestratorComponent | None:
        component = self._registry.get("pipeline_integration_orchestrator")
        if isinstance(component, PipelineIntegrationOrchestratorComponent):
            return component
        return None

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        gateway = self.internal_api_gateway
        pio = self.pipeline_orchestrator
        return (
            self._initialized
            and self._registry.count() > 0
            and gateway is not None
            and gateway.is_ready()
            and pio is not None
            and pio.is_ready()
        )

    def _require_pio_and_api(self, process_id):
        pio_component = self.pipeline_orchestrator
        gateway = self.internal_api_gateway
        if pio_component is None or not pio_component.is_ready():
            return None, InternalApiErrorResponse(
                error_code=InternalApiErrorCode.PIO_ORCHESTRATION_REQUIRED,
                message="Pipeline Integration Orchestrator requerido",
                process_id=process_id,
            )
        if gateway is None or gateway.internal_api is None:
            return None, InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="API Interna no disponible",
                process_id=process_id,
            )
        return (pio_component.orchestrator, gateway.internal_api), None

    def dispatch_start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        resources, error = self._require_pio_and_api(request.process_id)
        if error is not None:
            return error
        orchestrator, internal_api = resources
        return orchestrator.orchestrate_start_analysis(request, internal_api)

    def dispatch_query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        resources, error = self._require_pio_and_api(request.process_id)
        if error is not None:
            return error
        orchestrator, internal_api = resources
        return orchestrator.orchestrate_query_status(request, internal_api)

    def dispatch_query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        resources, error = self._require_pio_and_api(request.process_id)
        if error is not None:
            return error
        orchestrator, internal_api = resources
        return orchestrator.orchestrate_query_result(request, internal_api)

    def dispatch_cancel_analysis(
        self,
        request: CancelAnalysisRequest,
    ) -> CancelAnalysisResponse | InternalApiErrorResponse:
        resources, error = self._require_pio_and_api(request.process_id)
        if error is not None:
            return error
        orchestrator, internal_api = resources
        return orchestrator.orchestrate_cancel_analysis(request, internal_api)

    def dispatch_validate_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        resources, error = self._require_pio_and_api(request.process_id)
        if error is not None:
            return error
        orchestrator, internal_api = resources
        return orchestrator.orchestrate_validate_request(request, internal_api)

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["components"] = self._registry.snapshot()
        base["components_count"] = self._registry.count()
        base["components_ready"] = self._registry.ready_count()
        base["internal_api_ready"] = (
            self.internal_api_gateway.is_ready()
            if self.internal_api_gateway is not None
            else False
        )
        base["pio_ready"] = (
            self.pipeline_orchestrator.is_ready()
            if self.pipeline_orchestrator is not None
            else False
        )
        gateway = self.internal_api_gateway
        base["internal_api"] = (
            gateway.internal_api.snapshot()
            if gateway is not None and gateway.internal_api is not None
            else None
        )
        pio = self.pipeline_orchestrator
        base["pipeline_orchestrator"] = pio.snapshot() if pio is not None else None
        return base
