"""Pruebas unitarias del evaluador de similitud semántica."""

from __future__ import annotations

from types import SimpleNamespace

from zovrake_motor.classification.equivalence_detection.semantic_similarity import (
    SemanticSimilarityScorer,
)


def _concept(
    *,
    concept_id: str,
    normalized_value: str,
    concept_type: str = "material",
    semantic_knowledge: dict | None = None,
):
    return SimpleNamespace(
        normalized_concept_id=concept_id,
        concept_id=concept_id,
        normalized_value=normalized_value,
        original_value=normalized_value,
        concept_type=concept_type,
        metadata={
            "semantic_knowledge": (
                semantic_knowledge
                if semantic_knowledge is not None
                else {}
            )
        },
    )


def test_exact_text_and_type_are_very_similar() -> None:
    scorer = SemanticSimilarityScorer()

    left = _concept(
        concept_id="c-001",
        normalized_value="cemento portland tipo i",
    )

    right = _concept(
        concept_id="c-002",
        normalized_value="cemento portland tipo i",
    )

    result = scorer.compare(
        left,
        right,
    )

    assert result.score >= 0.70
    assert result.lexical_score == 1.0
    assert result.type_score == 1.0
    assert result.classification_hint in {
        "similar",
        "very_similar",
    }
    assert (
        "strong_normalized_text_similarity"
        in result.reasons
    )
    assert (
        "same_concept_type"
        in result.reasons
    )


def test_different_concepts_have_lower_similarity() -> None:
    scorer = SemanticSimilarityScorer()

    left = _concept(
        concept_id="c-001",
        normalized_value=(
            "cemento portland tipo i"
        ),
    )

    right = _concept(
        concept_id="c-002",
        normalized_value=(
            "pista atletica sistema sandwich"
        ),
    )

    result = scorer.compare(
        left,
        right,
    )

    assert result.lexical_score < 0.50
    assert result.score < 0.70
    assert (
        "weak_textual_similarity"
        in result.limitations
    )


def test_shared_semantic_facts_increase_similarity() -> None:
    scorer = SemanticSimilarityScorer()

    semantic = {
        "semantic_knowledge_available": True,
        "fact_ids": (
            "fact-001",
        ),
        "attribute_ids": (
            "attribute-001",
        ),
        "entity_ids": (
            "entity-001",
        ),
        "evidence_ids": (
            "evidence-001",
        ),
        "facts": (
            {
                "fact_id": "fact-001",
                "fact_type": "description",
                "label": "descripcion",
                "raw_value": (
                    "cemento portland tipo i"
                ),
            },
        ),
    }

    left = _concept(
        concept_id="c-001",
        normalized_value=(
            "cemento portland tipo i"
        ),
        semantic_knowledge=semantic,
    )

    right = _concept(
        concept_id="c-002",
        normalized_value=(
            "cemento portland tipo i"
        ),
        semantic_knowledge=semantic,
    )

    result = scorer.compare(
        left,
        right,
    )

    assert result.fact_overlap_score == 1.0
    assert result.attribute_overlap_score == 1.0
    assert result.entity_overlap_score == 1.0
    assert result.evidence_overlap_score == 1.0

    assert (
        "shared_semantic_facts"
        in result.reasons
    )
    assert (
        "shared_semantic_attributes"
        in result.reasons
    )
    assert (
        "shared_semantic_entities"
        in result.reasons
    )
    assert (
        "shared_evidence"
        in result.reasons
    )


def test_matching_numbers_and_units_are_exposed() -> None:
    scorer = SemanticSimilarityScorer()

    left = _concept(
        concept_id="c-001",
        normalized_value=(
            "rollo pvc 1280 mt"
        ),
    )

    right = _concept(
        concept_id="c-002",
        normalized_value=(
            "rollo pvc 1280 mt"
        ),
    )

    result = scorer.compare(
        left,
        right,
    )

    assert (
        result.numeric_compatibility_score
        == 1.0
    )
    assert (
        result.unit_compatibility_score
        == 1.0
    )

    assert (
        "matching_numeric_information"
        in result.reasons
    )
    assert (
        "matching_units"
        in result.reasons
    )


def test_missing_semantic_knowledge_is_reported_as_limitation() -> None:
    scorer = SemanticSimilarityScorer()

    left = _concept(
        concept_id="c-001",
        normalized_value="producto a",
    )

    right = _concept(
        concept_id="c-002",
        normalized_value="producto b",
    )

    result = scorer.compare(
        left,
        right,
    )

    assert (
        "left_concept_has_no_semantic_knowledge"
        in result.limitations
    )
    assert (
        "right_concept_has_no_semantic_knowledge"
        in result.limitations
    )


def test_similarity_never_declares_equivalence() -> None:
    scorer = SemanticSimilarityScorer()

    left = _concept(
        concept_id="c-001",
        normalized_value="cemento portland tipo i",
    )

    right = _concept(
        concept_id="c-002",
        normalized_value="cemento portland tipo i",
    )

    result = scorer.compare(
        left,
        right,
    )

    data = result.to_dict()

    assert "equivalent" not in data
    assert result.classification_hint != "equivalent"

    assert (
        "similarity_is_not_equivalence"
        in result.limitations
    )
    assert (
        "requires_downstream_evidence_decision"
        in result.limitations
    )