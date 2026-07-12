"""Motor central de Reconocimiento Documental (DRE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.adapters.framework import DocumentAdapterFramework
from zovrake_motor.comprehension.adapters.models import AdapterResolutionRequest
from zovrake_motor.comprehension.recognition.models import (
    AdapterSelectionPrepared,
    DocumentRecognitionRequest,
    DocumentRecognitionResult,
)
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.registry import RecognitionStrategyRegistry
from zovrake_motor.comprehension.recognition.resolver import RecognitionResolver
from zovrake_motor.config.categories.comprehension import DocumentRecognitionSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentRecognitionEngine:
    """
    Document Recognition Engine (DRE).

    Único responsable de identificar el tipo documental y preparar
    la selección del adaptador correspondiente.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: RecognitionStrategyRegistry | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or RecognitionStrategyRegistry()
        self._resolver: RecognitionResolver | None = None
        self._initialized = False

    @property
    def registry(self) -> RecognitionStrategyRegistry:
        return self._registry

    @property
    def resolver(self) -> RecognitionResolver:
        if self._resolver is None:
            self._resolver = RecognitionResolver(self._registry, settings=self._recognition_settings())
        return self._resolver

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= 3

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults(settings=self._recognition_settings())
        self._resolver = RecognitionResolver(self._registry, settings=self._recognition_settings())
        self._initialized = True

    def recognize(self, request: DocumentRecognitionRequest) -> DocumentRecognitionResult:
        return self.resolver.resolve(request)

    def prepare_adapter_selection(
        self,
        result: DocumentRecognitionResult,
        *,
        adapter_framework: DocumentAdapterFramework | None = None,
    ) -> DocumentRecognitionResult:
        """Prepara la selección del adaptador sin ejecutarlo."""
        if not result.recognized or result.identified_format is None:
            adapter_selection = AdapterSelectionPrepared(
                format_type=None,
                suggested_adapter=None,
                adapter_resolvable=False,
                resolution_message="Formato no identificado — adaptador no preparado",
            )
            return self._with_adapter_selection(result, adapter_selection)

        suggested_adapter = result.suggested_adapter
        adapter_resolvable = False
        resolution_message = "Adaptador sugerido por catálogo — sin resolución del framework"

        if adapter_framework is not None:
            resolution = adapter_framework.resolve(
                AdapterResolutionRequest(format_type=result.identified_format),
            )
            suggested_adapter = resolution.adapter_name or suggested_adapter
            adapter_resolvable = resolution.resolved
            resolution_message = resolution.message
        elif suggested_adapter is not None:
            adapter_resolvable = True
            resolution_message = "Adaptador sugerido por catálogo de formatos"

        adapter_selection = AdapterSelectionPrepared(
            format_type=result.identified_format,
            suggested_adapter=suggested_adapter,
            adapter_resolvable=adapter_resolvable,
            resolution_message=resolution_message,
        )
        return self._with_adapter_selection(result, adapter_selection)

    def extend(self, strategy: RecognitionStrategyPort) -> None:
        """Incorpora una nueva estrategia mediante extensión sin modificar el núcleo."""
        self._registry.register(strategy)

    def _recognition_settings(self) -> DocumentRecognitionSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().recognition
        return DocumentRecognitionSettings.default()

    def _with_adapter_selection(
        self,
        result: DocumentRecognitionResult,
        adapter_selection: AdapterSelectionPrepared,
    ) -> DocumentRecognitionResult:
        observations = (
            *result.technical_observations,
            f"adapter_selection_prepared={adapter_selection.adapter_resolvable}",
        )
        return DocumentRecognitionResult(
            process_id=result.process_id,
            document_id=result.document_id,
            recognized=result.recognized,
            identified_format=result.identified_format,
            confidence=result.confidence,
            confidence_level=result.confidence_level,
            strategy_used=result.strategy_used,
            strategy_type=result.strategy_type,
            suggested_adapter=adapter_selection.suggested_adapter or result.suggested_adapter,
            adapter_selection=adapter_selection,
            technical_observations=observations,
            strategies_executed=result.strategies_executed,
        )

    def snapshot(self) -> dict[str, Any]:
        settings = self._recognition_settings()
        return {
            "initialized": self._initialized,
            "strategies_count": self._registry.count(),
            "strategies": self._registry.snapshot(),
            "format_catalog": self._format_catalog_snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "min_confidence_threshold": settings.min_confidence_threshold,
                "extension_strategy_enabled": settings.extension_strategy_enabled,
                "mime_type_strategy_enabled": settings.mime_type_strategy_enabled,
                "metadata_strategy_enabled": settings.metadata_strategy_enabled,
                "magic_number_strategy_enabled": settings.magic_number_strategy_enabled,
                "supported_formats": list(settings.supported_formats),
            },
        }

    def _format_catalog_snapshot(self) -> dict[str, Any]:
        from zovrake_motor.comprehension.recognition.catalog import FormatCatalog

        return FormatCatalog.snapshot()
