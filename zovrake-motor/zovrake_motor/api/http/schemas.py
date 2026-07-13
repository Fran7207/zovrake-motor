"""Esquemas Pydantic de la API REST — mapeo al contrato público 9.1."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from zovrake_motor.api.enums import PublicContractVersion
from zovrake_motor.api.models import (
    AnalysisDocumentReference,
    PublicAnalysisRequest,
    PublicResultQuery,
    PublicStatusQuery,
    RequirementContext,
)


class DocumentPayload(BaseModel):
    document_id: str
    document_label: str = ""
    content_type: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("document_id es obligatorio")
        return cleaned


class RequirementPayload(BaseModel):
    codigo_req: str
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("codigo_req")
    @classmethod
    def validate_codigo_req(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("codigo_req es obligatorio")
        return cleaned


class CreateAnalysisPayload(BaseModel):
    codigo_req: str
    project_id: str
    quotation_id: str = ""
    analysis_id: UUID | None = None
    requirement: RequirementPayload | None = None
    documents: list[DocumentPayload] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    contract_version: str = PublicContractVersion.V1.value

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("project_id es obligatorio")
        return cleaned

    @field_validator("codigo_req")
    @classmethod
    def validate_codigo_req(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("codigo_req es obligatorio")
        return cleaned

    def to_public_request(self) -> PublicAnalysisRequest:
        requirement = self.requirement or RequirementPayload(
            codigo_req=self.codigo_req,
            description="",
        )
        return PublicAnalysisRequest(
            analysis_id=self.analysis_id or uuid4(),
            codigo_req=self.codigo_req,
            project_id=self.project_id,
            quotation_id=self.quotation_id,
            requirement=RequirementContext(
                codigo_req=requirement.codigo_req,
                description=requirement.description,
                metadata=dict(requirement.metadata),
            ),
            documents=tuple(
                AnalysisDocumentReference(
                    document_id=document.document_id,
                    document_label=document.document_label,
                    content_type=document.content_type,
                    metadata=dict(document.metadata),
                )
                for document in self.documents
            ),
            metadata=dict(self.metadata),
            contract_version=self.contract_version,
        )


class AnalysisQueryParams(BaseModel):
    project_id: str = ""
    quotation_id: str = ""
    result_reference_id: str = ""

    def to_status_query(self, analysis_id: UUID) -> PublicStatusQuery:
        return PublicStatusQuery(
            analysis_id=analysis_id,
            project_id=self.project_id,
            quotation_id=self.quotation_id,
        )

    def to_result_query(self, analysis_id: UUID) -> PublicResultQuery:
        return PublicResultQuery(
            analysis_id=analysis_id,
            project_id=self.project_id,
            quotation_id=self.quotation_id,
            result_reference_id=self.result_reference_id,
        )
