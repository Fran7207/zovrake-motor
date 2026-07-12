"""Modelos del módulo de Recepción."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class ReceptionResult:
    """Resultado de recepción — estructura preparatoria."""

    accepted: bool
    process_id: UUID
    codigo_req: str
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "message": self.message,
            "metadata": self.metadata,
        }
