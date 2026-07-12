"""Pipeline Integration Orchestrator — orquestación central ERP ↔ Motor."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID

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
from zovrake_motor.enterprise_integration.pio.enums import (
    IntegrationPipelinePhase,
    PipelineOrchestrationOperation,
)
from zovrake_motor.enterprise_integration.pio.events import PipelineEventRecorder
from zovrake_motor.enterprise_integration.pio.lifecycle import IntegrationPipelineLifecycle
from zovrake_motor.enterprise_integration.pio.models import (
    PipelineExecutionContext,
    PipelineOrchestrationResult,
    PipelineTransitionRecord,
    utc_now,
)
from zovrake_motor.enterprise_integration.pio.motor_gateway import MotorUnitGateway
from zovrake_motor.enterprise_integration.pio.traceability import PipelineTraceabilityStore
from zovrake_motor.states.exceptions import StateManagementError

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
    from zovrake_motor.enterprise_integration.internal_api.api import InternalIntegrationApi
    from zovrake_motor.enterprise_integration.ommf.ports import IntegrationObservabilityPort
    from zovrake_motor.enterprise_integration.posf.ports import IntegrationPerformancePort
    from zovrake_motor.enterprise_integration.svaf.ports import PipelineValidationGatePort


class PipelineIntegrationOrchestrator:
    """
    Orquestador central del Pipeline de Integración.

    Responsabilidad única: coordinar el ciclo completo de solicitudes
    sin lógica de negocio, IA ni ejecución interna del Motor.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        traceability: PipelineTraceabilityStore | None = None,
        motor_gateway: MotorUnitGateway | None = None,
    ) -> None:
        self._integration = integration
        self._traceability = traceability or PipelineTraceabilityStore()
        self._motor_gateway = motor_gateway or MotorUnitGateway()
        self._event_recorder = PipelineEventRecorder(integration)
        self._validation_gate: PipelineValidationGatePort | None = None
        self._observability: IntegrationObservabilityPort | None = None
        self._performance_optimizer: IntegrationPerformancePort | None = None
        self._initialized = False

    def bind_validation_gate(self, gate: PipelineValidationGatePort) -> None:
        self._validation_gate = gate

    def bind_observability(self, observability: IntegrationObservabilityPort) -> None:
        self._observability = observability

    def bind_performance_optimizer(self, optimizer: IntegrationPerformancePort) -> None:
        self._performance_optimizer = optimizer

    @property
    def traceability(self) -> PipelineTraceabilityStore:
        return self._traceability

    @property
    def motor_gateway(self) -> MotorUnitGateway:
        return self._motor_gateway

    def initialize(self) -> None:
        self._motor_gateway.initialize()
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized and self._motor_gateway.is_prepared

    def _settings(self):
        return self._integration.enterprise_integration_settings().pipeline_integration_orchestrator

    def _create_context(
        self,
        *,
        process_id: UUID,
        operation: PipelineOrchestrationOperation,
        codigo_req: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PipelineExecutionContext:
        meta = dict(metadata or {})
        return PipelineExecutionContext(
            process_id=process_id,
            operation=operation.value,
            project_id=str(meta.get("project_id", "")),
            analysis_id=str(meta.get("analysis_id", "")),
            codigo_req=codigo_req,
            metadata=meta,
        )

    def _advance_phase(
        self,
        context: PipelineExecutionContext,
        operation: PipelineOrchestrationOperation,
        to_phase: IntegrationPipelinePhase,
        *,
        reason: str = "",
    ) -> None:
        if not IntegrationPipelineLifecycle.is_valid_transition(
            operation,
            context.current_phase,
            to_phase,
        ):
            raise ValueError(
                f"Transición no permitida: {context.current_phase} -> {to_phase.value}",
            )

        transition = PipelineTransitionRecord(
            from_phase=context.current_phase,
            to_phase=to_phase,
            reason=reason,
        )
        context.transitions.append(transition)
        context.current_phase = to_phase
        context.updated_at = utc_now()

        motor_state = IntegrationPipelineLifecycle.motor_state_for_phase(to_phase)
        if motor_state is not None:
            self._sync_motor_state(context, motor_state, reason)

        self._event_recorder.record_phase_transition(
            context.process_id,
            phase=to_phase,
            operation=operation.value,
            reason=reason,
        )
        if self._observability is not None:
            self._observability.record_pipeline_transition(
                process_id=context.process_id,
                project_id=context.project_id,
                quotation_id=str(context.metadata.get("quotation_id", "")),
                component="PipelineIntegrationOrchestrator",
                pipeline_phase=to_phase.value,
                operation=operation.value,
                duration_ms=0.0,
            )
        if self._performance_optimizer is not None:
            self._performance_optimizer.record_pipeline_transition(
                process_id=context.process_id,
                phase=to_phase.value,
                operation=operation.value,
                transition_count=len(context.transitions),
                project_id=context.project_id,
                quotation_id=str(context.metadata.get("quotation_id", "")),
            )

    def _sync_motor_state(
        self,
        context: PipelineExecutionContext,
        motor_state,
        reason: str,
    ) -> None:
        state_manager = self._integration.state_manager
        record = state_manager.get_process(context.process_id)
        if record is None:
            try:
                state_manager.create_process(
                    context.process_id,
                    context.codigo_req,
                    metadata={
                        "project_id": context.project_id,
                        "analysis_id": context.analysis_id,
                    },
                    initial_state=motor_state,
                )
                return
            except StateManagementError:
                record = state_manager.get_process(context.process_id)

        if record is not None and record.current_state != motor_state:
            state_manager.update_state(context.process_id, motor_state, reason)

    def _run_phases(
        self,
        context: PipelineExecutionContext,
        operation: PipelineOrchestrationOperation,
        *,
        phase_handler,
    ) -> PipelineOrchestrationResult | InternalApiErrorResponse:
        phases_completed: list[IntegrationPipelinePhase] = []
        flow = IntegrationPipelineLifecycle.flow_for(operation)

        for phase in flow:
            try:
                self._advance_phase(context, operation, phase, reason=f"Avance {operation.value}")
            except ValueError as exc:
                self._advance_phase(
                    context,
                    operation,
                    IntegrationPipelinePhase.ERROR_CONTROLADO,
                    reason=str(exc),
                )
                self._traceability.save(context)
                return InternalApiErrorResponse(
                    error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                    message=str(exc),
                    process_id=context.process_id,
                    details={"pipeline_context": context.to_dict()},
                )

            phases_completed.append(phase)
            handler_result = phase_handler(context, phase)
            if isinstance(handler_result, InternalApiErrorResponse):
                self._advance_phase(
                    context,
                    operation,
                    IntegrationPipelinePhase.ERROR_CONTROLADO,
                    reason=handler_result.message,
                )
                self._traceability.save(context)
                return handler_result

        self._traceability.save(context)
        self._event_recorder.record_orchestration_completed(
            context.process_id,
            operation=operation.value,
            success=True,
        )
        return PipelineOrchestrationResult(
            context=context,
            success=True,
            message=f"Pipeline {operation.value} completado — sin ejecución interna",
            phases_completed=tuple(phases_completed),
            executed=False,
        )

    def orchestrate_start_analysis(
        self,
        request: StartAnalysisRequest,
        internal_api: InternalIntegrationApi,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
                message="PIO no inicializado",
                process_id=request.process_id,
            )

        gate = self._validation_gate
        if gate is not None:
            internal_check = gate.validate_internal_request(request)
            if not internal_check.approved:
                return InternalApiErrorResponse(
                    error_code=InternalApiErrorCode.STRUCTURAL_VALIDATION_FAILED,
                    message="Validación SVAF fallida — Pipeline bloqueado",
                    process_id=request.process_id,
                    details={
                        "validation_errors": [
                            issue.message for issue in internal_check.validation.issues
                        ],
                    },
                )
            authorization = gate.authorize_pipeline_entry(
                process_id=request.process_id,
                operation=PipelineOrchestrationOperation.START_ANALYSIS.value,
                metadata=request.metadata,
            )
            if not authorization.approved:
                return InternalApiErrorResponse(
                    error_code=InternalApiErrorCode.STRUCTURAL_VALIDATION_FAILED,
                    message="Autorización SVAF denegada — Pipeline bloqueado",
                    process_id=request.process_id,
                    details={
                        "validation_errors": [
                            issue.message for issue in authorization.validation.issues
                        ],
                    },
                )

        context = self._create_context(
            process_id=request.process_id,
            operation=PipelineOrchestrationOperation.START_ANALYSIS,
            codigo_req=request.codigo_req,
            metadata=request.metadata,
        )
        api_response: StartAnalysisResponse | InternalApiErrorResponse | None = None

        def handler(ctx: PipelineExecutionContext, phase: IntegrationPipelinePhase):
            nonlocal api_response
            if phase == IntegrationPipelinePhase.VALIDACION_INICIADA:
                validation = internal_api.validate_request(
                    ValidateAnalysisRequest(
                        process_id=request.process_id,
                        codigo_req=request.codigo_req,
                        contract_version=request.contract_version,
                        payload={
                            "codigo_req": request.codigo_req,
                            "document_ids": list(request.document_ids),
                        },
                    ),
                )
                if isinstance(validation, InternalApiErrorResponse):
                    return validation
                if not validation.valid:
                    return InternalApiErrorResponse(
                        error_code=InternalApiErrorCode.STRUCTURAL_VALIDATION_FAILED,
                        message="Validación estructural fallida en PIO",
                        process_id=request.process_id,
                        details={"validation_errors": list(validation.validation_errors)},
                    )
            if phase == IntegrationPipelinePhase.INVOCACION_MOTOR_PREPARADA:
                invocation = self._motor_gateway.invoke_prepared(
                    process_id=request.process_id,
                    codigo_req=request.codigo_req,
                    operation=PipelineOrchestrationOperation.START_ANALYSIS.value,
                )
                ctx.motor_invocation_prepared = invocation["prepared"]
                ctx.motor_executed = invocation["invoked"]
            if phase == IntegrationPipelinePhase.RESULTADO_GENERADO:
                api_response = internal_api.start_analysis(request)
                return api_response
            return None

        pipeline_result = self._run_phases(
            context,
            PipelineOrchestrationOperation.START_ANALYSIS,
            phase_handler=handler,
        )
        if isinstance(pipeline_result, InternalApiErrorResponse):
            return pipeline_result
        if isinstance(api_response, InternalApiErrorResponse):
            return api_response
        if api_response is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                message="Respuesta de API Interna no generada",
                process_id=request.process_id,
            )

        return StartAnalysisResponse(
            process_id=api_response.process_id,
            success=api_response.success,
            message=api_response.message,
            contract_version=api_response.contract_version,
            processing_status=api_response.processing_status,
            executed=False,
            metadata={
                **api_response.metadata,
                "pipeline_orchestration": pipeline_result.to_dict(),
            },
        )

    def orchestrate_query_status(
        self,
        request: AnalysisStatusQueryRequest,
        internal_api: InternalIntegrationApi,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
                message="PIO no inicializado",
                process_id=request.process_id,
            )

        context = self._create_context(
            process_id=request.process_id,
            operation=PipelineOrchestrationOperation.QUERY_STATUS,
            codigo_req=request.codigo_req,
            metadata=request.metadata,
        )
        api_response: AnalysisStatusResponse | InternalApiErrorResponse | None = None

        def handler(_ctx: PipelineExecutionContext, phase: IntegrationPipelinePhase):
            nonlocal api_response
            if phase == IntegrationPipelinePhase.RESULTADO_ENTREGADO:
                api_response = internal_api.query_status(request)
                return api_response
            return None

        pipeline_result = self._run_phases(
            context,
            PipelineOrchestrationOperation.QUERY_STATUS,
            phase_handler=handler,
        )
        if isinstance(pipeline_result, InternalApiErrorResponse):
            return pipeline_result
        if isinstance(api_response, InternalApiErrorResponse):
            return api_response
        if api_response is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                message="Consulta de estado no completada",
                process_id=request.process_id,
            )

        return AnalysisStatusResponse(
            process_id=api_response.process_id,
            success=api_response.success,
            message=api_response.message,
            contract_version=api_response.contract_version,
            processing_status=api_response.processing_status,
            motor_state=api_response.motor_state,
            executed=False,
            metadata={
                **api_response.metadata,
                "pipeline_orchestration": pipeline_result.to_dict(),
            },
        )

    def orchestrate_query_result(
        self,
        request: AnalysisResultQueryRequest,
        internal_api: InternalIntegrationApi,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
                message="PIO no inicializado",
                process_id=request.process_id,
            )

        context = self._create_context(
            process_id=request.process_id,
            operation=PipelineOrchestrationOperation.QUERY_RESULT,
            codigo_req=request.codigo_req,
            metadata=request.metadata,
        )
        api_response: AnalysisResultResponse | InternalApiErrorResponse | None = None

        def handler(_ctx: PipelineExecutionContext, phase: IntegrationPipelinePhase):
            nonlocal api_response
            if phase == IntegrationPipelinePhase.RESULTADO_GENERADO:
                api_response = internal_api.query_result(request)
                return api_response
            return None

        pipeline_result = self._run_phases(
            context,
            PipelineOrchestrationOperation.QUERY_RESULT,
            phase_handler=handler,
        )
        if isinstance(pipeline_result, InternalApiErrorResponse):
            return pipeline_result
        if isinstance(api_response, InternalApiErrorResponse):
            return api_response
        if api_response is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                message="Consulta de resultado no completada",
                process_id=request.process_id,
            )

        return AnalysisResultResponse(
            process_id=api_response.process_id,
            success=api_response.success,
            message=api_response.message,
            contract_version=api_response.contract_version,
            processing_status=api_response.processing_status,
            result=api_response.result,
            executed=False,
            metadata={
                **api_response.metadata,
                "pipeline_orchestration": pipeline_result.to_dict(),
            },
        )

    def orchestrate_cancel_analysis(
        self,
        request: CancelAnalysisRequest,
        internal_api: InternalIntegrationApi,
    ) -> CancelAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
                message="PIO no inicializado",
                process_id=request.process_id,
            )

        context = self._create_context(
            process_id=request.process_id,
            operation=PipelineOrchestrationOperation.CANCEL_ANALYSIS,
            codigo_req=request.codigo_req,
            metadata=request.metadata,
        )
        api_response: CancelAnalysisResponse | InternalApiErrorResponse | None = None

        def handler(_ctx: PipelineExecutionContext, phase: IntegrationPipelinePhase):
            nonlocal api_response
            if phase == IntegrationPipelinePhase.ERROR_CONTROLADO:
                api_response = internal_api.cancel_analysis(request)
                return api_response
            return None

        pipeline_result = self._run_phases(
            context,
            PipelineOrchestrationOperation.CANCEL_ANALYSIS,
            phase_handler=handler,
        )
        if isinstance(pipeline_result, InternalApiErrorResponse):
            return pipeline_result
        if isinstance(api_response, InternalApiErrorResponse):
            return api_response
        if api_response is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                message="Cancelación no completada",
                process_id=request.process_id,
            )

        return CancelAnalysisResponse(
            process_id=api_response.process_id,
            success=api_response.success,
            message=api_response.message,
            contract_version=api_response.contract_version,
            processing_status=api_response.processing_status,
            executed=False,
            metadata={
                **api_response.metadata,
                "pipeline_orchestration": pipeline_result.to_dict(),
            },
        )

    def orchestrate_validate_request(
        self,
        request: ValidateAnalysisRequest,
        internal_api: InternalIntegrationApi,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
                message="PIO no inicializado",
                process_id=request.process_id,
            )

        context = self._create_context(
            process_id=request.process_id,
            operation=PipelineOrchestrationOperation.VALIDATE_REQUEST,
            codigo_req=request.codigo_req,
            metadata=request.metadata,
        )
        api_response: ValidateAnalysisResponse | InternalApiErrorResponse | None = None

        def handler(_ctx: PipelineExecutionContext, phase: IntegrationPipelinePhase):
            nonlocal api_response
            if phase == IntegrationPipelinePhase.VALIDACION_INICIADA:
                api_response = internal_api.validate_request(request)
                return api_response
            return None

        pipeline_result = self._run_phases(
            context,
            PipelineOrchestrationOperation.VALIDATE_REQUEST,
            phase_handler=handler,
        )
        if isinstance(pipeline_result, InternalApiErrorResponse):
            return pipeline_result
        if isinstance(api_response, InternalApiErrorResponse):
            return api_response
        if api_response is None:
            return InternalApiErrorResponse(
                error_code=InternalApiErrorCode.OPERATION_NOT_EXECUTED,
                message="Validación no completada",
                process_id=request.process_id,
            )

        return ValidateAnalysisResponse(
            process_id=api_response.process_id,
            success=api_response.success,
            message=api_response.message,
            contract_version=api_response.contract_version,
            valid=api_response.valid,
            validation_errors=api_response.validation_errors,
            metadata={
                **api_response.metadata,
                "pipeline_orchestration": pipeline_result.to_dict(),
            },
        )

    def get_pipeline_context(self, process_id: UUID) -> PipelineExecutionContext | None:
        return self._traceability.get(process_id)

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "deterministic_pipeline": settings.deterministic_pipeline,
            "traceability_count": self._traceability.count(),
            "motor_gateway": self._motor_gateway.snapshot(),
            "observability_bound": self._observability is not None,
            "performance_optimizer_bound": self._performance_optimizer is not None,
            "validation_gate_bound": self._validation_gate is not None,
        }
