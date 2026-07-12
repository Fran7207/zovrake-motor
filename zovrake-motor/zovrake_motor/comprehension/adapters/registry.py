"""Registro centralizado de adaptadores documentales."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.adapters.exceptions import AdapterNotFoundError
from zovrake_motor.comprehension.adapters.implementations import (
    ExcelDocumentAdapter,
    ImageDocumentAdapter,
    PdfDocumentAdapter,
    WordDocumentAdapter,
)
from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort


class AdapterRegistry:
    """
    Registro único de adaptadores documentales.

    Todo adaptador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._adapters_by_format: dict[DocumentFormatType, DocumentAdapterPort] = {}
        self._adapters_by_name: dict[str, DocumentAdapterPort] = {}

    def register(self, adapter: DocumentAdapterPort) -> None:
        """Registra un adaptador sin modificar los existentes."""
        if adapter.format_type in self._adapters_by_format:
            raise ValueError(f"Adaptador ya registrado para formato: {adapter.format_type.value}")
        if adapter.adapter_name in self._adapters_by_name:
            raise ValueError(f"Adaptador ya registrado: {adapter.adapter_name}")

        self._adapters_by_format[adapter.format_type] = adapter
        self._adapters_by_name[adapter.adapter_name] = adapter

    def register_defaults(self) -> None:
        """Registra los adaptadores iniciales del Framework."""
        defaults: tuple[DocumentAdapterPort, ...] = (
            PdfDocumentAdapter(),
            WordDocumentAdapter(),
            ExcelDocumentAdapter(),
            ImageDocumentAdapter(),
        )
        for adapter in defaults:
            self.register(adapter)

    def get(self, format_type: DocumentFormatType) -> DocumentAdapterPort | None:
        return self._adapters_by_format.get(format_type)

    def require(self, format_type: DocumentFormatType) -> DocumentAdapterPort:
        adapter = self.get(format_type)
        if adapter is None:
            raise AdapterNotFoundError(f"Adaptador no registrado para formato: {format_type.value}")
        return adapter

    def get_by_name(self, name: str) -> DocumentAdapterPort | None:
        return self._adapters_by_name.get(name)

    def all_adapters(self) -> tuple[DocumentAdapterPort, ...]:
        return tuple(self._adapters_by_format.values())

    def registered_formats(self) -> tuple[DocumentFormatType, ...]:
        return tuple(self._adapters_by_format.keys())

    def count(self) -> int:
        return len(self._adapters_by_format)

    def ready_count(self) -> int:
        return sum(1 for adapter in self._adapters_by_format.values() if adapter.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [adapter.snapshot() for adapter in self.all_adapters()]
