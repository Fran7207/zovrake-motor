from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from zovrake_motor.classification.comparable_group_builder.builders import (
    build_comparable_group_record,
)
from zovrake_motor.classification.comparable_group_builder.gateway import (
    EquivalenceCatalogGateway,
)
from zovrake_motor.classification.comparable_group_builder.builders_strategies import (
    EquivalenceClusterGroupBuilder,
)
from zovrake_motor.classification.equivalence_detection.enums import EquivalenceRelationType
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings
from zovrake_motor.motor_runtime.cotizaciones_executor import CotizacionesAnalysisExecutor


def _raw_relation(process_id: str, *, left: str, right: str, left_doc: str, right_doc: str, relation_type: str = "comparable") -> dict:
    return {
        "equivalence_id": "EQ-001",
        "involved_concept_ids": [left, right],
        "relation_type": relation_type,
        "evidence_level": "medium",
        "status": "detected",
        "detector_type": "semantic_similarity",
        "explainability": {
            "criteria_used": [],
            "information_used": [],
            "limitations": [],
            "rationale": "test",
        },
        "traceability": {
            "process_id": process_id,
            "document_id": left_doc,
            "document_ids": [left_doc, right_doc],
            "model_id": "collective-model",
            "source_normalized_catalog_id": "cne://collective",
            "concept_ids": [left, right],
            "document_reference": f"document://{left_doc}",
            "canonical_reference": "canonical://collective",
            "original_preserved": True,
        },
        "metadata": {
            "shared_concept_type": "material",
            "semantic_comparable_candidate": True,
            "concept_source_map": {
                left: {
                    "concept_id": left,
                    "document_id": left_doc,
                    "document_reference": f"document://{left_doc}",
                    "source_record_id": "src-left",
                    "original_value": "cemento portland tipo i",
                    "normalized_value": "cemento portland tipo i",
                    "item_id": "item-left",
                    "quantity": "10",
                    "unit": "BLS",
                    "unit_price": "20",
                    "fields": {"marca": "A"},
                },
                right: {
                    "concept_id": right,
                    "document_id": right_doc,
                    "document_reference": f"document://{right_doc}",
                    "source_record_id": "src-right",
                    "original_value": "cemento portland tipo i",
                    "normalized_value": "cemento portland tipo i",
                    "item_id": "item-right",
                    "quantity": "12",
                    "unit": "BLS",
                    "unit_price": "18",
                    "fields": {"marca": "B"},
                },
            },
        },
    }


def test_comparable_relation_creates_group_and_preserves_item_sources() -> None:
    process_id = uuid4()
    raw = {
        "catalog_id": "eq://collective",
        "process_id": str(process_id),
        "model_id": "collective-model",
        "document_id": "multi-document://x",
        "document_ids": ["DOC-A", "DOC-B"],
        "source_normalized_catalog_id": "cne://collective",
        "equivalences": [
            _raw_relation(
                str(process_id),
                left="CONCEPT-A",
                right="CONCEPT-B",
                left_doc="DOC-A",
                right_doc="DOC-B",
            )
        ],
        "comparable_group_builder_prepared": True,
    }

    view = EquivalenceCatalogGateway().validate(raw)
    assert len(view.comparable_relations) == 1
    assert view.comparable_relations[0].relation_type == EquivalenceRelationType.COMPARABLE.value

    result = EquivalenceClusterGroupBuilder().build(
        view,
        settings=ComparableGroupBuilderSettings.default(),
        start_sequence=1,
    )

    assert len(result.groups) == 1
    source_map = result.groups[0].metadata["concept_source_map"]
    assert source_map["CONCEPT-A"]["document_id"] == "DOC-A"
    assert source_map["CONCEPT-A"]["item_id"] == "item-left"
    assert source_map["CONCEPT-B"]["document_id"] == "DOC-B"
    assert source_map["CONCEPT-B"]["item_id"] == "item-right"


def test_row_source_resolution_uses_exact_item_not_first_item() -> None:
    executor = object.__new__(CotizacionesAnalysisExecutor)

    document = SimpleNamespace(
        document_id="DOC-A",
        provider_name="PROVIDER-A",
        file_name="quote-a.pdf",
        document_label="quote-a.pdf",
        items=(
            {
                "item_id": "wrong-first",
                "description": "OTRO MATERIAL",
                "quantity": "1",
                "unit": "UN",
                "unit_price": "999",
            },
            {
                "item_id": "item-left",
                "description": "CEMENTO PORTLAND TIPO I",
                "quantity": "10",
                "unit": "BLS",
                "unit_price": "20",
                "fields": {"marca": "A"},
            },
        ),
    )

    model = {
        "metadata": {
            "concept_source_map": {
                "CONCEPT-A": {
                    "concept_id": "CONCEPT-A",
                    "document_id": "DOC-A",
                    "item_id": "item-left",
                    "original_value": "cemento portland tipo i",
                    "normalized_value": "cemento portland tipo i",
                }
            }
        }
    }

    row = {
        "provider_id": "PROVIDER-A",
        "metadata": {
            "provider_source_document_ids": ["DOC-A"],
        },
    }

    resolved = executor._resolve_row_source_item(
        model=model,
        row=row,
        provider_documents=[document],
    )

    assert resolved is not None
    assert resolved["item_id"] == "item-left"
    assert resolved["description"] == "CEMENTO PORTLAND TIPO I"


def test_cell_resolution_prefers_resolved_item_fields() -> None:
    document = SimpleNamespace(
        provider_name="PROVIDER-A",
        commercial_currency="PEN",
        commercial_total_amount="200",
        commercial_payment_terms="CONTADO",
        file_name="quote-a.pdf",
        document_label="quote-a.pdf",
    )

    item = {
        "item_id": "item-left",
        "description": "CEMENTO PORTLAND TIPO I",
        "quantity": "10",
        "unit": "BLS",
        "unit_price": "20",
        "fields": {
            "marca": "A",
            "presentacion": "42.5KG",
        },
    }

    resolve = CotizacionesAnalysisExecutor._resolve_cell_value

    assert resolve(attribute="description", document=document, provider_id="PROVIDER-A", item=item) == "CEMENTO PORTLAND TIPO I"
    assert resolve(attribute="quantity", document=document, provider_id="PROVIDER-A", item=item) == "10"
    assert resolve(attribute="unit", document=document, provider_id="PROVIDER-A", item=item) == "BLS"
    assert resolve(attribute="unit_price", document=document, provider_id="PROVIDER-A", item=item) == "20"
    assert resolve(attribute="marca", document=document, provider_id="PROVIDER-A", item=item) == "A"
    assert resolve(attribute="currency", document=document, provider_id="PROVIDER-A", item=item) == "PEN"
