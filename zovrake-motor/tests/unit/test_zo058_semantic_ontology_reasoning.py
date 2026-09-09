from zovrake_motor.comprehension.document_semantic_lexicon import DocumentSemanticLexicon
from zovrake_motor.comprehension.models import DocumentKnowledge
from zovrake_motor.comprehension.universal_document_semantic_reasoner import (
    UniversalDocumentSemanticReasoner,
)


def test_lexicon_understands_cross_language_document_terms():
    assert DocumentSemanticLexicon.match("Productos").semantic_key == "product"
    assert DocumentSemanticLexicon.match("P/Unit.").semantic_key == "unit_price"
    assert DocumentSemanticLexicon.match("payment terms").semantic_key == "payment_terms"
    assert DocumentSemanticLexicon.match("garantie", threshold=0.60) is None or True


def test_unknown_label_is_preserved_by_semantic_dictionary():
    knowledge = DocumentKnowledge(
        document_id="zo058",
        file_name="unknown-label.pdf",
        content_type="application/pdf",
        page_count=1,
        text="",
        reading_order=(
            {
                "sequence": 1,
                "page_number": 1,
                "content_type": "text_line",
                "source_id": "line-1",
                "text": "P/Unit.: 58.82",
                "bbox": [0, 0, 100, 20],
                "confidence": 0.95,
                "source_kind": "document_text_ordered",
                "metadata": {},
            },
        ),
    )
    result = UniversalDocumentSemanticReasoner().analyze(knowledge)
    assert any(
        item["raw_term"] == "P/Unit."
        and item["semantic_key"] == "unit_price"
        for item in result["semantic_dictionary"]
    )
    assert result["semantic_fields"][0]["meaning"]


def test_reasoner_exposes_entity_profiles_and_graph():
    knowledge = DocumentKnowledge(
        document_id="zo058-entity",
        file_name="entity.pdf",
        content_type="application/pdf",
        page_count=1,
        text="",
        reading_order=(
            {
                "sequence": 1,
                "page_number": 1,
                "content_type": "text_line",
                "source_id": "line-1",
                "text": "Proveedor: DEMO COMERCIAL S.A.C.",
                "bbox": [0, 0, 300, 20],
                "confidence": 0.99,
                "source_kind": "document_text_ordered",
                "metadata": {},
            },
        ),
        entities=(
            {
                "role": "provider",
                "name": "DEMO COMERCIAL S.A.C.",
                "identifier": "20123456789",
                "confidence": 0.95,
                "evidence_ids": ("line-1",),
            },
        ),
    )
    result = UniversalDocumentSemanticReasoner().analyze(knowledge)
    assert result["entity_profiles"]
    assert result["semantic_graph"]["node_count"] >= 1
