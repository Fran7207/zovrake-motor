"""Contrato base del Document Adapter Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType


class DocumentAdapterPort(ABC):
    """
    Contrato común para todos los adaptadores documentales.

    Garantiza que cualquier formato se integre mediante la misma interfaz.
    """

    @property
    @abstractmethod
    def format_type(self) -> DocumentFormatType:
        """Formato documental que adapta este componente."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Identificador único del adaptador."""

    @property
    @abstractmethod
    def adapter_label(self) -> str:
        """Etiqueta descriptiva del adaptador."""

    @property
    @abstractmethod
    def supported_extensions(self) -> tuple[str, ...]:
        """Extensiones de archivo asociadas al formato."""

    @abstractmethod
    def is_ready(self) -> bool:
        """Indica si el adaptador está preparado para etapas futuras."""

    def supports_format(self, format_type: DocumentFormatType) -> bool:
        return self.format_type == format_type

    def snapshot(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "adapter_label": self.adapter_label,
            "format_type": self.format_type.value,
            "supported_extensions": list(self.supported_extensions),
            "ready": self.is_ready(),
        }
