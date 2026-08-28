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

def test_group_provider_injection_is_scoped_to_group_documents() -> None:
    structure_catalog = {
        "structures": [
            {
                "table_id": "TABLE-1",
                "group_id": "GROUP-1",
                "domain_reference": {"document_id": "DOC-A"},
                "traceability": {
                    "lineage": {
                        "document_id": "DOC-A",
                        "document_ids": ["DOC-A", "DOC-B"],
                    },
                },
                "metadata_prepared": {},
            },
            {
                "table_id": "TABLE-2",
                "group_id": "GROUP-2",
                "domain_reference": {"document_id": "DOC-C"},
                "traceability": {
                    "lineage": {
                        "document_id": "DOC-C",
                        "document_ids": ["DOC-C", "DOC-D"],
                    },
                },
                "metadata_prepared": {},
            },
        ],
    }

    provider_source_map = [
        {
            "provider_id": "PROVIDER-A",
            "provider_name": "PROVIDER-A",
            "document_ids": ["DOC-A"],
            "document_count": 1,
            "duplicate_document_source": False,
        },
        {
            "provider_id": "PROVIDER-B",
            "provider_name": "PROVIDER-B",
            "document_ids": ["DOC-B"],
            "document_count": 1,
            "duplicate_document_source": False,
        },
        {
            "provider_id": "PROVIDER-C",
            "provider_name": "PROVIDER-C",
            "document_ids": ["DOC-C"],
            "document_count": 1,
            "duplicate_document_source": False,
        },
        {
            "provider_id": "PROVIDER-D",
            "provider_name": "PROVIDER-D",
            "document_ids": ["DOC-D"],
            "document_count": 1,
            "duplicate_document_source": False,
        },
    ]

    result = CotizacionesAnalysisExecutor._inject_group_providers(
        structure_catalog,
        provider_source_map=provider_source_map,
    )

    assert result["structures"][0]["metadata_prepared"]["available_providers"] == [
        "PROVIDER-A",
        "PROVIDER-B",
    ]
    assert result["structures"][1]["metadata_prepared"]["available_providers"] == [
        "PROVIDER-C",
        "PROVIDER-D",
    ]


def test_group_provider_injection_deduplicates_same_provider_across_documents() -> None:
    structure_catalog = {
        "structures": [
            {
                "table_id": "TABLE-1",
                "group_id": "GROUP-1",
                "domain_reference": {"document_id": "DOC-A"},
                "traceability": {
                    "lineage": {
                        "document_id": "DOC-A",
                        "document_ids": ["DOC-A", "DOC-B"],
                    },
                },
                "metadata_prepared": {},
            },
        ],
    }

    provider_source_map = [
        {
            "provider_id": "PROVIDER-A",
            "provider_name": "PROVIDER-A",
            "document_ids": ["DOC-A", "DOC-B"],
            "document_count": 2,
            "duplicate_document_source": True,
        },
    ]

    result = CotizacionesAnalysisExecutor._inject_group_providers(
        structure_catalog,
        provider_source_map=provider_source_map,
    )

    assert result["structures"][0]["metadata_prepared"]["available_providers"] == [
        "PROVIDER-A",
    ]
