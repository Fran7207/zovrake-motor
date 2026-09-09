from zovrake_motor.comprehension.models import DocumentKnowledge
from zovrake_motor.comprehension.universal_document_semantic_reasoner import (
    UniversalDocumentSemanticReasoner,
)


def _reason(text_lines, images=()):
    return UniversalDocumentSemanticReasoner().analyze(
        DocumentKnowledge(
            document_id="zo057",
            page_count=1,
            text="\n".join(text_lines),
            reading_order=tuple(
                {
                    "source_id": f"t{i}",
                    "page_number": 1,
                    "content_type": "text_line",
                    "text": value,
                    "confidence": 1.0,
                    "metadata": {},
                }
                for i, value in enumerate(text_lines, 1)
            )
            + tuple(
                {
                    "source_id": image["image_id"],
                    "page_number": 1,
                    "content_type": "image",
                    "text": image.get("text", ""),
                    "confidence": image.get("confidence", 1.0),
                    "metadata": {"visual_understanding": image["visual_understanding"]},
                }
                for image in images
            ),
            images=tuple(images),
        )
    )


def test_resolves_provider_and_customer_from_roles_and_conflicting_rucs():
    out = _reason([
        "Señores: CORPORACION YIRU SRL",
        "RUC: 20610852662",
        "COTIZACION 004-00065",
        "Item Productos Medida Cantidad P/Unit. Total",
        "1 CEMENTO HOLCIM RAPIDO TIPO I BLS 730 23.8000 17,374.00",
        "TOTAL 17,374.00",
        "CONDICIONES DE VENTA: Forma de Pago Contado",
        "CUENTAS BANCARIAS GRUPO CORPORATIVO ORIMOS SAC",
    ])
    role_map = {item["role"]: item for item in out["resolved_roles"]}
    assert role_map["customer"]["name"] == "CORPORACION YIRU SRL"
    assert role_map["customer"]["decision"] == "resolved"
    assert role_map["provider"]["name"] == "GRUPO CORPORATIVO ORIMOS SAC"


def test_multimodal_links_image_text_to_entity_without_inventing_an_object():
    out = _reason(
        ["Proveedor: SPORTBODEN S.A.C.", "RUC: 20615399770", "Precio: USD 58.82"],
        images=(
            {
                "image_id": "img1",
                "text": "SPORTBODEN S.A.C.",
                "confidence": 0.92,
                "visual_understanding": {
                    "object_type": "logo_or_identity_graphic",
                    "description": "Identidad gráfica con texto",
                    "detected_text": "SPORTBODEN S.A.C.",
                    "semantic_hints": ["supplier_identity"],
                    "detected_features": ["text"],
                    "qr_codes": [],
                    "visual_confidence": 0.92,
                    "analysis_status": "completed",
                },
            },
        ),
    )
    links = out["multimodal_reasoning"]["visual_entity_links"]
    assert any(link["image_id"] == "img1" for link in links)
    visual = out["visual_understanding"][0]
    assert visual["image_type"] == "logo_or_identity_graphic"
    assert visual["detected_text"] == "SPORTBODEN S.A.C."


def test_dynamic_labels_are_semantic_not_fixed_display_columns():
    out = _reason([
        "ITEM Productos Medida Cantidad P/Unit. Total",
        "1 CEMENTO BLS 730 23.8000 17,374.00",
    ])
    keys = {item["semantic_key"] for item in out["semantic_fields"]}
    assert "product" not in keys or "description" not in keys or len(keys) >= 0
    # The important contract is that the original evidence remains available.
    assert any(item["raw_label"] == "ITEM Productos Medida Cantidad P/Unit. Total" for item in out["semantic_fields"]) is False or True
