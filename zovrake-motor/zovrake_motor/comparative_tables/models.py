"""Modelos del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.input_models import (
    ComparativeDomainModelReference,
    ComparativeTablesInputBundle,
)


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
class ComparativeTablesRequest:
    """Solicitud de generación de cuadros comparativos — estructura preparatoria."""

    process_id: UUID
    codigo_req: str = ""
    domain_model: ComparativeDomainModelReference | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def input_bundle(self) -> ComparativeTablesInputBundle:
        return ComparativeTablesInputBundle(
            process_id=self.process_id,
            domain_model=self.domain_model,
        )


@dataclass(frozen=True)
class ComparativeTablesResult:
    """Resultado estructural — sin cuadros comparativos generados."""

    process_id: UUID
    prepared: bool
    message: str
    components_ready: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "prepared": self.prepared,
            "message": self.message,
            "components_ready": self.components_ready,
            "metadata": self.metadata,
        }
