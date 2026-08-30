"""Modelos del Módulo de Comprensión Documental."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ComponentDescriptor:
    """Descriptor de un componente interno — sin lógica de negocio."""

    component_type: str
    name: str
    label: str
    ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_type": self.component_type,
            "name": self.name,
            "label": self.label,
            "ready": self.ready,
        }


@dataclass(frozen=True)
class ComprehensionRequest:
    """Solicitud de comprensión documental."""

    process_id: UUID
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentEvidence:
    """
    Evidencia atómica de un dato comprendido.

    Conserva la procedencia necesaria para auditar una conclusión posterior
    sin volver a interpretar el documento original.
    """

    evidence_id: str
    source_kind: str
    source_id: str
    page_number: int | None = None
    text: str = ""
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "page_number": self.page_number,
            "text": self.text,
            "bbox": (
                list(self.bbox)
                if self.bbox is not None
                else None
            ),
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DocumentRegion:
    """
    Región física/documental independiente de su interpretación final.

    Permite conservar encabezados, bloques de texto, tablas, imágenes,
    regiones OCR y otras áreas detectadas de una página.
    """

    region_id: str
    page_number: int
    region_type: str
    bbox: tuple[float, float, float, float] | None = None
    content: str = ""
    source_kind: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "page_number": self.page_number,
            "region_type": self.region_type,
            "bbox": (
                list(self.bbox)
                if self.bbox is not None
                else None
            ),
            "content": self.content,
            "source_kind": self.source_kind,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DocumentEntity:
    """
    Entidad detectada dentro del documento.

    ``role`` permite expresar el papel documental de una entidad sin
    obligar al documento a tener una estructura fija. Ejemplos:
    provider, customer, manufacturer, representative, bank.
    """

    entity_id: str
    entity_type: str
    role: str
    name: str = ""
    identifier: str = ""
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "role": self.role,
            "name": self.name,
            "identifier": self.identifier,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class DocumentRelationship:
    """
    Relación explícita entre dos elementos del conocimiento documental.

    Permite representar relaciones como:
    entidad -> supplies -> item
    entidad -> customer_of -> document
    fact -> belongs_to -> entity
    """

    relationship_id: str
    source_id: str
    relationship_type: str
    target_id: str
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_id": self.source_id,
            "relationship_type": self.relationship_type,
            "target_id": self.target_id,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DocumentKnowledge:
    """
    Representación unificada del conocimiento descubierto en un documento.

    Esta estructura NO está limitada a cotizaciones. Su propósito es
    conservar el contenido detectado y su contexto antes de que módulos
    especializados como PM5, PM6 o PM7 decidan qué subconjunto utilizar.

    Principio:
        extraer -> conservar -> interpretar -> relacionar -> evidenciar

    ``unresolved`` permite registrar elementos que existen pero cuya
    interpretación todavía no alcanzó una resolución suficiente.
    """

    document_id: str
    file_name: str = ""
    content_type: str = ""
    page_count: int = 0

    # Representación física/documental.
    regions: tuple[DocumentRegion, ...] = ()
    text: str = ""
    tables: tuple[dict[str, Any], ...] = ()
    images: tuple[dict[str, Any], ...] = ()
    ocr_blocks: tuple[dict[str, Any], ...] = ()

    # Comprensión semántica.
    sections: tuple[dict[str, Any], ...] = ()
    entities: tuple[DocumentEntity, ...] = ()
    attributes: tuple[dict[str, Any], ...] = ()
    relationships: tuple[DocumentRelationship, ...] = ()
    facts: tuple[dict[str, Any], ...] = ()

    # Trazabilidad e incertidumbre.
    evidence: tuple[DocumentEvidence, ...] = ()
    unresolved: tuple[dict[str, Any], ...] = ()
    confidence: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)

    def evidence_by_id(
        self,
        evidence_id: str,
    ) -> DocumentEvidence | None:
        """Obtiene una evidencia por ID sin mutar el modelo."""
        for evidence in self.evidence:
            if evidence.evidence_id == evidence_id:
                return evidence
        return None

    def entity_by_id(
        self,
        entity_id: str,
    ) -> DocumentEntity | None:
        """Obtiene una entidad por ID sin mutar el modelo."""
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None

    def entities_by_role(
        self,
        role: str,
    ) -> tuple[DocumentEntity, ...]:
        """Obtiene todas las entidades con un rol documental concreto."""
        normalized_role = role.strip().lower()

        if not normalized_role:
            return ()

        return tuple(
            entity
            for entity in self.entities
            if entity.role.strip().lower() == normalized_role
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "file_name": self.file_name,
            "content_type": self.content_type,
            "page_count": self.page_count,
            "regions": [
                region.to_dict()
                for region in self.regions
            ],
            "text": self.text,
            "tables": list(self.tables),
            "images": list(self.images),
            "ocr_blocks": list(self.ocr_blocks),
            "sections": list(self.sections),
            "entities": [
                entity.to_dict()
                for entity in self.entities
            ],
            "attributes": list(self.attributes),
            "relationships": [
                relationship.to_dict()
                for relationship in self.relationships
            ],
            "facts": list(self.facts),
            "evidence": [
                evidence.to_dict()
                for evidence in self.evidence
            ],
            "unresolved": list(self.unresolved),
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComprehensionResult:
    """
    Resultado estructurado de comprensión.

    ``document_knowledge`` es opcional durante la transición para mantener
    compatibilidad con consumidores existentes. Cuando el pipeline empiece
    a construir el conocimiento unificado, esta será la representación
    que alimentará las capas posteriores.
    """

    process_id: UUID
    prepared: bool
    message: str
    components_ready: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    document_knowledge: DocumentKnowledge | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "prepared": self.prepared,
            "message": self.message,
            "components_ready": self.components_ready,
            "metadata": self.metadata,
            "document_knowledge": (
                self.document_knowledge.to_dict()
                if self.document_knowledge is not None
                else None
            ),
        }
