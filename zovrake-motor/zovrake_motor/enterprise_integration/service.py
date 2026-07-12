"""Servicio del Módulo de Integración Empresarial."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.enterprise_integration.components.erp_communication_gateway import (
    ErpCommunicationGatewayComponent,
)
from zovrake_motor.enterprise_integration.components.async_processing_queue_manager import (
    AsyncProcessingQueueManagerComponent,
)
from zovrake_motor.enterprise_integration.apqm.execution_adapter import (
    EnterpriseIntegrationApqmExecutor,
)
from zovrake_motor.enterprise_integration.components.fault_tolerance_retry_recovery_framework import (
    FaultToleranceRetryRecoveryFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.security_validation_audit_framework import (
    SecurityValidationAuditFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.observability_metrics_monitoring_framework import (
    ObservabilityMetricsMonitoringFrameworkComponent,
)
from zovrake_motor.enterprise_integration.components.performance_optimization_scalability_framework import (
    PerformanceOptimizationScalabilityFrameworkComponent,
)
from zovrake_motor.enterprise_integration.ommf.source_adapter import EnterpriseIntegrationOmmfSourceAdapter
from zovrake_motor.enterprise_integration.posf.ommf_adapter import EnterpriseIntegrationPosfOmmfAdapter
from zovrake_motor.enterprise_integration.svaf.fault_notification_adapter import (
    EnterpriseIntegrationSvafFaultNotifier,
)
from zovrake_motor.enterprise_integration.ftrrf.continuity_adapter import (
    EnterpriseIntegrationFtrrfContinuityAdapter,
)
from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.ecg.dispatcher_adapter import (
    EnterpriseIntegrationEcgDispatcher,
)
from zovrake_motor.enterprise_integration.components.pipeline_integration_orchestrator import (
    PipelineIntegrationOrchestratorComponent,
)
from zovrake_motor.enterprise_integration.components.enterprise_integration_coordinator import (
    EnterpriseIntegrationCoordinator,
)
from zovrake_motor.enterprise_integration.input_gateway import IntelligentAnalysisOutputGateway
from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
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
from zovrake_motor.enterprise_integration.models import (
    EnterpriseIntegrationRequest,
    EnterpriseIntegrationResult,
)
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiErrorCode
from zovrake_motor.enterprise_integration.pipeline import EnterpriseIntegrationPipeline
from zovrake_motor.enterprise_integration.port import EnterpriseIntegrationPort
from zovrake_motor.enterprise_integration.registry import ComponentRegistry
from zovrake_motor.events.manager import EventManager
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class EnterpriseIntegrationService(
    ConfigurationAccessible,
    ModulePort,
    EnterpriseIntegrationPort,
):
    """
    Módulo de Integración Empresarial entre ERP y Motor Inteligente.

    Responsabilidad única: coordinar la comunicación entre ambos sistemas sin
    incorporar lógica de negocio ni lógica de inteligencia artificial.
    """

    MODULE_NAME = "enterprise_integration"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        component_registry: ComponentRegistry | None = None,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        intelligent_analysis_gateway: IntelligentAnalysisOutputGateway | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._integration = integration or EnterpriseIntegrationMotorIntegration(
            config_provider=config_provider,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        self._registry = component_registry or ComponentRegistry()
        self._enterprise_integration_coordinator: EnterpriseIntegrationCoordinator | None = None
        self._intelligent_analysis_gateway = intelligent_analysis_gateway
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    @property
    def component_registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def enterprise_integration_coordinator(self) -> EnterpriseIntegrationCoordinator | None:
        return self._enterprise_integration_coordinator

    @property
    def intelligent_analysis_gateway(self) -> IntelligentAnalysisOutputGateway:
        if self._intelligent_analysis_gateway is None:
            self._intelligent_analysis_gateway = IntelligentAnalysisOutputGateway(
                settings=self._integration.enterprise_integration_settings(),
            )
        return self._intelligent_analysis_gateway

    @property
    def integration(self) -> EnterpriseIntegrationMotorIntegration:
        return self._integration

    @property
    def state_manager(self) -> StateManager:
        return self._integration.state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._integration.event_manager

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._enterprise_integration_coordinator = self._registry.register_defaults(
            integration=self._integration,
        )
        for component in self._registry.all_components():
            component.initialize()
        dispatcher = EnterpriseIntegrationEcgDispatcher(self)
        executor = EnterpriseIntegrationApqmExecutor(self)
        ecg_component = self._registry.get("erp_communication_gateway")
        apqm_component = self._registry.get("async_processing_queue_manager")
        ftrrf_component = self._registry.get("fault_tolerance_retry_recovery_framework")
        svaf_component = self._registry.get("security_validation_audit_framework")
        ommf_component = self._registry.get("observability_metrics_monitoring_framework")
        posf_component = self._registry.get("performance_optimization_scalability_framework")
        pio_component = self._registry.get("pipeline_integration_orchestrator")
        if isinstance(ecg_component, ErpCommunicationGatewayComponent):
            ecg_component.gateway.bind_dispatch(dispatcher)
        if isinstance(apqm_component, AsyncProcessingQueueManagerComponent):
            apqm_component.manager.bind_execution(executor)
            if isinstance(ecg_component, ErpCommunicationGatewayComponent):
                ecg_component.gateway.bind_enqueue(apqm_component.manager)
        if isinstance(ftrrf_component, FaultToleranceRetryRecoveryFrameworkComponent):
            ftrrf_component.framework.bind_continuity(
                EnterpriseIntegrationFtrrfContinuityAdapter(self),
            )
            if isinstance(apqm_component, AsyncProcessingQueueManagerComponent):
                apqm_component.manager.bind_fault_handler(ftrrf_component.framework)
        if isinstance(svaf_component, SecurityValidationAuditFrameworkComponent):
            if isinstance(ftrrf_component, FaultToleranceRetryRecoveryFrameworkComponent):
                svaf_component.framework.bind_fault_notifier(
                    EnterpriseIntegrationSvafFaultNotifier(ftrrf_component.framework),
                )
            if isinstance(ecg_component, ErpCommunicationGatewayComponent):
                ecg_component.gateway.bind_security(svaf_component.framework)
            if isinstance(pio_component, PipelineIntegrationOrchestratorComponent):
                pio_component.orchestrator.bind_validation_gate(svaf_component.framework)
        if isinstance(ommf_component, ObservabilityMetricsMonitoringFrameworkComponent):
            ommf = ommf_component.framework
            ommf.bind_source(EnterpriseIntegrationOmmfSourceAdapter(self))
            if isinstance(pio_component, PipelineIntegrationOrchestratorComponent):
                pio_component.orchestrator.bind_observability(ommf)
            if isinstance(apqm_component, AsyncProcessingQueueManagerComponent):
                apqm_component.manager.bind_observability(ommf)
            if isinstance(ftrrf_component, FaultToleranceRetryRecoveryFrameworkComponent):
                ftrrf_component.framework.bind_observability(ommf)
            if isinstance(svaf_component, SecurityValidationAuditFrameworkComponent):
                svaf_component.framework.bind_observability(ommf)
        if isinstance(posf_component, PerformanceOptimizationScalabilityFrameworkComponent):
            posf = posf_component.framework
            if isinstance(ommf_component, ObservabilityMetricsMonitoringFrameworkComponent):
                posf.bind_metrics_source(EnterpriseIntegrationPosfOmmfAdapter(ommf_component.framework))
            if isinstance(pio_component, PipelineIntegrationOrchestratorComponent):
                pio_component.orchestrator.bind_performance_optimizer(posf)
            if isinstance(apqm_component, AsyncProcessingQueueManagerComponent):
                apqm_component.manager.bind_performance_optimizer(posf)
        self._intelligent_analysis_gateway = IntelligentAnalysisOutputGateway(
            settings=self._integration.enterprise_integration_settings(),
        )
        self._initialized = True

    def prepare(self, request: EnterpriseIntegrationRequest) -> EnterpriseIntegrationResult:
        settings = self._integration.enterprise_integration_settings()
        gateway = self.intelligent_analysis_gateway
        input_bundle = request.input_bundle()
        consumption = gateway.prepare_consumption(input_bundle)
        coordinator = self._enterprise_integration_coordinator

        return EnterpriseIntegrationResult(
            process_id=request.process_id,
            prepared=True,
            message="Arquitectura de Integración Empresarial preparada — sin procesamiento",
            components_ready=self._registry.ready_count(),
            metadata={
                "codigo_req": request.codigo_req,
                "enabled": settings.enabled,
                "components_count": self._registry.count(),
                "intelligent_analysis_consumption": consumption,
                "pm8_input_contract_required": settings.pm8_input_contract_required,
                "internal_api_ready": coordinator.is_ready() if coordinator else False,
                "internal_integration_api_prepared": settings.internal_integration_api.prepared,
                "pipeline_orchestrator_ready": coordinator.is_ready() if coordinator else False,
                "erp_communication_gateway_ready": self._ecg_ready(),
                "async_processing_queue_manager_ready": self._apqm_ready(),
                "fault_tolerance_retry_recovery_framework_ready": self._ftrrf_ready(),
                "security_validation_audit_framework_ready": self._svaf_ready(),
                "observability_metrics_monitoring_framework_ready": self._ommf_ready(),
                "performance_optimization_scalability_framework_ready": self._posf_ready(),
                "enterprise_integration_pipeline": EnterpriseIntegrationPipeline.build_snapshot(
                    self._registry,
                ),
            },
        )

    def start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="Integration Coordinator no inicializado",
                process_id=request.process_id,
            )
        return coordinator.dispatch_start_analysis(request)

    def query_analysis_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="Integration Coordinator no inicializado",
                process_id=request.process_id,
            )
        return coordinator.dispatch_query_status(request)

    def query_analysis_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="Integration Coordinator no inicializado",
                process_id=request.process_id,
            )
        return coordinator.dispatch_query_result(request)

    def cancel_analysis(
        self,
        request: CancelAnalysisRequest,
    ) -> CancelAnalysisResponse | InternalApiErrorResponse:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="Integration Coordinator no inicializado",
                process_id=request.process_id,
            )
        return coordinator.dispatch_cancel_analysis(request)

    def validate_analysis_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.COORDINATOR_REQUIRED,
                message="Integration Coordinator no inicializado",
                process_id=request.process_id,
            )
        return coordinator.dispatch_validate_request(request)

    @property
    def erp_communication_gateway(self) -> ErpCommunicationGatewayComponent | None:
        component = self._registry.get("erp_communication_gateway")
        if isinstance(component, ErpCommunicationGatewayComponent):
            return component
        return None

    def _ecg_ready(self) -> bool:
        ecg = self.erp_communication_gateway
        return ecg is not None and ecg.is_ready()

    def _apqm_ready(self) -> bool:
        apqm = self.async_processing_queue_manager
        return apqm is not None and apqm.is_ready()

    def _ftrrf_ready(self) -> bool:
        ftrrf = self.fault_tolerance_retry_recovery_framework
        return ftrrf is not None and ftrrf.is_ready()

    def _svaf_ready(self) -> bool:
        svaf = self.security_validation_audit_framework
        return svaf is not None and svaf.is_ready()

    def _ommf_ready(self) -> bool:
        ommf = self.observability_metrics_monitoring_framework
        return ommf is not None and ommf.is_ready()

    def _posf_ready(self) -> bool:
        posf = self.performance_optimization_scalability_framework
        return posf is not None and posf.is_ready()

    @property
    def async_processing_queue_manager(self) -> AsyncProcessingQueueManagerComponent | None:
        component = self._registry.get("async_processing_queue_manager")
        if isinstance(component, AsyncProcessingQueueManagerComponent):
            return component
        return None

    @property
    def fault_tolerance_retry_recovery_framework(
        self,
    ) -> FaultToleranceRetryRecoveryFrameworkComponent | None:
        component = self._registry.get("fault_tolerance_retry_recovery_framework")
        if isinstance(component, FaultToleranceRetryRecoveryFrameworkComponent):
            return component
        return None

    def get_fault_tolerance_snapshot(self) -> dict[str, Any] | None:
        ftrrf = self.fault_tolerance_retry_recovery_framework
        if ftrrf is None:
            return None
        return ftrrf.snapshot()

    @property
    def security_validation_audit_framework(
        self,
    ) -> SecurityValidationAuditFrameworkComponent | None:
        component = self._registry.get("security_validation_audit_framework")
        if isinstance(component, SecurityValidationAuditFrameworkComponent):
            return component
        return None

    def get_security_validation_audit_snapshot(self) -> dict[str, Any] | None:
        svaf = self.security_validation_audit_framework
        if svaf is None:
            return None
        return svaf.snapshot()

    @property
    def observability_metrics_monitoring_framework(
        self,
    ) -> ObservabilityMetricsMonitoringFrameworkComponent | None:
        component = self._registry.get("observability_metrics_monitoring_framework")
        if isinstance(component, ObservabilityMetricsMonitoringFrameworkComponent):
            return component
        return None

    def get_observability_metrics_monitoring_snapshot(self) -> dict[str, Any] | None:
        ommf = self.observability_metrics_monitoring_framework
        if ommf is None:
            return None
        return ommf.snapshot()

    @property
    def performance_optimization_scalability_framework(
        self,
    ) -> PerformanceOptimizationScalabilityFrameworkComponent | None:
        component = self._registry.get("performance_optimization_scalability_framework")
        if isinstance(component, PerformanceOptimizationScalabilityFrameworkComponent):
            return component
        return None

    def get_performance_optimization_scalability_snapshot(self) -> dict[str, Any] | None:
        posf = self.performance_optimization_scalability_framework
        if posf is None:
            return None
        return posf.snapshot()

    def process_async_queue_pending(self) -> int:
        """Procesa solicitudes pendientes en la cola lógica — no bloqueante para el ERP."""
        apqm = self.async_processing_queue_manager
        if apqm is None or not apqm.is_ready():
            return 0
        return apqm.manager.process_all_pending()

    def get_async_processing_queue_snapshot(self) -> dict[str, Any] | None:
        apqm = self.async_processing_queue_manager
        if apqm is None:
            return None
        return apqm.snapshot()

    def submit_evidence_center_analysis(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> ErpAnalysisDelivery:
        """Punto de entrada oficial ERP (Centro de Evidencias) → Motor vía ECG."""
        ecg = self.erp_communication_gateway
        if ecg is None or not ecg.is_ready():
            raise RuntimeError("ERP Communication Gateway no disponible")
        return ecg.gateway.submit_analysis_request(request)

    def query_evidence_center_status(
        self,
        request: EvidenceCenterStatusQuery,
    ) -> ErpAnalysisDelivery:
        ecg = self.erp_communication_gateway
        if ecg is None or not ecg.is_ready():
            raise RuntimeError("ERP Communication Gateway no disponible")
        return ecg.gateway.query_analysis_status(request)

    def query_evidence_center_result(
        self,
        request: EvidenceCenterResultQuery,
    ) -> ErpAnalysisDelivery:
        ecg = self.erp_communication_gateway
        if ecg is None or not ecg.is_ready():
            raise RuntimeError("ERP Communication Gateway no disponible")
        return ecg.gateway.query_analysis_result(request)

    def get_erp_communication_gateway_snapshot(self) -> dict[str, Any] | None:
        ecg = self.erp_communication_gateway
        if ecg is None:
            return None
        return ecg.snapshot()

    def get_internal_api_snapshot(self) -> dict[str, Any] | None:
        coordinator = self._enterprise_integration_coordinator
        if coordinator is None:
            return None
        gateway = coordinator.internal_api_gateway
        if gateway is None or gateway.internal_api is None:
            return None
        return gateway.internal_api.snapshot()

    def get_pipeline_orchestrator_snapshot(self) -> dict[str, Any] | None:
        component = self._registry.get("pipeline_integration_orchestrator")
        if component is None or not hasattr(component, "snapshot"):
            return None
        return component.snapshot()

    def get_pipeline_context(self, process_id):
        component = self._registry.get("pipeline_integration_orchestrator")
        if component is None or not hasattr(component, "orchestrator"):
            return None
        return component.orchestrator.get_pipeline_context(process_id)

    def get_contract_catalog(self) -> dict[str, Any] | None:
        component = self._registry.get("communication_contracts")
        if component is None or not hasattr(component, "contract_catalog"):
            return None
        return component.contract_catalog()

    def get_enterprise_integration_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return EnterpriseIntegrationPipeline.build_snapshot(self._registry)

    def snapshot(self) -> dict[str, Any]:
        return {
            "module_name": self.MODULE_NAME,
            "initialized": self._initialized,
            "integration": self._integration.snapshot(),
            "intelligent_analysis_gateway": self.intelligent_analysis_gateway.snapshot(),
            "components": self._registry.snapshot(),
            "enterprise_integration_coordinator": (
                self._enterprise_integration_coordinator.snapshot()
                if self._enterprise_integration_coordinator is not None
                else None
            ),
            "enterprise_integration_pipeline": self.get_enterprise_integration_pipeline_snapshot(),
            "internal_api": self.get_internal_api_snapshot(),
            "pipeline_orchestrator": self.get_pipeline_orchestrator_snapshot(),
            "erp_communication_gateway": self.get_erp_communication_gateway_snapshot(),
            "async_processing_queue_manager": self.get_async_processing_queue_snapshot(),
            "fault_tolerance_retry_recovery_framework": self.get_fault_tolerance_snapshot(),
            "security_validation_audit_framework": self.get_security_validation_audit_snapshot(),
            "observability_metrics_monitoring_framework": (
                self.get_observability_metrics_monitoring_snapshot()
            ),
            "performance_optimization_scalability_framework": (
                self.get_performance_optimization_scalability_snapshot()
            ),
            "contract_catalog": self.get_contract_catalog(),
        }
