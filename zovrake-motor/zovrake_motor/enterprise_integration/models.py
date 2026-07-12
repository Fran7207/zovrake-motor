"""Modelos del Módulo de Integración Empresarial."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.input_models import (
    EnterpriseIntegrationInputBundle,
    IntelligentAnalysisResultReference,
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
class EnterpriseIntegrationRequest:
    """Solicitud de integración empresarial — estructura preparatoria."""

    process_id: UUID
    codigo_req: str = ""
    analysis_result: IntelligentAnalysisResultReference | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def input_bundle(self) -> EnterpriseIntegrationInputBundle:
        return EnterpriseIntegrationInputBundle(
            process_id=self.process_id,
            analysis_result=self.analysis_result,
            codigo_req=self.codigo_req,
        )


@dataclass(frozen=True)
class EnterpriseIntegrationResult:
    """Resultado estructural — sin integración ejecutada."""

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
