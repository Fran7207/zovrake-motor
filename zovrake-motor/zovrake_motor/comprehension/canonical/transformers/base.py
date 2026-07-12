"""Utilidades compartidas para transformadores del CRE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import SectionTransformationResult
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


def metadata_value(extraction: ContentExtractionResult, key: str, default: Any = None) -> Any:
    return extraction.metadata.get(key, default)


def source_reference(traceability_id: str, section: CanonicalSectionType) -> str:
    return f"{traceability_id}/{section.value}"


def prepared_section_result(
    *,
    transformer_name: str,
    section_type: CanonicalSectionType,
    observation: str = "Transformador preparado — sin interpretación en esta etapa",
) -> SectionTransformationResult:
    return SectionTransformationResult(
        section_type=section_type.value,
        transformer_name=transformer_name,
        technical_observations=(observation, "traceability_preserved=True"),
    )
