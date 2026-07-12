"""Modelos del Content Extraction Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.extraction.enums import ExtractionIncidentSeverity


@dataclass(frozen=True)
class AdapterDocumentContext:
    """
    Contexto del documento recibido exclusivamente a través del adaptador.

    El CEE nunca accede directamente al documento original.
    """

    process_id: UUID
    document_id: str
    adapter_name: str
    format_type: str
    document_reference: str
    original_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "adapter_name": self.adapter_name,
            "format_type": self.format_type,
            "document_reference": self.document_reference,
            "original_preserved": self.original_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ContentExtractionRequest:
    """Solicitud de extracción — documento vía adaptador únicamente."""

    process_id: UUID
    document_id: str
    adapter_context: AdapterDocumentContext
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractedTable:
    """Tabla detectada durante la extracción."""

    table_id: str
    rows: tuple[tuple[str, ...], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "rows": [list(row) for row in self.rows],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class StructuralElement:
    """Elemento estructural encontrado durante la extracción."""

    element_type: str
    content: str
    position: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_type": self.element_type,
            "content": self.content,
            "position": self.position,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ExtractionIncident:
    """Incidencia detectada durante la extracción."""

    extractor_name: str
    message: str
    severity: ExtractionIncidentSeverity = ExtractionIncidentSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        return {
            "extractor_name": self.extractor_name,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class ExtractorResult:
    """Resultado individual de un extractor especializado."""

    extractor_name: str
    extractor_type: str
    extracted_text: str = ""
    tables: tuple[ExtractedTable, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    structural_elements: tuple[StructuralElement, ...] = ()
    incidents: tuple[ExtractionIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "extractor_name": self.extractor_name,
            "extractor_type": self.extractor_type,
            "extracted_text": self.extracted_text,
            "tables": [table.to_dict() for table in self.tables],
            "metadata": self.metadata,
            "structural_elements": [element.to_dict() for element in self.structural_elements],
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }


@dataclass(frozen=True)
class ContentExtractionResult:
    """Resultado estructurado y uniforme de extracción documental."""

    process_id: UUID
    document_id: str
    extracted_text: str
    tables: tuple[ExtractedTable, ...]
    metadata: dict[str, Any]
    structural_elements: tuple[StructuralElement, ...]
    incidents: tuple[ExtractionIncident, ...]
    original_preserved: bool
    ocr_integration_prepared: bool
    extractors_executed: int
    adapter_name: str
    technical_observations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "extracted_text": self.extracted_text,
            "tables": [table.to_dict() for table in self.tables],
            "metadata": self.metadata,
            "structural_elements": [element.to_dict() for element in self.structural_elements],
            "incidents": [incident.to_dict() for incident in self.incidents],
            "original_preserved": self.original_preserved,
            "ocr_integration_prepared": self.ocr_integration_prepared,
            "extractors_executed": self.extractors_executed,
            "adapter_name": self.adapter_name,
            "technical_observations": list(self.technical_observations),
        }
