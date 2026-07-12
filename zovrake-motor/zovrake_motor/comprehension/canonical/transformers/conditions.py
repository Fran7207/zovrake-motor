"""Transformador de la sección Condiciones."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalCondition,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import ConditionsTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ConditionsTransformer(ConditionsTransformerPort):
    """Responsabilidad: transformar condiciones detectadas."""

    @property
    def transformer_name(self) -> str:
        return "conditions_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Condiciones"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.CONDITIONS

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_conditions(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Condiciones transformadas desde elementos estructurales",
        )

    def build_conditions(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalCondition, ...]:
        section_ref = source_reference(traceability.extraction_reference_id, self.section_type)
        conditions: list[CanonicalCondition] = []

        for index, element in enumerate(extraction_result.structural_elements):
            if element.element_type in {"condition", "footer", "terms"}:
                conditions.append(
                    CanonicalCondition(
                        condition_id=f"condition-{index}",
                        content=element.content,
                        source_reference=f"{section_ref}/element/{index}",
                        condition_type=element.element_type,
                        fields=element.metadata,
                    ),
                )

        raw_conditions = metadata_value(extraction_result, "conditions", ())
        if isinstance(raw_conditions, (list, tuple)):
            for index, condition_data in enumerate(raw_conditions):
                if isinstance(condition_data, dict):
                    conditions.append(
                        CanonicalCondition(
                            condition_id=str(condition_data.get("condition_id", f"meta-condition-{index}")),
                            content=str(condition_data.get("content", "")),
                            source_reference=f"{section_ref}/metadata/{index}",
                            condition_type=str(condition_data.get("condition_type", "")),
                            fields=condition_data,
                        ),
                    )

        return tuple(conditions)
