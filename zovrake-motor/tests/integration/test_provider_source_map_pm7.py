"""Prueba PM7: provider_source_map llega al modelo definitivo."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)
from zovrake_motor.motor_runtime.document_content import ResolvedDocumentContent


@dataclass(frozen=True)
class _Doc:
    document_id: str
    provider_name: str


def test_provider_source_map_is_embedded_in_pm7_catalog() -> None:
    definitive_catalog = {
        "catalog_id": "cmb-catalog://test",
        "models": [
            {
                "definitive_model_id": "MD-001",
                "metadata": {},
                "dynamic_rows": [
                    {
                        "provider_id": "ABC SAC",
                        "metadata": {},
                    }
                ],
            }
        ],
    }

    source_map = [
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

    result = CotizacionesAnalysisExecutor._inject_provider_source_map_into_definitive_catalog(
        definitive_catalog=definitive_catalog,
        provider_source_map=source_map,
    )

    assert result["provider_source_map_count"] == 2
    assert result["provider_source_map"] == source_map

    model = result["models"][0]
    assert model["metadata"]["provider_source_map"] == source_map

    row = model["dynamic_rows"][0]
    assert row["metadata"]["provider_source_document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]
    assert row["metadata"]["provider_source_document_count"] == 2
    assert row["metadata"]["provider_source_ambiguous"] is True


def test_provider_source_map_does_not_create_duplicate_provider_ids() -> None:
    source_map = [
        {
            "provider_id": "ABC SAC",
            "provider_name": "ABC SAC",
            "document_ids": ["DOC-A", "DOC-B"],
        },
        {
            "provider_id": "ABC SAC",
            "provider_name": "ABC SAC",
            "document_ids": ["DOC-C"],
        },
    ]

    result = CotizacionesAnalysisExecutor._inject_provider_source_map_into_definitive_catalog(
        definitive_catalog={"models": []},
        provider_source_map=source_map,
    )

    assert result["provider_source_map_count"] == 1
    assert result["provider_source_map"][0]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]