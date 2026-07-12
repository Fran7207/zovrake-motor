"""Modelos del Document Adapter Framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType


@dataclass(frozen=True)
class AdapterDescriptor:
    """Descriptor estructural de un adaptador documental."""

    adapter_name: str
    adapter_label: str
    format_type: DocumentFormatType
    supported_extensions: tuple[str, ...]
    ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "adapter_label": self.adapter_label,
            "format_type": self.format_type.value,
            "supported_extensions": list(self.supported_extensions),
            "ready": self.ready,
        }


@dataclass(frozen=True)
class AdapterResolutionRequest:
    """Solicitud de resolución de adaptador — sin detección automática."""

    format_type: DocumentFormatType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterResolutionResult:
    """Resultado estructural de resolución de adaptador."""

    resolved: bool
    format_type: DocumentFormatType
    adapter_name: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved": self.resolved,
            "format_type": self.format_type.value,
            "adapter_name": self.adapter_name,
            "message": self.message,
        }
