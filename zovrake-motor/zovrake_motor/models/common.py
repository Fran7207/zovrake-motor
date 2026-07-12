"""Modelos compartidos del dominio del Motor — sin lógica de negocio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class MotorRequest:
    """Solicitud futura proveniente del ERP — estructura preparatoria."""

    codigo_req: str
    detalles_requerimiento: str = ""
    process_id: UUID = field(default_factory=uuid4)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MotorResponse:
    """Respuesta futura hacia el ERP — estructura preparatoria."""

    process_id: UUID
    codigo_req: str
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
