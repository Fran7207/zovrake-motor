"""Motor central de Extracción de Contenido (CEE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.extraction.adapter_gateway import (
    AdapterDocumentGateway,
)
from zovrake_motor.comprehension.extraction.executor import ExtractionExecutor
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionRequest,
    ContentExtractionResult,
)
from zovrake_motor.comprehension.extraction.ocr_hook import OcrIntegrationPoint
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort
from zovrake_motor.comprehension.extraction.registry import ExtractorRegistry
from zovrake_motor.config.categories.comprehension import DocumentExtractionSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ContentExtractionEngine:
    """
    Content Extraction Engine (CEE).

    Coordina la extracción estructural del contenido documental.
    El resto del Motor nunca extrae contenido directamente.
    """

    EXPECTED_EXTRACTOR_COUNT = 8

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ExtractorRegistry | None = None,
        gateway: AdapterDocumentGateway | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ExtractorRegistry()
        self._gateway = gateway or AdapterDocumentGateway()
        self._executor: ExtractionExecutor | None = None
        self._ocr_hook: OcrIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ExtractorRegistry:
        return self._registry

    @property
    def executor(self) -> ExtractionExecutor:
        if self._executor is None:
            self._executor = ExtractionExecutor(self._registry)
        return self._executor

    @property
    def ocr_integration(self) -> OcrIntegrationPoint:
        if self._ocr_hook is None:
            self._ocr_hook = OcrIntegrationPoint(
                settings=self._extraction_settings()
            )
        return self._ocr_hook

    def is_ready(self) -> bool:
        return (
            self._initialized
            and self._registry.count() >= self.EXPECTED_EXTRACTOR_COUNT
        )

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults(
                settings=self._extraction_settings()
            )

        self._executor = ExtractionExecutor(self._registry)
        self._ocr_hook = OcrIntegrationPoint(
            settings=self._extraction_settings()
        )
        self._initialized = True

    def extract(
        self,
        request: ContentExtractionRequest,
    ) -> ContentExtractionResult:
        context = self._gateway.validate(request)

        ocr_status = (
            self.ocr_integration.prepare_for_future_execution()
        )

        result = self.executor.execute(
            request,
            adapter_name=context.adapter_name,
            original_preserved=context.original_preserved,
            ocr_integration_prepared=self.ocr_integration.is_prepared,
        )

        observations = (
            *result.technical_observations,
            f"ocr_status={ocr_status['status']}",
            "document_original_unmodified=True",
        )

        semantic_tables = context.metadata.get(
            "semantic_tables",
            (),
        )

        if isinstance(semantic_tables, (list, tuple)):
            normalized_semantic_tables = tuple(
                table
                for table in semantic_tables
                if isinstance(table, dict)
            )
        else:
            normalized_semantic_tables = ()

        return ContentExtractionResult(
            process_id=result.process_id,
            document_id=result.document_id,
            extracted_text=result.extracted_text,
            tables=result.tables,
            metadata={
                **result.metadata,
                "ocr_preparation": ocr_status,
                "semantic_tables": normalized_semantic_tables,
            },
            structural_elements=result.structural_elements,
            incidents=result.incidents,
            original_preserved=result.original_preserved,
            ocr_integration_prepared=result.ocr_integration_prepared,
            extractors_executed=result.extractors_executed,
            adapter_name=result.adapter_name,
            technical_observations=observations,
        )

    def extend(self, extractor: ContentExtractorPort) -> None:
        """Incorpora un nuevo extractor mediante extensión sin modificar el núcleo."""
        self._registry.register(extractor)

    def _extraction_settings(self) -> DocumentExtractionSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().extraction

        return DocumentExtractionSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._extraction_settings()

        return {
            "initialized": self._initialized,
            "extractors_count": self._registry.count(),
            "extractors": self._registry.snapshot(),
            "ocr_integration": self.ocr_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_original": settings.preserve_original,
                "ocr_integration_prepared": (
                    settings.ocr_integration_prepared
                ),
                "ocr_enabled": settings.ocr_enabled,
            },
        }