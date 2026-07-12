"""Resolución de adaptadores documentales."""

from __future__ import annotations

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.models import AdapterResolutionRequest, AdapterResolutionResult
from zovrake_motor.comprehension.adapters.registry import AdapterRegistry
from zovrake_motor.config.categories.comprehension import DocumentAdapterSettings


class AdapterResolver:
    """
    Mecanismo de resolución de adaptadores por tipo de documento.

    No implementa detección automática de formato en esta etapa.
    """

    def __init__(
        self,
        registry: AdapterRegistry,
        *,
        settings: DocumentAdapterSettings | None = None,
    ) -> None:
        self._registry = registry
        self._settings = settings or DocumentAdapterSettings.default()

    @property
    def settings(self) -> DocumentAdapterSettings:
        return self._settings

    def can_resolve(self, format_type: DocumentFormatType) -> bool:
        adapter = self._registry.get(format_type)
        if adapter is None:
            return False
        return self._is_format_enabled(format_type)

    def resolve(self, request: AdapterResolutionRequest) -> AdapterResolutionResult:
        adapter = self._registry.get(request.format_type)
        if adapter is None:
            return AdapterResolutionResult(
                resolved=False,
                format_type=request.format_type,
                adapter_name=None,
                message="Adaptador no registrado para el formato solicitado",
            )

        if not self._is_format_enabled(request.format_type):
            return AdapterResolutionResult(
                resolved=False,
                format_type=request.format_type,
                adapter_name=adapter.adapter_name,
                message="Formato deshabilitado en configuración central",
            )

        return AdapterResolutionResult(
            resolved=True,
            format_type=request.format_type,
            adapter_name=adapter.adapter_name,
            message="Adaptador resuelto — sin procesamiento en esta etapa",
        )

    def _is_format_enabled(self, format_type: DocumentFormatType) -> bool:
        if not self._settings.enabled:
            return False

        mapping = {
            DocumentFormatType.PDF: self._settings.pdf_enabled,
            DocumentFormatType.WORD: self._settings.word_enabled,
            DocumentFormatType.EXCEL: self._settings.excel_enabled,
            DocumentFormatType.IMAGE: self._settings.image_enabled,
        }
        return mapping.get(format_type, False)
