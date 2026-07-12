"""Constructor de la entidad Ítems."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalItemEntity, InternalTraceability
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class ItemsEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir las entidades Ítem."""

    @property
    def builder_name(self) -> str:
        return "items_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Ítems"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.ITEMS

    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        self.build_entities(representation, traceability=traceability)
        return prepared_entity_result(builder_name=self.builder_name, entity_type=self.entity_type)

    def build_entities(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> tuple[InternalItemEntity, ...]:
        items: list[InternalItemEntity] = []
        for item in representation.items:
            items.append(
                InternalItemEntity(
                    entity_id=f"item-{item.item_id}",
                    item_id=item.item_id,
                    document_id=traceability.document_id,
                    description=item.description,
                    canonical_reference=item.source_reference,
                    extraction_reference=traceability.extraction_reference_id,
                    source_reference=f"{model_reference(traceability, self.entity_type)}/{item.item_id}",
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    unit=item.unit,
                    fields=item.fields,
                ),
            )
        return tuple(items)
