"""Adaptador API Pública → ERP Communication Gateway (PM8)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.api.enums import (
    IntegrationApiErrorCode,
    IntegrationApiLifecycleStage,
)
from zovrake_motor.api.models import (
    AnalysisStatusPayload,
    ControlledErrorPayload,
    PublicAnalysisRequest,
    PublicAnalysisResponse,
    PublicResultQuery,
    PublicStatusQuery,
    StructuredAnalysisResultPayload,
)
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import (
        ErpAnalysisDelivery,
    )
    from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class EcgGatewayAdapter:
    """
    Traduce el contrato público de la API al contrato oficial ECG (PM8).

    No modifica el Motor Inteligente ni el ERP.
    No interpreta documentos ni ejecuta inteligencia.
    """

    def __init__(self, service: EnterpriseIntegrationService) -> None:
        self._service = service

    def submit_analysis(self, request: PublicAnalysisRequest) -> PublicAnalysisResponse:
        self._service.initialize()
        evidence_request = self._to_evidence_request(request)
        delivery = self._service.submit_evidence_center_analysis(evidence_request)
        return self._from_delivery(
            delivery,
            analysis_id=request.analysis_id,
            codigo_req=request.codigo_req,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
            default_stage=IntegrationApiLifecycleStage.SENT_TO_MOTOR,
        )

    def query_status(self, query: PublicStatusQuery) -> PublicAnalysisResponse:
        self._service.initialize()
        delivery = self._service.query_evidence_center_status(
            EvidenceCenterStatusQuery(
                process_id=query.analysis_id,
                project_id=query.project_id,
                quotation_id=query.quotation_id,
            ),
        )
        return self._from_delivery(
            delivery,
            analysis_id=query.analysis_id,
            codigo_req="",
            project_id=query.project_id,
            quotation_id=query.quotation_id,
            default_stage=self._lifecycle_stage_from_queue(query.analysis_id),
        )

    def query_result(self, query: PublicResultQuery) -> PublicAnalysisResponse:
        self._service.initialize()
        delivery = self._service.query_evidence_center_result(
            EvidenceCenterResultQuery(
                process_id=query.analysis_id,
                project_id=query.project_id,
                quotation_id=query.quotation_id,
                result_reference_id=query.result_reference_id,
            ),
        )
        return self._from_delivery(
            delivery,
            analysis_id=query.analysis_id,
            codigo_req="",
            project_id=query.project_id,
            quotation_id=query.quotation_id,
            default_stage=IntegrationApiLifecycleStage.RESULT_GENERATED,
        )

    def _lifecycle_stage_from_queue(self, analysis_id) -> IntegrationApiLifecycleStage:
        """Deriva la etapa pública del ciclo de vida desde el estado real de la cola APQM."""
        from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage

        apqm = self._service.async_processing_queue_manager
        if apqm is None or not apqm.is_ready():
            return IntegrationApiLifecycleStage.PROCESSING

        item = apqm.manager.get_item_by_process(analysis_id)
        if item is None:
            return IntegrationApiLifecycleStage.PROCESSING

        if item.stage == ApqmProcessingStage.PROCESSING_COMPLETED:
            return IntegrationApiLifecycleStage.RESULT_GENERATED
        if item.stage == ApqmProcessingStage.CONTROLLED_ERROR:
            return IntegrationApiLifecycleStage.FAILED
        if item.stage == ApqmProcessingStage.PROCESSING_CANCELLED:
            return IntegrationApiLifecycleStage.CANCELLED
        return IntegrationApiLifecycleStage.PROCESSING

    @staticmethod
    def _to_evidence_request(request: PublicAnalysisRequest) -> EvidenceCenterAnalysisRequest:
        requirement = request.requirement
        codigo_req = requirement.codigo_req if requirement is not None else request.codigo_req
        description = requirement.description if requirement is not None else ""
        documents = tuple(
            EvidenceDocumentReference(
                document_id=document.document_id,
                document_label=document.document_label,
                metadata={
                    **document.metadata,
                    **({"content_type": document.content_type} if document.content_type else {}),
                },
            )
            for document in request.documents
        )
        analysis_metadata = dict(request.metadata)
        analysis_metadata.setdefault("source", "integration_api")
        analysis_metadata["public_contract_version"] = request.contract_version
        analysis_metadata.setdefault("integration_channel", "integration_api")
        return EvidenceCenterAnalysisRequest(
            process_id=request.analysis_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
            requirement=RequirementDetailsReference(
                codigo_req=codigo_req,
                description=description,
                metadata=dict(requirement.metadata) if requirement is not None else {},
            ),
            evidence_documents=documents,
            analysis_metadata=analysis_metadata,
        )

    @staticmethod
    def _from_delivery(
        delivery: ErpAnalysisDelivery,
        *,
        analysis_id,
        codigo_req: str,
        project_id: str,
        quotation_id: str,
        default_stage: IntegrationApiLifecycleStage,
    ) -> PublicAnalysisResponse:
        error: ControlledErrorPayload | None = None
        if not delivery.success:
            error = ControlledErrorPayload(
                error_code=IntegrationApiErrorCode.INTERNAL_ERROR,
                message=delivery.message or "Error controlado en la plataforma de integración",
                recoverable=True,
                details={"analysis_status": delivery.analysis_status},
            )

        result: StructuredAnalysisResultPayload | None = None
        analysis_result = getattr(delivery, "analysis_result", None)
        if analysis_result is not None:
            payload = analysis_result.to_dict() if hasattr(analysis_result, "to_dict") else {}
            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            comparative_ready = bool(
                metadata.get("comparative_tables")
                or payload.get("executed")
                or payload.get("comparative_tables")
            )
            result = StructuredAnalysisResultPayload(
                catalog_id=str(payload.get("catalog_id", "")),
                result_reference_id=str(payload.get("result_reference_id", "")),
                comparative_tables_ready=comparative_ready,
                payload=payload if isinstance(payload, dict) else {},
            )

        stage = default_stage
        if delivery.success and getattr(delivery, "metadata", None):
            metadata = delivery.metadata if isinstance(delivery.metadata, dict) else {}
            if metadata.get("async") is True:
                stage = IntegrationApiLifecycleStage.SENT_TO_MOTOR

        status = AnalysisStatusPayload(
            stage=stage if delivery.success else IntegrationApiLifecycleStage.FAILED,
            processing_status=str(delivery.analysis_status or ""),
            message=delivery.message or "",
        )

        metadata: dict[str, Any] = {}
        if isinstance(getattr(delivery, "metadata", None), dict):
            metadata = dict(delivery.metadata)

        return PublicAnalysisResponse(
            analysis_id=analysis_id,
            codigo_req=codigo_req,
            project_id=project_id,
            quotation_id=quotation_id,
            success=delivery.success,
            status=status,
            result=result,
            error=error,
            metadata=metadata,
        )
