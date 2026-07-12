"""Modelos del módulo de Gestión de Documentos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DocumentReference:
    """Referencia a un documento — sin contenido ni lectura en esta etapa."""

    id: str
    nombre: str
    tipo: str
    tamano: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentCollection:
    """Colección de documentos asociada a un proceso."""

    process_id: UUID
    codigo_req: str
    documents: list[DocumentReference] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.documents)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "count": self.count,
            "documents": [
                {"id": d.id, "nombre": d.nombre, "tipo": d.tipo, "tamano": d.tamano}
                for d in self.documents
            ],
        }
