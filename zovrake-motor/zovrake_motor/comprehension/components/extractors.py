"""Extractores — integración con el Content Extraction Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.extraction.engine import ContentExtractionEngine
from zovrake_motor.comprehension.extraction.integration import ExtractionMotorIntegration
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ContentExtractionResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ExtractorsRegistry(ComprehensionComponentPort):
    """
    Gestor del Content Extraction Engine (CEE).

    Responsabilidad única: coordinar la extracción estructural del contenido
    documental recibido exclusivamente a través del adaptador documental.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ContentExtractionEngine | None = None,
    ) -> None:
        self._engine = engine or ContentExtractionEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "extractors"

    @property
    def component_label(self) -> str:
        return "Extractores"

    @property
    def engine(self) -> ContentExtractionEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def extract(
        self,
        request: ContentExtractionRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ContentExtractionResult:
        if integration is not None and record_traceability:
            bridge = ExtractionMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_extraction(
                request.process_id,
                document_id=request.document_id,
                adapter_name=request.adapter_context.adapter_name,
            )

        result = self._engine.extract(request)

        if integration is not None and record_traceability:
            bridge = ExtractionMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_extraction(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
