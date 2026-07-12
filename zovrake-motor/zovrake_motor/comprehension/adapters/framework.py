"""Framework central de Adaptadores Documentales."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.adapters.models import AdapterResolutionRequest, AdapterResolutionResult
from zovrake_motor.comprehension.adapters.registry import AdapterRegistry
from zovrake_motor.comprehension.adapters.resolver import AdapterResolver
from zovrake_motor.config.categories.comprehension import DocumentAdapterSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentAdapterFramework:
    """
    Framework central del Módulo de Comprensión Documental.

    Administra el registro, resolución y extensión de adaptadores documentales.
    El núcleo del Motor nunca depende de un formato específico.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: AdapterRegistry | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or AdapterRegistry()
        self._resolver: AdapterResolver | None = None
        self._initialized = False

    @property
    def registry(self) -> AdapterRegistry:
        return self._registry

    @property
    def resolver(self) -> AdapterResolver:
        if self._resolver is None:
            self._resolver = AdapterResolver(self._registry, settings=self._adapter_settings())
        return self._resolver

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= 4

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults()
        self._resolver = AdapterResolver(self._registry, settings=self._adapter_settings())
        self._initialized = True

    def resolve(self, request: AdapterResolutionRequest) -> AdapterResolutionResult:
        return self.resolver.resolve(request)

    def extend(self, adapter: Any) -> None:
        """Incorpora un nuevo adaptador mediante extensión sin modificar el núcleo."""
        from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort

        if not isinstance(adapter, DocumentAdapterPort):
            raise TypeError("El adaptador debe implementar DocumentAdapterPort")
        self._registry.register(adapter)

    def _adapter_settings(self) -> DocumentAdapterSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().adapters
        return DocumentAdapterSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._adapter_settings()
        return {
            "initialized": self._initialized,
            "adapters_count": self._registry.count(),
            "adapters_ready": self._registry.ready_count(),
            "registered_formats": [fmt.value for fmt in self._registry.registered_formats()],
            "adapters": self._registry.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "auto_resolution_enabled": settings.auto_resolution_enabled,
                "pdf_enabled": settings.pdf_enabled,
                "word_enabled": settings.word_enabled,
                "excel_enabled": settings.excel_enabled,
                "image_enabled": settings.image_enabled,
            },
        }
