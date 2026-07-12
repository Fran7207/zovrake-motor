"""Constructor del modelo uniforme de contexto."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.context_integration.gateway import AUTHORIZED_SOURCE_FIELD
from zovrake_motor.comprehension.context_integration.models import RequirementContextModel


class RequirementContextBuilder:
    """
    Construye el modelo uniforme de contexto a partir de
    'Detalles del requerimiento' sin interpretar el contenido.
    """

    def build(
        self,
        detalles_requerimiento: str,
        *,
        process_id: UUID,
        document_id: str,
        requirement_code: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RequirementContextModel:
        context_id = f"ctx://{process_id}/{document_id}"
        structural_metadata = {
            "source_field": AUTHORIZED_SOURCE_FIELD,
            "content_length": len(detalles_requerimiento),
            "process_id": str(process_id),
            "document_id": document_id,
            "requirement_code": requirement_code,
            **(metadata or {}),
        }
        return RequirementContextModel(
            context_id=context_id,
            description=detalles_requerimiento,
            observations=(),
            priorities=(),
            restrictions=(),
            additional_notes=(),
            metadata=structural_metadata,
            immutable=True,
        )
