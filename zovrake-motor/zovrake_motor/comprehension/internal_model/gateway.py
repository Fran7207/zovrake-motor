"""Puerta de acceso exclusiva a la Representación Canónica."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.models import CanonicalDocument, CanonicalRepresentationResult
from zovrake_motor.comprehension.internal_model.exceptions import CanonicalInputError, TraceabilityError
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalTraceability


class CanonicalRepresentationGateway:
    """
    Garantiza que el IDMB reciba exclusivamente la Representación Canónica.

    Nunca accede directamente al documento original.
    """

    def validate(self, request: InternalModelBuildRequest) -> CanonicalRepresentationResult:
        canonical = request.canonical_result
        if canonical.process_id != request.process_id:
            raise CanonicalInputError("El process_id no coincide con la representación canónica")
        if not canonical.document_id:
            raise CanonicalInputError("Representación canónica sin document_id")
        representation = canonical.representation
        if not representation.immutable:
            raise CanonicalInputError("La representación canónica no es inmutable")
        if not canonical.original_preserved:
            raise TraceabilityError("El documento original no está preservado en la representación canónica")
        return canonical

    def build_traceability(
        self,
        canonical: CanonicalRepresentationResult,
        *,
        model_id: str,
    ) -> InternalTraceability:
        trace = canonical.representation.traceability
        return InternalTraceability(
            process_id=canonical.process_id,
            document_id=canonical.document_id,
            model_id=model_id,
            canonical_reference_id=f"cre://{canonical.document_id}",
            extraction_reference_id=trace.extraction_reference_id,
            document_reference=trace.document_reference,
            adapter_name=trace.adapter_name,
            format_type=trace.format_type,
            original_preserved=canonical.original_preserved,
        )

    @staticmethod
    def representation(canonical: CanonicalRepresentationResult) -> CanonicalDocument:
        return canonical.representation
