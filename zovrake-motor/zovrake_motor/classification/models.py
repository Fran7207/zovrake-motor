"""Modelos del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.input_models import (
    ClassificationInputBundle,
    DocumentIndexReference,
    IntegratedContextReference,
    InternalDocumentModelReference,
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
class ClassificationRequest:
    """Solicitud de clasificación inteligente — estructura preparatoria."""

    process_id: UUID
    codigo_req: str = ""
    internal_model: InternalDocumentModelReference | None = None
    index_reference: DocumentIndexReference | None = None
    context_reference: IntegratedContextReference | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def input_bundle(self) -> ClassificationInputBundle:
        return ClassificationInputBundle(
            process_id=self.process_id,
            internal_model=self.internal_model,
            index_reference=self.index_reference,
            context_reference=self.context_reference,
        )


@dataclass(frozen=True)
class ClassificationResult:
    """Resultado estructural de clasificación — sin grupos comparables."""

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
