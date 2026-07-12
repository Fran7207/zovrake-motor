"""Utilidades compartidas para constructores del IDMB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalTraceability


def model_reference(traceability: InternalTraceability, entity: InternalEntityType) -> str:
    return f"{traceability.model_id}/{entity.value}"


def prepared_entity_result(
    *,
    builder_name: str,
    entity_type: InternalEntityType,
    observation: str = "Constructor preparado — sin interpretación en esta etapa",
) -> EntityBuildResult:
    return EntityBuildResult(
        entity_type=entity_type.value,
        builder_name=builder_name,
        technical_observations=(observation, "traceability_preserved=True"),
    )


def requirement_fields(requirement_context: dict[str, Any] | None) -> dict[str, Any]:
    return dict(requirement_context or {})
