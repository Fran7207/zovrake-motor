from zovrake_motor.comprehension.models import DocumentKnowledge
from zovrake_motor.comprehension.semantic_closure import UniversalSemanticClosure
from zovrake_motor.comprehension.universal_document_semantic_reasoner import UniversalDocumentSemanticReasoner


def test_semantic_closure_explains_known_terms_and_preserves_unknowns():
    known = UniversalSemanticClosure.resolve_term("P/Unit.")
    unknown = UniversalSemanticClosure.resolve_term("ZXQ-77", context="Presentación ZXQ-77")

    assert known.semantic_key == "unit_price"
    assert known.confidence >= 0.9
    assert unknown.semantic_key in {"identifier_like", "unknown"}
    assert unknown.source in {"shape_inference", "unresolved_semantic_term"}


def test_reasoner_publishes_semantic_closure_for_all_observed_tokens():
    knowledge = DocumentKnowledge(
        document_id="zo059",
        page_count=1,
        text="",
        reading_order=(
            {
                "sequence": 1,
                "page_number": 1,
                "content_type": "text_line",
                "source_id": "line-1",
                "text": "Proveedor: DEMO COMERCIAL S.A.C. Precio unitario: 125.50",
                "confidence": 1.0,
                "metadata": {},
            },
        ),
    )
    result = UniversalDocumentSemanticReasoner().analyze(knowledge)
    closure = result["semantic_closure"]
    assert closure
    assert any(item["term"].casefold() == "proveedor" and item["semantic_key"] == "provider" for item in closure)
    assert "semantic_closure" in result["answer_context"]
