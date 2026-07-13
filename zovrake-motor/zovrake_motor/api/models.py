"""
Contrato público estable ERP ↔ API de Integración.

Define el sobre de comunicación que el ERP (Centro de Evidencias) utilizará
para hablar con el Motor a través de la API, sin acoplarse a módulos internos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.api.enums import (
    IntegrationApiErrorCode,
    IntegrationApiLifecycleStage,
    PublicContractVersion,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AnalysisDocumentReference:
    """Documento enviado desde el Centro de Evidencias."""

    document_id: str
    document_label: str = ""
    content_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_label": self.document_label,
            "content_type": self.content_type,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RequirementContext:
    """Contexto del requerimiento asociado al análisis."""

    codigo_req: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "codigo_req": self.codigo_req,
            "description": self.description,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PublicAnalysisRequest:
    """
    Solicitud pública de análisis — contrato estable v1.

    Campos mínimos del contrato de comunicación ERP ↔ API ↔ Motor.
    """

    analysis_id: UUID
    codigo_req: str
    project_id: str
    quotation_id: str = ""
    requirement: RequirementContext | None = None
    documents: tuple[AnalysisDocumentReference, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    contract_version: str = PublicContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": str(self.analysis_id),
            "codigo_req": self.codigo_req,
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "requirement": (
                self.requirement.to_dict()
                if self.requirement is not None
                else RequirementContext(codigo_req=self.codigo_req).to_dict()
            ),
            "documents": [document.to_dict() for document in self.documents],
            "metadata": dict(self.metadata),
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class PublicStatusQuery:
    """Consulta pública de estado del análisis."""

    analysis_id: UUID
    project_id: str = ""
    quotation_id: str = ""
    contract_version: str = PublicContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": str(self.analysis_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class PublicResultQuery:
    """Consulta pública del resultado estructurado."""

    analysis_id: UUID
    project_id: str = ""
    quotation_id: str = ""
    result_reference_id: str = ""
    contract_version: str = PublicContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": str(self.analysis_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "result_reference_id": self.result_reference_id,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class ControlledErrorPayload:
    """Error controlado entregado al ERP sin detener otros análisis."""

    error_code: IntegrationApiErrorCode
    message: str
    recoverable: bool = True
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "recoverable": self.recoverable,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class AnalysisStatusPayload:
    """Estado actual del análisis."""

    stage: IntegrationApiLifecycleStage
    processing_status: str = ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "processing_status": self.processing_status,
            "message": self.message,
        }


@dataclass(frozen=True)
class StructuredAnalysisResultPayload:
    """Resultado estructurado listo para representación visual en el ERP."""

    catalog_id: str = ""
    result_reference_id: str = ""
    comparative_tables_ready: bool = False
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "result_reference_id": self.result_reference_id,
            "comparative_tables_ready": self.comparative_tables_ready,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class PublicAnalysisResponse:
    """
    Respuesta pública estable hacia el ERP.

    Contiene identificadores, estado, resultado y errores controlados.
    """

    analysis_id: UUID
    codigo_req: str
    project_id: str
    success: bool
    status: AnalysisStatusPayload
    quotation_id: str = ""
    result: StructuredAnalysisResultPayload | None = None
    error: ControlledErrorPayload | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=_utcnow)
    contract_version: str = PublicContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": str(self.analysis_id),
            "codigo_req": self.codigo_req,
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "success": self.success,
            "status": self.status.to_dict(),
            "result": self.result.to_dict() if self.result is not None else None,
            "error": self.error.to_dict() if self.error is not None else None,
            "metadata": dict(self.metadata),
            "occurred_at": self.occurred_at.isoformat(),
            "contract_version": self.contract_version,
        }
