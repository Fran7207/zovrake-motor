"""Utilidades compartidas para extractores del CEE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionRequest,
    ExtractedTable,
    ExtractionIncident,
    ExtractorResult,
    StructuralElement,
)


def metadata_value(request: ContentExtractionRequest, key: str, default: Any = None) -> Any:
    if key in request.metadata:
        return request.metadata[key]
    return request.adapter_context.metadata.get(key, default)


def prepared_result(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    observation: str = "Extractor preparado — sin lectura de documento en esta etapa",
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        technical_observations=(observation, "original_preserved=True"),
    )


def result_with_text(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    text: str,
    observation: str,
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        extracted_text=text,
        technical_observations=(observation, "original_preserved=True"),
    )


def result_with_tables(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    tables: tuple[ExtractedTable, ...],
    observation: str,
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        tables=tables,
        technical_observations=(observation, "original_preserved=True"),
    )


def result_with_metadata(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    metadata: dict[str, Any],
    observation: str,
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        metadata=metadata,
        technical_observations=(observation, "original_preserved=True"),
    )


def result_with_elements(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    elements: tuple[StructuralElement, ...],
    observation: str,
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        structural_elements=elements,
        technical_observations=(observation, "original_preserved=True"),
    )


def result_with_incident(
    *,
    extractor_name: str,
    extractor_type: ExtractorType,
    incident: ExtractionIncident,
) -> ExtractorResult:
    return ExtractorResult(
        extractor_name=extractor_name,
        extractor_type=extractor_type.value,
        incidents=(incident,),
        technical_observations=("Incidencia registrada — documento original preservado",),
    )
