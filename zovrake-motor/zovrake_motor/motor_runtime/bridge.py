"""Puente de invocación del Motor — inyectable en MotorUnitGateway sin romper PM8."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.motor_runtime.cotizaciones_executor import CotizacionesAnalysisExecutor
from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry


class MotorExecutionBridge:
    """
    Adaptador invocado por ``MotorUnitGateway``.

    No pertenece a ``enterprise_integration``; evita importaciones prohibidas
    desde el módulo de integración empresarial.
    """

    def __init__(
        self,
        *,
        executor: CotizacionesAnalysisExecutor,
        result_registry: AnalysisResultRegistry,
    ) -> None:
        self._executor = executor
        self._registry = result_registry

    @property
    def result_registry(self) -> AnalysisResultRegistry:
        return self._registry

    def __call__(
        self,
        *,
        process_id: UUID,
        codigo_req: str,
        operation: str,
        document_ids: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = dict(metadata or {})
        evidence_documents = self._extract_evidence_documents(metadata, document_ids)
        requirement_description = str(
            metadata.get("requirement_description")
            or ((metadata.get("analysis_metadata") or {}).get("requirement_description"))
            or ""
        )
        if not evidence_documents:
            return {
                "invoked": False,
                "prepared": True,
                "executed": False,
                "process_id": str(process_id),
                "codigo_req": codigo_req,
                "operation": operation,
                "message": "Invocación preparada — sin documentos de evidencia disponibles",
                "executes_intelligent_analysis": False,
            }

        stored = self._executor.execute(
            process_id=process_id,
            codigo_req=codigo_req,
            evidence_documents=evidence_documents,
            requirement_description=requirement_description,
            metadata=metadata,
        )
        return {
            "invoked": True,
            "prepared": True,
            "executed": True,
            "process_id": str(process_id),
            "codigo_req": codigo_req,
            "operation": operation,
            "catalog_id": stored.catalog_id,
            "message": stored.message,
            "executes_intelligent_analysis": True,
            "accesses_motor_internals": False,
            "documents_processed": len(stored.documents_processed),
        }

    @staticmethod
    def _extract_evidence_documents(
        metadata: dict[str, Any],
        document_ids: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        documents = metadata.get("evidence_documents")
        if isinstance(documents, list) and documents:
            return [dict(doc) for doc in documents if isinstance(doc, dict)]

        analysis_metadata = metadata.get("analysis_metadata")
        if isinstance(analysis_metadata, dict):
            nested = analysis_metadata.get("evidence_documents")
            if isinstance(nested, list) and nested:
                return [dict(doc) for doc in nested if isinstance(doc, dict)]

        # Fallback mínimo: identidades sin contenido.
        return [
            {
                "document_id": document_id,
                "document_label": document_id,
                "content_type": "application/pdf",
                "metadata": {"file_name": document_id, "content_data_url": ""},
            }
            for document_id in document_ids
        ]
