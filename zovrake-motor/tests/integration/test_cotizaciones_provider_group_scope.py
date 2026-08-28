"""Pruebas de aislamiento de proveedores por Grupo Comparable."""

from __future__ import annotations

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)


def _structure(group_id: str, document_id: str) -> dict[str, object]:
    return {
        "table_id": f"CTS-{group_id}",
        "group_id": group_id,
        "metadata_prepared": {
            "available_providers": [f"document://{document_id}"],
        },
        "traceability": {
            "lineage": {
                "document_ids": [document_id],
            },
        },
        "domain_reference": {
            "document_id": document_id,
        },
    }


def test_providers_are_scoped_to_their_comparable_group() -> None:
    structure_catalog = {
        "structures": [
            _structure("GROUP-A", "DOC-A"),
            _structure("GROUP-B", "DOC-B"),
        ],
    }

    provider_source_map = [
        {
            "provider_id": "PROVIDER-A",
            "provider_name": "Proveedor A",
            "document_ids": ["DOC-A"],
        },
        {
            "provider_id": "PROVIDER-B",
            "provider_name": "Proveedor B",
            "document_ids": ["DOC-B"],
        },
    ]

    result = CotizacionesAnalysisExecutor._inject_group_providers(
        structure_catalog,
        provider_source_map=provider_source_map,
    )

    structures = result["structures"]
    assert structures[0]["metadata_prepared"]["available_providers"] == [
        "PROVIDER-A",
    ]
    assert structures[1]["metadata_prepared"]["available_providers"] == [
        "PROVIDER-B",
    ]
    assert structures[0]["metadata_prepared"]["provider_scope"] == "comparable_group"
    assert structures[1]["metadata_prepared"]["provider_scope"] == "comparable_group"


def test_provider_reference_is_resolved_from_document_reference() -> None:
    structure_catalog = {
        "structures": [_structure("GROUP-A", "DOC-A")],
    }

    result = CotizacionesAnalysisExecutor._inject_group_providers(
        structure_catalog,
        provider_source_map=[
            {
                "provider_id": "ABC SAC",
                "provider_name": "ABC SAC",
                "document_ids": ["DOC-A", "DOC-B"],
            },
        ],
    )

    assert result["structures"][0]["metadata_prepared"]["available_providers"] == [
        "ABC SAC",
    ]
