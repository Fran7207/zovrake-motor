"""Puerta de acceso al documento exclusivamente vía adaptador documental."""

from __future__ import annotations

from zovrake_motor.comprehension.extraction.exceptions import AdapterAccessError, OriginalDocumentModifiedError
from zovrake_motor.comprehension.extraction.models import AdapterDocumentContext, ContentExtractionRequest


class AdapterDocumentGateway:
    """
    Garantiza que el CEE reciba el documento únicamente a través del adaptador.

    Nunca accede directamente al documento original.
    """

    def validate(self, request: ContentExtractionRequest) -> AdapterDocumentContext:
        context = request.adapter_context
        if not context.adapter_name:
            raise AdapterAccessError("El documento debe provenir de un adaptador documental")
        if not context.document_reference:
            raise AdapterAccessError("Referencia del adaptador documental no proporcionada")
        if not context.original_preserved:
            raise OriginalDocumentModifiedError("El documento original no está preservado")
        return context
