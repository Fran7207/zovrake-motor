"""Construcción de entregas ERP — inmutables, sin interpretación."""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import (
    AnalysisResultDeliveryReference,
    ComparativeTablesDeliveryReference,
    ErpAnalysisDelivery,
    ErpControlledError,
    TraceabilityDeliveryBundle,
)
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.apqm.models import EnqueueResult
from zovrake_motor.enterprise_integration.svaf.models import SecurityValidationOutcome
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisResultResponse,
    AnalysisStatusResponse,
    InternalApiErrorResponse,
    StartAnalysisResponse,
)


class ErpDeliveryBuilder:
    """
    Construye entregas al ERP preservando inmutabilidad del Motor.

    No modifica recomendaciones, explicaciones, evidencias ni confianza.
    """

    def from_start_analysis(
        self,
        erp_request: EvidenceCenterAnalysisRequest,
        motor_response: StartAnalysisResponse | InternalApiErrorResponse,
        *,
        pipeline_context: dict[str, Any] | None = None,
    ) -> ErpAnalysisDelivery:
        if isinstance(motor_response, InternalApiErrorResponse):
            return self._error_delivery(
                process_id=erp_request.process_id,
                project_id=erp_request.project_id,
                quotation_id=erp_request.quotation_id,
                motor_response=motor_response,
            )

        traceability = self._build_traceability(
            erp_request.process_id,
            erp_request.project_id,
            erp_request.quotation_id,
            pipeline_context,
        )
        return ErpAnalysisDelivery(
            process_id=erp_request.process_id,
            project_id=erp_request.project_id,
            quotation_id=erp_request.quotation_id,
            success=motor_response.success,
            message=motor_response.message,
            analysis_status=motor_response.processing_status.value,
            analysis_result=AnalysisResultDeliveryReference(
                result_reference_id=f"pending-{erp_request.process_id}",
                prepared=True,
                executed=False,
                metadata={"start_accepted": True},
            ),
            comparative_tables=ComparativeTablesDeliveryReference(prepared=True),
            traceability=traceability,
            metadata={
                "internal_api_contract": motor_response.contract_version,
                "executed": False,
                "source_data_preserved": True,
            },
        )

    def from_status_query(
        self,
        erp_request: EvidenceCenterStatusQuery,
        motor_response: AnalysisStatusResponse | InternalApiErrorResponse,
        *,
        pipeline_context: dict[str, Any] | None = None,
    ) -> ErpAnalysisDelivery:
        if isinstance(motor_response, InternalApiErrorResponse):
            return self._error_delivery(
                process_id=erp_request.process_id,
                project_id=erp_request.project_id,
                quotation_id=erp_request.quotation_id,
                motor_response=motor_response,
            )

        return ErpAnalysisDelivery(
            process_id=erp_request.process_id,
            project_id=erp_request.project_id,
            quotation_id=erp_request.quotation_id,
            success=motor_response.success,
            message=motor_response.message,
            analysis_status=motor_response.processing_status.value,
            traceability=self._build_traceability(
                erp_request.process_id,
                erp_request.project_id,
                erp_request.quotation_id,
                pipeline_context,
            ),
            metadata={
                "motor_state": motor_response.motor_state,
                "executed": False,
                "source_data_preserved": True,
            },
        )

    def from_result_query(
        self,
        erp_request: EvidenceCenterResultQuery,
        motor_response: AnalysisResultResponse | InternalApiErrorResponse,
        *,
        pipeline_context: dict[str, Any] | None = None,
    ) -> ErpAnalysisDelivery:
        if isinstance(motor_response, InternalApiErrorResponse):
            return self._error_delivery(
                process_id=erp_request.process_id,
                project_id=erp_request.project_id,
                quotation_id=erp_request.quotation_id,
                motor_response=motor_response,
            )

        result_ref = None
        if motor_response.result is not None:
            result_ref = AnalysisResultDeliveryReference(
                result_reference_id=motor_response.result.result_reference_id,
                catalog_id=motor_response.result.catalog_id,
                prepared=motor_response.result.prepared,
                executed=motor_response.result.executed,
                source_data_preserved=motor_response.result.source_data_preserved,
                metadata=dict(motor_response.result.metadata),
            )

        return ErpAnalysisDelivery(
            process_id=erp_request.process_id,
            project_id=erp_request.project_id,
            quotation_id=erp_request.quotation_id,
            success=motor_response.success,
            message=motor_response.message,
            analysis_status=motor_response.processing_status.value,
            analysis_result=result_ref,
            comparative_tables=ComparativeTablesDeliveryReference(
                prepared=True,
                metadata={"delivery_prepared": True},
            ),
            traceability=self._build_traceability(
                erp_request.process_id,
                erp_request.project_id,
                erp_request.quotation_id,
                pipeline_context,
            ),
            metadata={
                "executed": False,
                "source_data_preserved": True,
                "immutable": True,
            },
        )

    def from_enqueue_acceptance(
        self,
        erp_request: EvidenceCenterAnalysisRequest,
        enqueue_result: EnqueueResult,
    ) -> ErpAnalysisDelivery:
        """Entrega inmediata al ERP — procesamiento asíncrono en cola."""
        if not enqueue_result.success:
            return ErpAnalysisDelivery(
                process_id=erp_request.process_id,
                project_id=erp_request.project_id,
                quotation_id=erp_request.quotation_id,
                success=False,
                message=enqueue_result.message,
                analysis_status="error_controlado",
                controlled_error=ErpControlledError(
                    error_code="queue_rejected",
                    message=enqueue_result.message,
                    details=dict(enqueue_result.metadata),
                ),
                metadata={"source_data_preserved": True, "async": True},
            )

        return ErpAnalysisDelivery(
            process_id=erp_request.process_id,
            project_id=erp_request.project_id,
            quotation_id=erp_request.quotation_id,
            success=True,
            message=enqueue_result.message,
            analysis_status="procesamiento_pendiente",
            analysis_result=AnalysisResultDeliveryReference(
                result_reference_id=f"queued-{enqueue_result.queue_item_id}",
                prepared=True,
                executed=False,
                metadata={
                    "queued": True,
                    "queue_item_id": enqueue_result.queue_item_id,
                    "queue_position": enqueue_result.queue_position,
                },
            ),
            comparative_tables=ComparativeTablesDeliveryReference(prepared=True),
            traceability=TraceabilityDeliveryBundle(
                process_id=str(erp_request.process_id),
                project_id=erp_request.project_id,
                quotation_id=erp_request.quotation_id,
                pipeline_transitions=(),
                source_data_preserved=True,
            ),
            metadata={
                "async": True,
                "executed": False,
                "queue_stage": enqueue_result.stage.value,
                "source_data_preserved": True,
            },
        )

    def from_validation_rejection(
        self,
        erp_request: EvidenceCenterAnalysisRequest,
        *,
        outcome: SecurityValidationOutcome,
    ) -> ErpAnalysisDelivery:
        errors = tuple(issue.message for issue in outcome.validation.issues)
        return ErpAnalysisDelivery(
            process_id=erp_request.process_id,
            project_id=erp_request.project_id,
            quotation_id=erp_request.quotation_id,
            success=False,
            message="Validación de seguridad rechazada",
            analysis_status="error_validacion",
            controlled_error=ErpControlledError(
                error_code="structural_validation_failed",
                message="; ".join(errors) or "Validación rechazada",
                details={"pipeline_blocked": outcome.pipeline_blocked},
            ),
            metadata={
                "source_data_preserved": True,
                "svaf_validated": True,
                "notified_ftrrf": outcome.notified_ftrrf,
            },
        )

    def from_security_rejection(
        self,
        *,
        process_id,
        project_id: str,
        quotation_id: str,
        outcome: SecurityValidationOutcome,
    ) -> ErpAnalysisDelivery:
        errors = tuple(issue.message for issue in outcome.validation.issues)
        return ErpAnalysisDelivery(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            success=False,
            message="Validación de seguridad rechazada",
            analysis_status="error_validacion",
            controlled_error=ErpControlledError(
                error_code="structural_validation_failed",
                message="; ".join(errors) or "Validación rechazada",
                details={"pipeline_blocked": outcome.pipeline_blocked},
            ),
            metadata={"source_data_preserved": True, "svaf_validated": True},
        )

    def _error_delivery(
        self,
        *,
        process_id,
        project_id: str,
        quotation_id: str,
        motor_response: InternalApiErrorResponse,
    ) -> ErpAnalysisDelivery:
        return ErpAnalysisDelivery(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            success=False,
            message=motor_response.message,
            analysis_status="error_controlado",
            controlled_error=ErpControlledError(
                error_code=motor_response.error_code.value,
                message=motor_response.message,
                details=dict(motor_response.details),
            ),
            metadata={"source_data_preserved": True},
        )

    def _build_traceability(
        self,
        process_id,
        project_id: str,
        quotation_id: str,
        pipeline_context: dict[str, Any] | None,
    ) -> TraceabilityDeliveryBundle:
        transitions: tuple[dict[str, Any], ...] = ()
        if pipeline_context is not None:
            transitions = tuple(pipeline_context.get("transitions", ()))
        return TraceabilityDeliveryBundle(
            process_id=str(process_id),
            project_id=project_id,
            quotation_id=quotation_id,
            pipeline_transitions=transitions,
            source_data_preserved=True,
        )
