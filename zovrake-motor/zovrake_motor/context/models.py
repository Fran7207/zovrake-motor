"""Modelos del módulo de Gestión del Contexto."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class ProcessContext:
    """
    Contexto del requerimiento.

    Administra el campo 'Detalles del requerimiento' sin interpretarlo.
    """

    process_id: UUID
    codigo_req: str
    detalles_requerimiento: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "detalles_requerimiento": self.detalles_requerimiento,
            "detalles_length": len(self.detalles_requerimiento),
            "metadata": self.metadata,
        }
