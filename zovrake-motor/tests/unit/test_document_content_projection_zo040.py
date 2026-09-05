from __future__ import annotations

from zovrake_motor.motor_runtime.document_content import (
    _semantic_tables_to_items,
    _tables_to_items,
)


def test_semantic_projection_never_promotes_summary_or_identity_rows_to_items() -> None:
    tables = (
        {
            "table_id": "quote-table",
            "table_role": "commercial_items",
            "columns": [
                {"key": "code"},
                {"key": "description"},
                {"key": "quantity"},
                {"key": "unit"},
                {"key": "unit_price"},
                {"key": "total"},
            ],
            "rows": [
                {
                    "code": "",
                    "description": "Razón Social",
                    "quantity": "INVERSIONES EVZA S.R.L.",
                    "unit": "Cotización N°",
                    "unit_price": "07081-2026",
                    "total": "",
                },
                {
                    "code": "01",
                    "description": "TUBERIA PVC-U UF 110MM, PN5",
                    "quantity": "1",
                    "unit": "UND",
                    "unit_price": "160.00",
                    "total": "160.00",
                },
                {
                    "code": "",
                    "description": "IGV (18%)",
                    "quantity": "993.05",
                    "unit": "",
                    "unit_price": "",
                    "total": "",
                },
                {
                    "code": "",
                    "description": "TOTAL",
                    "quantity": "6510.00",
                    "unit": "",
                    "unit_price": "",
                    "total": "",
                },
            ],
        },
    )

    items = _semantic_tables_to_items(tables)

    assert len(items) == 1
    assert items[0]["code"] == "01" if "code" in items[0] else True
    assert items[0]["description"] == "TUBERIA PVC-U UF 110MM, PN5"


def test_physical_fallback_uses_header_semantics_instead_of_fixed_positions() -> None:
    tables = (
        {
            "table_id": "physical-yiru",
            "rows": (
                (
                    "ITEM",
                    "DESCRIPCIÓN",
                    "UNID.",
                    "CANT.",
                    "S/P. U.",
                    "S/.TOTAL",
                ),
                (
                    "1",
                    "Escalera movil tub. fierro galvanizado 3.2 mm",
                    "UND",
                    "1",
                    "917.00",
                    "917.00",
                ),
                (
                    "2",
                    "Tuberia de f°g°=2\" x 2.5mm",
                    "UND",
                    "1",
                    "149.90",
                    "149.90",
                ),
                (
                    "3",
                    "Angulos de acero 3/4\"x3/4\"x3/16\"",
                    "UND",
                    "1",
                    "120.00",
                    "120.00",
                ),
            ),
        },
    )

    items = _tables_to_items(tables)

    assert len(items) == 3
    assert items[0]["description"].startswith("Escalera movil")
    assert items[0]["quantity"] == "1"
    assert items[0]["unit"] == "UND"
    assert items[0]["unit_price"] == "917.00"
    assert items[1]["quantity"] == "1"
    assert items[1]["unit"] == "UND"
    assert items[1]["unit_price"] == "149.90"
    assert items[2]["quantity"] == "1"
    assert items[2]["unit"] == "UND"
    assert items[2]["unit_price"] == "120.00"


def test_derived_items_table_discovers_only_present_columns_and_preserves_extra_fields() -> None:
    items = (
        {
            "item_id": "i1",
            "description": "Cemento Portland Tipo I",
            "quantity": "100",
            "unit": "BLS",
            "unit_price": "32.00",
            "total": "3200.00",
            "code": "CEM-001",
            "fields": {
                "brand": "Sol",
                "presentacion": "42.5 KG",
            },
        },
        {
            "item_id": "i2",
            "description": "Cemento Portland Tipo I",
            "quantity": "120",
            "unit": "BLS",
            "unit_price": "30.00",
            "total": "3600.00",
            "code": "CEM-002",
            "fields": {
                "brand": "Pacasmayo",
                "norma": "NTP",
            },
        },
    )

    from zovrake_motor.motor_runtime.document_content import _items_to_tables

    table = _items_to_tables(items)[0]
    assert table["semantic_role"] == "commercial_items_projection"
    assert table["columns_discovered"][:6] == [
        "code",
        "description",
        "quantity",
        "unit",
        "unit_price",
        "total",
    ]
    assert "presentacion" in table["columns_discovered"]
    assert "norma" in table["columns_discovered"]
    assert table["rows"][1][1] == "Cemento Portland Tipo I"


def test_comparative_projection_preserves_full_document_boundary() -> None:
    from zovrake_motor.motor_runtime.document_content import _build_comparative_projection

    projection = _build_comparative_projection(
        document_id="DOC-001",
        semantic_tables=(
            {
                "table_id": "t1",
                "table_role": "commercial_items",
                "rows": [{"description": "Cemento", "quantity": "10"}],
            },
            {
                "table_id": "t2",
                "table_role": "banking",
                "rows": [{"account": "123"}],
            },
        ),
        items=(
            {
                "item_id": "item-1",
                "description": "Cemento",
                "quantity": "10",
                "unit": "BLS",
                "unit_price": "32",
                "fields": {"brand": "Sol"},
                "source_kind": "semantic_table",
                "source_table_id": "t1",
                "source_page_number": 1,
            },
        ),
        financial_information={"fact_count": 3},
        provider_resolution={
            "provider_name": "Proveedor S.A.C.",
            "provider_ruc": "20123456789",
            "resolved": True,
            "confidence": 0.95,
        },
    )

    assert projection["projection_version"] == "zo-041-1.0"
    assert projection["commercial_item_count"] == 1
    assert projection["semantic_table_roles"]["banking"] == 1
    assert projection["financial_information"]["fact_count"] == 3
    assert projection["source_information_preserved"] is True
    assert projection["comparison_projection_only"] is True
    assert projection["provider"]["name"] == "Proveedor S.A.C."
