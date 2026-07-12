"""Puerta de acceso exclusiva a la salida del Content Extraction Engine."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.exceptions import ExtractionInputError, TraceabilityError
from zovrake_motor.comprehension.canonical.models import (
    CanonicalRepresentationRequest,
    CanonicalTraceability,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ExtractionResultGateway:
    """
    Garantiza que el CRE reciba exclusivamente la salida del CEE.

    Nunca accede directamente al documento original.
    """

    def validate(self, request: CanonicalRepresentationRequest) -> ContentExtractionResult:
        extraction = request.extraction_result
        if extraction.process_id != request.process_id:
            raise ExtractionInputError("El process_id no coincide con el resultado de extracción")
        if not extraction.document_id:
            raise ExtractionInputError("Resultado de extracción sin document_id")
        if not extraction.adapter_name:
            raise ExtractionInputError("Resultado de extracción sin adaptador documental")
        if not extraction.original_preserved:
            raise TraceabilityError("El documento original no está preservado en la extracción")
        return extraction

    def build_traceability(self, extraction: ContentExtractionResult) -> CanonicalTraceability:
        format_type = str(extraction.metadata.get("format_type", "unknown"))
        document_reference = str(
            extraction.metadata.get(
                "document_reference",
                f"extraction://{extraction.adapter_name}/{extraction.document_id}",
            ),
        )
        return CanonicalTraceability(
            process_id=extraction.process_id,
            document_id=extraction.document_id,
            adapter_name=extraction.adapter_name,
            document_reference=document_reference,
            format_type=format_type,
            extraction_reference_id=f"cee://{extraction.document_id}",
            original_preserved=extraction.original_preserved,
            extraction_extractors_executed=extraction.extractors_executed,
        )
