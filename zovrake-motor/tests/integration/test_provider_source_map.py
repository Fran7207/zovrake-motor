"""Pruebas de identidad proveedor ↔ documentos fuente."""

from __future__ import annotations

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)
from zovrake_motor.motor_runtime.document_content import ResolvedDocumentContent


def _document(document_id: str, provider_name: str) -> ResolvedDocumentContent:
    return ResolvedDocumentContent(
        document_id=document_id,
        document_label=document_id,
        content_type="application/pdf",
        file_name=f"{document_id}.pdf",
        provider_name=provider_name,
        text_content="contenido",
        tables=(),
        items=(),
        commercial_currency="PEN",
        commercial_total_amount="100",
        commercial_payment_terms="contado",
        metadata={},
    )


def test_provider_source_map_preserves_provider_identity_and_document_sources() -> None:
    documents = (
        _document("DOC-A", "ABC SAC"),
        _document("DOC-B", "ABC SAC"),
        _document("DOC-C", "XYZ SAC"),
    )

    mapping = CotizacionesAnalysisExecutor._build_provider_source_map(documents)

    assert mapping == [
        {
            "provider_id": "ABC SAC",
            "provider_name": "ABC SAC",
            "document_ids": ["DOC-A", "DOC-B"],
            "document_count": 2,
            "duplicate_document_source": True,
        },
        {
            "provider_id": "XYZ SAC",
            "provider_name": "XYZ SAC",
            "document_ids": ["DOC-C"],
            "document_count": 1,
            "duplicate_document_source": False,
        },
    ]