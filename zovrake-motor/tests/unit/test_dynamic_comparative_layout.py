from uuid import uuid4

from zovrake_motor.comparative_tables.comparative_model_builder.layout_composer import compose_comparative_layout


def test_layout_is_dynamic_and_includes_payment_when_available():
    layout = compose_comparative_layout(
        enriched_context={"title": "Comparación de propuestas"},
        structure={"group_type": "products", "commercial_information": {"currency": "PEN"}},
        columns=[
            {"column_id": "c1", "attribute_name": "Descripción", "logical_position": 1, "data_type": "text"},
            {"column_id": "c2", "attribute_name": "Precio Unit.", "logical_position": 2, "data_type": "number"},
        ],
        rows=[{"row_id": "r1", "provider_id": "P1", "logical_position": 1, "column_references": ["c1", "c2"], "table_id": "t1"}],
        providers=[
            {
                "provider_id": "P1",
                "provider_name": "Proveedor A",
                "commercial_information": {"fields": {"Forma de Pago": "Contado", "Validez": "7 días"}},
            },
        ],
        document_ids=("doc-1",),
    )
    assert layout["template_fixed"] is False
    assert layout["mandatory_present_when_available"]["payment_method_or_terms"] is True
    assert "payment_terms" in layout["hierarchy"]["secondary"]
    assert layout["matrix"]["fixed_schema"] is False


def test_layout_does_not_create_absent_payment_section():
    layout = compose_comparative_layout(
        enriched_context={}, structure={"group_type": "service"}, columns=[], rows=[],
        providers=[{"provider_id": "P1", "provider_name": "Proveedor A", "commercial_information": {"fields": {"Garantía": "12 meses"}}}],
        document_ids=(),
    )
    assert layout["mandatory_present_when_available"]["payment_method_or_terms"] is False
    assert "payment_terms" not in [section["section_id"] for section in layout["sections"]]


def test_layout_exposes_provider_payment_and_mp7_decision_area():
    layout = compose_comparative_layout(
        enriched_context={}, structure={"group_type": "material"}, columns=[], rows=[],
        providers=[
            {"provider_id": "D1", "provider_name": "Proveedor A", "commercial_information": {"fields": {"Forma de Pago": "50% adelanto, 50% contraentrega"}}},
            {"provider_id": "D2", "provider_name": "Proveedor B", "commercial_information": {"fields": {"Forma de Pago": "30 días crédito"}}},
        ], document_ids=("D1", "D2"),
    )
    assert len(layout["provider_sections"]) == 2
    assert all(section["has_payment_evidence"] for section in layout["provider_sections"])
    assert all(section["payment_fields"] for section in layout["provider_sections"])
    assert layout["decision_area"]["owner"] == "MP7"
    assert layout["decision_area"]["fixed_content"] is False
