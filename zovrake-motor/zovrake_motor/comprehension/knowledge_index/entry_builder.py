"""Constructor de entradas del índice documental."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.internal_model.models import InternalDocumentModel, InternalModelBuildResult
from zovrake_motor.comprehension.knowledge_index.enums import IndexEntryStatus
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexEntry, DocumentIndexTraceability


class IndexEntryBuilder:
    """
    Construye entradas uniformes del índice a partir del Modelo Documental Interno.

    No interpreta el contenido ni duplica el modelo completo.
    """

    def build(
        self,
        model_result: InternalModelBuildResult,
        *,
        index_id: str,
        validation_reference: str = "",
        project_id: str = "",
        metadata: dict[str, Any] | None = None,
        reuse_prepared: bool = True,
        query_integration_prepared: bool = True,
    ) -> DocumentIndexEntry:
        model = model_result.model
        trace = model.traceability
        traceability = DocumentIndexTraceability(
            index_id=index_id,
            process_id=trace.process_id,
            document_id=trace.document_id,
            model_id=trace.model_id,
            validation_reference=validation_reference or f"dvf://{trace.document_id}",
            adapter_name=trace.adapter_name,
            canonical_reference_id=trace.canonical_reference_id,
            extraction_reference_id=trace.extraction_reference_id,
            document_reference=trace.document_reference,
            original_preserved=trace.original_preserved,
        )
        query_keys = self._build_query_keys(
            model,
            project_id=project_id,
            metadata=metadata,
        )
        return DocumentIndexEntry(
            index_id=index_id,
            traceability=traceability,
            status=IndexEntryStatus.REGISTERED,
            provider_name=model.provider.name,
            requirement_code=model.requirement_context.requirement_code,
            project_id=project_id,
            model_reference=trace.model_id,
            query_keys=query_keys,
            reuse_prepared=reuse_prepared,
            query_integration_prepared=query_integration_prepared,
            technical_observations=(
                "index_entry_built_from_internal_model=True",
                "traceability_preserved=True",
            ),
        )

    def _build_query_keys(
        self,
        model: InternalDocumentModel,
        *,
        project_id: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, str]:
        keys = {
            "document_id": model.document.document_id,
            "model_id": model.model_id,
            "provider_name": model.provider.name,
            "provider_id": model.provider.provider_id,
            "requirement_code": model.requirement_context.requirement_code,
            "project_id": project_id,
            "format_type": model.traceability.format_type,
            "adapter_name": model.traceability.adapter_name,
        }
        extra = metadata or {}
        for key in ("date", "project", "provider"):
            if key in extra:
                keys[key] = str(extra[key])
        return keys
