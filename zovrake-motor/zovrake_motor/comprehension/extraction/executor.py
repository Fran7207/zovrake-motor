"""Ejecutor de extractores del Content Extraction Engine."""

from __future__ import annotations

from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionRequest,
    ContentExtractionResult,
    ExtractorResult,
)
from zovrake_motor.comprehension.extraction.registry import ExtractorRegistry


class ExtractionExecutor:
    """
    Ejecuta el catálogo de extractores y consolida un resultado uniforme.

    No interpreta el contenido ni modifica el documento original.
    """

    def __init__(self, registry: ExtractorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        request: ContentExtractionRequest,
        *,
        adapter_name: str,
        original_preserved: bool,
        ocr_integration_prepared: bool,
    ) -> ContentExtractionResult:
        extractor_results: list[ExtractorResult] = []
        for extractor in self._registry.all_extractors():
            extractor_results.append(extractor.extract(request))

        extracted_text = "\n".join(
            result.extracted_text for result in extractor_results if result.extracted_text
        )
        tables = tuple(table for result in extractor_results for table in result.tables)
        metadata: dict = {}
        for result in extractor_results:
            metadata.update(result.metadata)
        structural_elements = tuple(
            element for result in extractor_results for element in result.structural_elements
        )
        incidents = tuple(incident for result in extractor_results for incident in result.incidents)
        observations = tuple(
            observation
            for result in extractor_results
            for observation in result.technical_observations
        )

        return ContentExtractionResult(
            process_id=request.process_id,
            document_id=request.document_id,
            extracted_text=extracted_text,
            tables=tables,
            metadata=metadata,
            structural_elements=structural_elements,
            incidents=incidents,
            original_preserved=original_preserved,
            ocr_integration_prepared=ocr_integration_prepared,
            extractors_executed=len(extractor_results),
            adapter_name=adapter_name,
            technical_observations=observations,
        )
