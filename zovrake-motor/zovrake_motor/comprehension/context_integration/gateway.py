"""Puerta de acceso exclusiva al contexto del requerimiento."""

from __future__ import annotations

from zovrake_motor.comprehension.context_integration.exceptions import (
    ContextInputError,
    DocumentModelImmutableError,
    TraceabilityError,
)
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexResult

AUTHORIZED_SOURCE_FIELD = "detalles_requerimiento"


class ContextInputGateway:
    """
    Garantiza que el CIE reciba exclusivamente contexto de
    'Detalles del requerimiento' y referencias válidas del pipeline.

    Nunca accede directamente al documento original.
    """

    def validate(self, request: ContextIntegrationRequest) -> ContextIntegrationRequest:
        if not isinstance(request.detalles_requerimiento, str):
            raise ContextInputError(
                "El contexto debe provenir exclusivamente del campo 'Detalles del requerimiento'",
            )
        if request.metadata.get("source_field") not in (None, AUTHORIZED_SOURCE_FIELD):
            raise ContextInputError(
                f"Fuente de contexto no autorizada: {request.metadata.get('source_field')}",
            )
        model_result = request.model_result
        index_result = request.index_result
        if model_result.process_id != request.process_id:
            raise ContextInputError("El process_id no coincide con el modelo documental interno")
        if index_result.process_id != request.process_id:
            raise ContextInputError("El process_id no coincide con el resultado de indexación")
        if model_result.document_id != index_result.document_id:
            raise TraceabilityError("El document_id no coincide entre modelo e índice")
        model = model_result.model
        if not model.immutable:
            raise DocumentModelImmutableError("El modelo documental interno no es inmutable")
        if index_result.entry.traceability.model_id != model.model_id:
            raise TraceabilityError("El model_id no coincide entre modelo e índice")
        if not model_result.original_preserved:
            raise TraceabilityError("El documento original no está preservado en el modelo interno")
        return request

    @staticmethod
    def model_result(request: ContextIntegrationRequest) -> InternalModelBuildResult:
        return request.model_result

    @staticmethod
    def index_result(request: ContextIntegrationRequest) -> DocumentIndexResult:
        return request.index_result
