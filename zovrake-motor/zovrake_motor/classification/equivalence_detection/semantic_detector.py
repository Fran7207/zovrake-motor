"""Detector semántico de relaciones comparables entre conceptos normalizados."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable

from zovrake_motor.classification.equivalence_detection.builders import build_equivalence_record
from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectorType,
    EquivalenceRelationType,
    EvidenceLevel,
)
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogView
from zovrake_motor.classification.equivalence_detection.models import DetectorResult
from zovrake_motor.classification.equivalence_detection.port import EquivalenceDetectorPort
from zovrake_motor.classification.equivalence_detection.semantic_similarity import SemanticSimilarityScorer


class SemanticSimilarityRelationDetector(EquivalenceDetectorPort):
    """
    Produce relaciones de equivalencia/comparabilidad a partir de señales
    semánticas ya disponibles en CNE.

    La salida ``comparable`` es deliberadamente distinta de ``equivalent``:
    CGB puede utilizar una relación comparable para construir un grupo
    candidato, pero PM7 debe conservar la incertidumbre y validar la decisión.
    """

    def __init__(self, scorer: SemanticSimilarityScorer | None = None) -> None:
        self._scorer = scorer or SemanticSimilarityScorer()

    @property
    def detector_name(self) -> str:
        return "semantic_similarity_relation_detector"

    @property
    def detector_label(self) -> str:
        return "Detector Semántico de Similitud y Comparabilidad"

    @property
    def detector_type(self) -> EquivalenceDetectorType:
        return EquivalenceDetectorType.SEMANTIC_SIMILARITY

    def detect(
        self,
        catalog_view: NormalizedConceptCatalogView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = tuple(
            concept
            for concept in catalog_view.concepts
            if concept.normalized_value.strip()
        )

        candidates = self._candidate_pairs(
            concepts,
        )

        relations = []
        sequence = start_sequence
        comparisons = 0

        # El límite se toma del catálogo para que el detector permanezca
        # desacoplado de ConfigurationProvider y pueda probarse aisladamente.
        max_comparisons = int(
            catalog_view.raw_catalog.get(
                "semantic_similarity_max_comparisons",
                50_000,
            )
            or 50_000
        )
        comparable_threshold = float(
            catalog_view.raw_catalog.get(
                "semantic_similarity_comparable_threshold",
                0.52,
            )
            or 0.52
        )
        equivalent_threshold = float(
            catalog_view.raw_catalog.get(
                "semantic_similarity_equivalent_threshold",
                0.85,
            )
            or 0.85
        )
        min_shared_tokens = int(
            catalog_view.raw_catalog.get(
                "semantic_similarity_min_shared_tokens",
                1,
            )
            or 1
        )

        for left, right in candidates:
            if comparisons >= max_comparisons:
                break

            comparisons += 1

            if not self._same_cross_document_type(
                left,
                right,
            ):
                continue

            shared_tokens = self._shared_tokens(
                left.normalized_value,
                right.normalized_value,
            )

            if len(shared_tokens) < min_shared_tokens:
                continue

            similarity = self._scorer.compare(
                left,
                right,
            )

            if self._has_hard_unit_conflict(
                left,
                right,
                similarity.unit_compatibility_score,
            ):
                continue

            if similarity.score < comparable_threshold:
                continue

            if similarity.score >= equivalent_threshold:
                relation_type = EquivalenceRelationType.EQUIVALENT
                evidence_level = EvidenceLevel.HIGH
                rationale = (
                    "La evaluación semántica supera el umbral de equivalencia "
                    "y no presenta un conflicto duro de unidad; la relación "
                    "queda trazada como equivalente según las señales disponibles."
                )
            else:
                relation_type = EquivalenceRelationType.COMPARABLE
                evidence_level = EvidenceLevel.MEDIUM
                rationale = (
                    "Los conceptos presentan similitud semántica suficiente "
                    "para formar un candidato de comparación, pero la señal "
                    "no alcanza el nivel requerido para declarar equivalencia."
                )

            relations.append(
                build_equivalence_record(
                    catalog_view=catalog_view,
                    concepts=(left, right),
                    sequence=sequence,
                    relation_type=relation_type,
                    evidence_level=evidence_level,
                    detector_type=self.detector_type.value,
                    detector_name=self.detector_name,
                    criteria_used=(
                        "cross_document_pair",
                        "concept_type_match",
                        "shared_informative_token",
                        "semantic_similarity_score",
                        "unit_compatibility_check",
                    ),
                    information_used=(
                        f"left_normalized_value={left.normalized_value}",
                        f"right_normalized_value={right.normalized_value}",
                        f"semantic_similarity_score={similarity.score}",
                        f"lexical_score={similarity.lexical_score}",
                        f"type_score={similarity.type_score}",
                        f"numeric_compatibility_score={similarity.numeric_compatibility_score}",
                        f"unit_compatibility_score={similarity.unit_compatibility_score}",
                        f"shared_tokens={','.join(sorted(shared_tokens))}",
                    ),
                    limitations=(
                        "deterministic_semantic_similarity",
                        "similarity_is_not_business_winner_decision",
                        "requires_downstream_evidence_analysis",
                    ),
                    rationale=rationale,
                    metadata={
                        "semantic_similarity_score": similarity.score,
                        "semantic_similarity_classification_hint": similarity.classification_hint,
                        "semantic_similarity_reasons": list(similarity.reasons),
                        "semantic_similarity_limitations": list(similarity.limitations),
                        "semantic_similarity_shared_tokens": sorted(shared_tokens),
                        "semantic_comparable_candidate": True,
                        "semantic_equivalence_candidate": relation_type == EquivalenceRelationType.EQUIVALENT,
                        "left_normalized_value": left.normalized_value,
                        "right_normalized_value": right.normalized_value,
                        "left_concept_type": left.concept_type,
                        "right_concept_type": right.concept_type,
                    },
                )
            )
            sequence += 1

        observations = (
            f"detector_type={self.detector_type.value}",
            f"candidate_pairs={len(candidates)}",
            f"comparisons_executed={comparisons}",
            f"semantic_relations_detected={len(relations)}",
            f"semantic_relations_truncated={comparisons >= max_comparisons}",
        )

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            equivalences=tuple(relations),
            technical_observations=observations,
        )

    @staticmethod
    def _same_cross_document_type(left, right) -> bool:
        if left.concept_type != right.concept_type:
            return False
        left_document_id = str(left.traceability.document_id).strip()
        right_document_id = str(right.traceability.document_id).strip()
        return bool(left_document_id and right_document_id and left_document_id != right_document_id)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        import re

        stopwords = {
            "a", "al", "con", "de", "del", "el", "en", "la",
            "las", "los", "para", "por", "un", "una", "y", "x", "e",
        }
        return {
            token
            for token in re.findall(r"[a-záéíóúüñ]+|\d+(?:[.,]\d+)?", value.casefold())
            if token and token not in stopwords
        }

    @classmethod
    def _shared_tokens(cls, left: str, right: str) -> set[str]:
        return cls._tokens(left) & cls._tokens(right)

    @classmethod
    def _candidate_pairs(cls, concepts: tuple) -> tuple[tuple[object, object], ...]:
        # Índice invertido: evita el coste O(n²) cuando hay muchos documentos.
        token_index: dict[str, list] = {}
        for concept in concepts:
            for token in cls._tokens(concept.normalized_value):
                token_index.setdefault(token, []).append(concept)

        pair_keys: set[tuple[str, str]] = set()
        pairs: list[tuple[object, object]] = []

        for token_concepts in token_index.values():
            if len(token_concepts) < 2:
                continue
            for left, right in combinations(token_concepts, 2):
                key = tuple(sorted((
                    str(left.normalized_concept_id),
                    str(right.normalized_concept_id),
                )))
                if key in pair_keys:
                    continue
                pair_keys.add(key)
                pairs.append((left, right))

        return tuple(pairs)

    @staticmethod
    def _metadata_unit(concept) -> str:
        metadata = getattr(concept, "metadata", {})
        if not isinstance(metadata, dict):
            return ""
        for key in ("unit", "unidad"):
            value = str(metadata.get(key, "") or "").strip().casefold()
            if value:
                return value
        return ""

    @classmethod
    def _has_hard_unit_conflict(cls, left, right, score: float) -> bool:
        left_unit = cls._metadata_unit(left)
        right_unit = cls._metadata_unit(right)
        if not left_unit or not right_unit:
            return False
        if left_unit == right_unit:
            return False
        # Unidades inequivalentes son una barrera fuerte para comparar.
        return score == 0.0

    def snapshot(self) -> dict[str, object]:
        return {
            "detector_name": self.detector_name,
            "detector_type": self.detector_type.value,
            "model_version": self._scorer.MODEL_VERSION,
            "uses_semantic_similarity": True,
            "produces_comparable_candidates": True,
            "does_not_decide_business_winner": True,
        }
