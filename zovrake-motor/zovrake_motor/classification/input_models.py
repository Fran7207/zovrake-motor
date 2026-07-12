"""Referencias de entrada del Módulo de Comprensión Documental — sin acoplamiento directo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class InternalDocumentModelReference:
    """
    Referencia al Modelo Documental Interno (IDMB).

    El módulo de clasificación consume exclusivamente esta referencia;
    nunca accede al documento original.
    """

    model_id: str
    document_id: str
    schema_version: str
    immutable: bool = True
    classification_ready: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "document_id": self.document_id,
            "schema_version": self.schema_version,
            "immutable": self.immutable,
            "classification_ready": self.classification_ready,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DocumentIndexReference:
    """Referencia a una entrada del Document Knowledge Index (DKI)."""

    index_entry_id: str
    model_id: str
    process_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index_entry_id": self.index_entry_id,
            "model_id": self.model_id,
            "process_id": self.process_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class IntegratedContextReference:
    """Referencia al Contexto Integrado asociado al requerimiento."""

    association_id: str
    process_id: str
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "association_id": self.association_id,
            "process_id": self.process_id,
            "codigo_req": self.codigo_req,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ClassificationInputBundle:
    """
    Paquete de entradas provenientes de Comprensión Documental.

    Contrato preparatorio para consumo exclusivo de IDMB, DKI y Contexto Integrado.
    """

    process_id: UUID
    internal_model: InternalDocumentModelReference | None = None
    index_reference: DocumentIndexReference | None = None
    context_reference: IntegratedContextReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "internal_model": (
                self.internal_model.to_dict() if self.internal_model is not None else None
            ),
            "index_reference": (
                self.index_reference.to_dict() if self.index_reference is not None else None
            ),
            "context_reference": (
                self.context_reference.to_dict() if self.context_reference is not None else None
            ),
        }
