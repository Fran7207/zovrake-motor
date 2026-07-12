"""Puerta de acceso exclusiva a Modelos Documentales Internos."""

from __future__ import annotations

from zovrake_motor.comprehension.internal_model.models import InternalDocumentModel, InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.exceptions import InternalModelInputError, TraceabilityError
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest


class InternalModelGateway:
    """
    Garantiza que el DKI reciba exclusivamente Modelos Documentales Internos.

    Nunca accede directamente al documento original.
    """

    def validate(self, request: DocumentIndexRequest) -> InternalModelBuildResult:
        model_result = request.model_result
        if model_result.process_id != request.process_id:
            raise InternalModelInputError("El process_id no coincide con el modelo documental interno")
        if not model_result.document_id:
            raise InternalModelInputError("Modelo documental interno sin document_id")
        model = model_result.model
        if not model.immutable:
            raise InternalModelInputError("El modelo documental interno no es inmutable")
        if not model_result.original_preserved:
            raise TraceabilityError("El documento original no está preservado en el modelo interno")
        return model_result

    @staticmethod
    def model(model_result: InternalModelBuildResult) -> InternalDocumentModel:
        return model_result.model
