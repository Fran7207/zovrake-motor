"""Constructor de asociaciones contexto-documento."""

from __future__ import annotations

from zovrake_motor.comprehension.context_integration.enums import ContextIntegrationStatus
from zovrake_motor.comprehension.context_integration.models import (
    ContextAssociation,
    ContextTraceability,
    RequirementContextModel,
)
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexResult


class ContextAssociationBuilder:
    """
    Construye asociaciones uniformes entre contexto y modelo documental.

    Nunca modifica la información documental.
    """

    def build(
        self,
        context: RequirementContextModel,
        *,
        model_result: InternalModelBuildResult,
        index_result: DocumentIndexResult,
        requirement_code: str = "",
        classification_prepared: bool = True,
        reasoning_prepared: bool = True,
    ) -> ContextAssociation:
        model = model_result.model
        trace = model.traceability
        index_trace = index_result.entry.traceability
        traceability = ContextTraceability(
            context_id=context.context_id,
            process_id=trace.process_id,
            document_id=trace.document_id,
            model_id=trace.model_id,
            index_id=index_result.index_id,
            canonical_reference_id=trace.canonical_reference_id,
            extraction_reference_id=trace.extraction_reference_id,
            document_reference=trace.document_reference,
            requirement_code=requirement_code or index_result.entry.requirement_code,
            original_preserved=trace.original_preserved,
            document_unmodified=True,
        )
        association_id = f"assoc://{context.context_id}/{index_trace.index_id}"
        return ContextAssociation(
            association_id=association_id,
            traceability=traceability,
            context=context,
            status=ContextIntegrationStatus.INTEGRATED,
            model_reference=trace.model_id,
            index_reference=index_result.index_id,
            classification_prepared=classification_prepared,
            reasoning_prepared=reasoning_prepared,
            technical_observations=(
                "context_integrated_from_detalles_requerimiento=True",
                "document_information_unmodified=True",
                "traceability_preserved=True",
            ),
        )
