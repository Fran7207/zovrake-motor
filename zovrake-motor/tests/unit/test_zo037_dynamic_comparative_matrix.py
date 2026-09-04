from __future__ import annotations

from types import SimpleNamespace

from zovrake_motor.motor_runtime.cotizaciones_executor import (
    CotizacionesAnalysisExecutor,
)


def _document(document_id: str, provider_name: str, item_id: str, description: str, price: str):
    return SimpleNamespace(
        document_id=document_id,
        document_label=f"{document_id}.pdf",
        file_name=f"{document_id}.pdf",
        provider_name=provider_name,
        commercial_currency="PEN",
        commercial_total_amount=price,
        commercial_payment_terms="Contado",
        items=(
            {
                "item_id": item_id,
                "description": description,
                "quantity": "10",
                "unit": "BLS",
                "unit_price": price,
                "fields": {"marca": provider_name},
            },
        ),
    )


def _model(provider_rows):
    columns = (
        {
            "column_id": "col-description",
            "attribute_name": "description",
            "display_name": "Descripción",
            "data_type": "string",
            "traceability": {"attribute_source": "source_item"},
            "logical_position": 1,
        },
        {
            "column_id": "col-quantity",
            "attribute_name": "quantity",
            "display_name": "Cantidad",
            "data_type": "string",
            "traceability": {"attribute_source": "source_item"},
            "logical_position": 2,
        },
        {
            "column_id": "col-unit",
            "attribute_name": "unit",
            "display_name": "Unidad",
            "data_type": "string",
            "traceability": {"attribute_source": "source_item"},
            "logical_position": 3,
        },
        {
            "column_id": "col-price",
            "attribute_name": "unit_price",
            "display_name": "Precio Unitario",
            "data_type": "string",
            "traceability": {"attribute_source": "source_item"},
            "logical_position": 4,
        },
    )

    rows = []
    for index, provider in enumerate(provider_rows, start=1):
        rows.append(
            {
                "provider_id": provider["provider_id"],
                "row_id": f"row-{index}",
                "cells_reserved": [
                    {
                        "column_id": "col-description",
                        "value": provider["description"],
                        "value_prepared": True,
                    },
                    {
                        "column_id": "col-quantity",
                        "value": provider["quantity"],
                        "value_prepared": True,
                    },
                    {
                        "column_id": "col-unit",
                        "value": provider["unit"],
                        "value_prepared": True,
                    },
                    {
                        "column_id": "col-price",
                        "value": provider["price"],
                        "value_prepared": True,
                    },
                ],
                "metadata": {
                    "provider_name": provider["provider_name"],
                    "provider_source_document_ids": [provider["document_id"]],
                    "source_item_id": provider["item_id"],
                },
            }
        )

    return {
        "definitive_model_id": "CMD-001",
        "comparative_table_id": "CMP-001",
        "group_id": "GRP-001",
        "group_type": "material",
        "dynamic_columns": list(columns),
        "dynamic_rows": rows,
        "document_ids": [p["document_id"] for p in provider_rows],
        "metadata": {
            "provider_source_map": [
                {
                    "provider_id": p["provider_id"],
                    "provider_name": p["provider_name"],
                    "document_ids": [p["document_id"]],
                }
                for p in provider_rows
            ],
            "semantic_knowledge": {
                "semantic_knowledge_available": True,
            },
        },
        "commercial_information": {},
        "technical_information": {},
        "traceability": {},
        "source_data_preserved": True,
    }


def test_matrix_is_ready_for_two_distinct_providers_and_binds_exact_items() -> None:
    documents = (
        _document("DOC-A", "Proveedor A", "ITEM-A", "Cemento Portland Tipo I", "20"),
        _document("DOC-B", "Proveedor B", "ITEM-B", "Cemento Portland Tipo I", "18"),
    )

    model = _model(
        [
            {
                "provider_id": "DOC-A",
                "provider_name": "Proveedor A",
                "document_id": "DOC-A",
                "item_id": "ITEM-A",
                "description": "Cemento Portland Tipo I",
                "quantity": "10",
                "unit": "BLS",
                "price": "20",
            },
            {
                "provider_id": "DOC-B",
                "provider_name": "Proveedor B",
                "document_id": "DOC-B",
                "item_id": "ITEM-B",
                "description": "Cemento Portland Tipo I",
                "quantity": "10",
                "unit": "BLS",
                "price": "18",
            },
        ]
    )

    payload = CotizacionesAnalysisExecutor._enrich_comparative_payload(
        definitive_catalog={"models": [model]},
        documents=documents,
    )

    assert payload["comparison_ready"] is True
    assert payload["comparison_count"] == 1
    assert payload["pending_group_count"] == 0

    matrix = payload["matrices"][0]
    assert matrix["comparison_status"] == "ready"
    assert matrix["provider_count"] == 2
    assert matrix["source_bindings_complete"] is True
    assert matrix["header"] == [
        "Descripción",
        "Cantidad",
        "Unidad",
        "Precio Unitario",
    ]

    assert matrix["rows"][0]["provider_name"] == "Proveedor A"
    assert matrix["rows"][0]["source_item_id"] == "ITEM-A"
    assert matrix["rows"][0]["source_item"]["description"] == "Cemento Portland Tipo I"
    assert matrix["rows"][0]["values"] == [
        "Cemento Portland Tipo I",
        "10",
        "BLS",
        "20",
    ]

    assert matrix["rows"][1]["provider_name"] == "Proveedor B"
    assert matrix["rows"][1]["source_item_id"] == "ITEM-B"
    assert matrix["rows"][1]["values"] == [
        "Cemento Portland Tipo I",
        "10",
        "BLS",
        "18",
    ]


def test_single_provider_group_is_pending_not_a_comparison() -> None:
    documents = (
        _document("DOC-A", "Proveedor A", "ITEM-A", "Cemento Portland Tipo I", "20"),
    )
    model = _model(
        [
            {
                "provider_id": "DOC-A",
                "provider_name": "Proveedor A",
                "document_id": "DOC-A",
                "item_id": "ITEM-A",
                "description": "Cemento Portland Tipo I",
                "quantity": "10",
                "unit": "BLS",
                "price": "20",
            },
        ]
    )

    payload = CotizacionesAnalysisExecutor._enrich_comparative_payload(
        definitive_catalog={"models": [model]},
        documents=documents,
    )

    assert payload["comparison_ready"] is False
    assert payload["comparison_count"] == 0
    assert payload["pending_group_count"] == 1
    assert payload["pending_groups"][0]["comparison_status"] == "pending_single_provider"


def test_provider_id_is_not_used_as_visible_name_when_real_name_exists() -> None:
    documents = (
        _document("DOC-A", "Proveedor Real SAC", "ITEM-A", "Cemento Portland Tipo I", "20"),
        _document("DOC-B", "Proveedor B SAC", "ITEM-B", "Cemento Portland Tipo I", "18"),
    )
    model = _model(
        [
            {
                "provider_id": "DOC-A",
                "provider_name": "",
                "document_id": "DOC-A",
                "item_id": "ITEM-A",
                "description": "Cemento Portland Tipo I",
                "quantity": "10",
                "unit": "BLS",
                "price": "20",
            },
            {
                "provider_id": "DOC-B",
                "provider_name": "Proveedor B SAC",
                "document_id": "DOC-B",
                "item_id": "ITEM-B",
                "description": "Cemento Portland Tipo I",
                "quantity": "10",
                "unit": "BLS",
                "price": "18",
            },
        ]
    )
    model["metadata"]["provider_source_map"][0]["provider_name"] = "Proveedor Real SAC"

    payload = CotizacionesAnalysisExecutor._enrich_comparative_payload(
        definitive_catalog={"models": [model]},
        documents=documents,
    )

    names = [row["provider_name"] for row in payload["matrices"][0]["rows"]]
    assert names == ["Proveedor Real SAC", "Proveedor B SAC"]
