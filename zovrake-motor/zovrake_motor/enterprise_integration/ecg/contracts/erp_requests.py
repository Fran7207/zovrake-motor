"""Contratos de entrada desde el Centro de Evidencias (ERP) — sin acoplamiento al frontend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.enums import EcgContractVersion


@dataclass(frozen=True)
class EvidenceDocumentReference:
    """Referencia inmutable a un documento del Centro de Evidencias."""

    document_id: str
    document_label: str = ""
    reference_type: str = "evidence_center"
    source_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_label": self.document_label,
            "reference_type": self.reference_type,
            "source_preserved": self.source_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class RequirementDetailsReference:
    """Detalles del requerimiento — referencia estructural sin validación documental."""

    codigo_req: str
    description: str = ""
    source_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "codigo_req": self.codigo_req,
            "description": self.description,
            "source_preserved": self.source_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EvidenceCenterAnalysisRequest:
    """
    Solicitud oficial del Centro de Evidencias (Cotizaciones) hacia el Motor.

    Único contrato de entrada ERP → ECG en 8.4.
    """

    process_id: UUID
    project_id: str
    quotation_id: str
    requirement: RequirementDetailsReference
    evidence_documents: tuple[EvidenceDocumentReference, ...] = field(default_factory=tuple)
    analysis_metadata: dict[str, Any] = field(default_factory=dict)
    contract_version: str = EcgContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "requirement": self.requirement.to_dict(),
            "evidence_documents": [doc.to_dict() for doc in self.evidence_documents],
            "analysis_metadata": self.analysis_metadata,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class EvidenceCenterStatusQuery:
    """Consulta de estado desde el Centro de Evidencias."""

    process_id: UUID
    project_id: str = ""
    quotation_id: str = ""
    contract_version: str = EcgContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "contract_version": self.contract_version,
        }


@dataclass(frozen=True)
class EvidenceCenterResultQuery:
    """Consulta de resultado desde el Centro de Evidencias."""

    process_id: UUID
    project_id: str = ""
    quotation_id: str = ""
    result_reference_id: str = ""
    contract_version: str = EcgContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "result_reference_id": self.result_reference_id,
            "contract_version": self.contract_version,
        }
