"""Modelos del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.input_models import (
    DefinitiveComparativeModelReference,
    IntelligentAnalysisInputBundle,
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
class IntelligentAnalysisRequest:
    """Solicitud de razonamiento inteligente — estructura preparatoria."""

    process_id: UUID
    codigo_req: str = ""
    definitive_model: DefinitiveComparativeModelReference | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def input_bundle(self) -> IntelligentAnalysisInputBundle:
        return IntelligentAnalysisInputBundle(
            process_id=self.process_id,
            definitive_model=self.definitive_model,
        )


@dataclass(frozen=True)
class IntelligentAnalysisResult:
    """Resultado estructural — sin análisis inteligente generado."""

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
