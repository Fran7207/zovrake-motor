"""Prueba del contrato PM6 → PM7 para identidad multi-documento."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogGateway,
)


def test_pm6_catalog_preserves_document_ids_for_pm7() -> None:
    process_id = uuid4()
    catalog = {
        "catalog_id": "cmb-catalog://collective",
        "process_id": str(process_id),
        "model_id": "collective-model",
        "document_id": "DOC-A",
        "document_ids": ["DOC-A", "DOC-B"],
        "pm6_definitive_output_contract": True,
        "pm7_input_contract_prepared": True,
        "source_data_preserved": True,
        "models": [
            {
                "definitive_model_id": "MD-001",
                "comparative_table_id": "TAB-001",
                "group_id": "GRP-001",
                "group_type": "material",
                "dynamic_columns": [],
                "dynamic_rows": [],
                "provider_organization": [],
                "commercial_information": {"fields": {}, "provider_fields": []},
                "technical_information": {"fields": {}, "specifications": [], "provider_fields": []},
                "inherited_context": {},
                "confidence_level_available": "high",
                "metadata": {},
                "traceability": {"document_ids": ["DOC-A", "DOC-B"]},
                "motor_internal_references": {},
                "integrity_status": "valid",
                "source_data_preserved": True,
            }
        ],
    }

    view = DefinitiveComparativeModelCatalogGateway().validate(catalog)

    assert view.document_ids == ("DOC-A", "DOC-B")
    assert view.models[0].traceability["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]