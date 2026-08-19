"""Transformación ERP → contrato oficial de la API Interna."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    StartAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry


class ErpRequestTransformer:
    """
    Transforma solicitudes del Centro de Evidencias al contrato Internal API v1.

    Nunca produce estructuras improvisadas.
    """

def to_start_analysis(
    self,
    request: EvidenceCenterAnalysisRequest,
) -> StartAnalysisRequest:
    """
    Transforma una solicitud del Centro de Evidencias al contrato
    oficial de la API Interna conservando las referencias documentales.

    Esta capa no interpreta ni procesa el contenido de los documentos.
    Únicamente conserva la información necesaria para que el Motor
    pueda resolver y procesar posteriormente el documento real.
    """
    document_ids = tuple(
        doc.document_id
        for doc in request.evidence_documents
    )

    document_references = tuple(
        {
            "document_id": doc.document_id,
            "document_label": doc.document_label,
            "content_type": str(
                (doc.metadata or {}).get("content_type", "")
            ),
            "metadata": dict(doc.metadata or {}),
        }
        for doc in request.evidence_documents
    )

    return StartAnalysisRequest(
        process_id=request.process_id,
        codigo_req=request.requirement.codigo_req,
        contract_version=ContractVersionRegistry.ACTIVE_VERSION,
        document_ids=document_ids,
        document_references=document_references,
        metadata={
            "source": "evidence_center",
            "project_id": request.project_id,
            "quotation_id": request.quotation_id,
            "analysis_metadata": request.analysis_metadata,
            "evidence_center_contract": request.contract_version,
            "requirement_description": request.requirement.description,
            "requirement_metadata": dict(
                request.requirement.metadata or {}
            ),
            "source_data_preserved": True,
            "document_count": len(document_references),
        },
    )

    def to_status_query(self, request: EvidenceCenterStatusQuery) -> AnalysisStatusQueryRequest:
        return AnalysisStatusQueryRequest(
            process_id=request.process_id,
            codigo_req="",
            contract_version=ContractVersionRegistry.ACTIVE_VERSION,
            metadata={
                "project_id": request.project_id,
                "quotation_id": request.quotation_id,
                "evidence_center_contract": request.contract_version,
            },
        )

    def to_result_query(self, request: EvidenceCenterResultQuery) -> AnalysisResultQueryRequest:
        return AnalysisResultQueryRequest(
            process_id=request.process_id,
            codigo_req="",
            contract_version=ContractVersionRegistry.ACTIVE_VERSION,
            result_reference_id=request.result_reference_id,
            metadata={
                "project_id": request.project_id,
                "quotation_id": request.quotation_id,
                "evidence_center_contract": request.contract_version,
            },
        )
