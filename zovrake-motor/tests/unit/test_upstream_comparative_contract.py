from __future__ import annotations

import base64
from pathlib import Path

from zovrake_motor.comprehension.document_entity_resolver import DocumentEntityResolver
from zovrake_motor.motor_runtime.document_content import resolve_evidence_documents


def test_provider_resolution_uses_visual_header_plus_business_email() -> None:
    # Se prueba la regla general con una evidencia visual degradada, sin
    # mencionar una empresa concreta en la lógica del resolver.
    from zovrake_motor.comprehension.models import DocumentKnowledge

    knowledge = DocumentKnowledge(
        document_id="generic-commercial",
        file_name="generic.pdf",
        content_type="application/pdf",
        page_count=1,
        text=(
            "RUC: 20123456789\n"
            "COTIZACION N° 1\n"
            "EMPRESA: CLIENTE DEMO SAC\n"
            "RUC 20987654321\n"
            "MAIL: corporacionacme1@example.com"
        ),
        visual_text="CORPORACION ACME",
        images=(
            {
                "image_id": "header-logo",
                "page_number": 1,
                "bbox": [10, 10, 100, 50],
                "ocr_text": "CORPORACION ACME",
                "visual_understanding": {"detected_text": "CORPORACION ACME"},
            },
        ),
    )

    resolved = DocumentEntityResolver().resolve(knowledge)
    assert any(
        entity.role == "provider"
        and entity.name == "CORPORACION ACME"
        and entity.identifier == "20123456789"
        for entity in resolved.entities
    )


def test_real_pdf_reaches_comparative_contract_exactly() -> None:
    pdf = Path("/mnt/data/COTIZACION CEMENTO.pdf")
    if not pdf.exists():
        return

    raw = base64.b64encode(pdf.read_bytes()).decode()
    resolved = resolve_evidence_documents(
        [
            {
                "document_id": "doc-real",
                "document_label": pdf.name,
                "content_type": "application/pdf",
                "metadata": {
                    "file_name": pdf.name,
                    "content_data_url": raw,
                },
            }
        ]
    )[0]

    assert resolved.provider_name == "CORPORACION YIRU"
    assert resolved.metadata["provider_ruc"] == "20610852662"
    assert resolved.commercial_currency == "PEN"
    assert resolved.commercial_total_amount == "21,000.00"

    assert len(resolved.items) == 1
    item = resolved.items[0]
    assert item["description"] == "CEMENTO HOLCIM TIPO I"
    assert item["quantity"] == "750.00"
    assert item["unit"] == "BOLSA"
    assert item["unit_price"] == "28.00"
    assert item["total"] == "21,000.00"

    financial = resolved.metadata["comparative_projection"]["financial_summary"]
    assert financial["subtotal"]["value"] == "17,796.61"
    assert financial["tax"]["value"] == "3,203.39"
    assert financial["total"]["value"] == "21,000.00"
    assert financial["currency"] == "PEN"
