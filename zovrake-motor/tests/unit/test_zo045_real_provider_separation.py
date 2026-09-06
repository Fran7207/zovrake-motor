from zovrake_motor.motor_runtime.cotizaciones_executor import CotizacionesAnalysisExecutor


def test_legacy_duplicate_guard_does_not_fabricate_second_concept():
    catalog = {
        "concepts": [
            {"normalized_concept_id": "concept-a"},
        ],
    }
    result = CotizacionesAnalysisExecutor._ensure_comparable_duplicate(catalog)
    assert len(result["concepts"]) == 1
    assert result["concepts"][0]["normalized_concept_id"] == "concept-a"


def test_seed_items_preserves_real_document_provider_and_item_identity():
    catalog = {"concepts": []}
    internal_model = {
        "document_id": "DOC-001",
        "provider_name": "PROVEEDOR REAL SAC",
        "items": [
            {
                "item_id": "ITEM-009",
                "description": "Cemento Portland Tipo I",
                "quantity": "100",
                "unit": "BLS",
                "unit_price": "30.00",
                "total": "3000.00",
                "code": "CEM-01",
                "fields": {"marca": "Marca A"},
            },
        ],
    }

    result = CotizacionesAnalysisExecutor._seed_concepts_from_items(
        catalog,
        internal_model,
    )

    concept = result["concepts"][0]
    assert concept["concept_id"] == "seed://DOC-001/ITEM-009"
    assert concept["traceability"]["document_id"] == "DOC-001"
    assert concept["traceability"]["source_item_id"] == "ITEM-009"
    assert concept["traceability"]["provider_name"] == "PROVEEDOR REAL SAC"
    assert concept["metadata"]["quantity"] == "100"
    assert concept["metadata"]["unit"] == "BLS"
    assert concept["metadata"]["unit_price"] == "30.00"
    assert concept["metadata"]["fields"]["marca"] == "Marca A"
