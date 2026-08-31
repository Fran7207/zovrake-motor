"""Evaluación determinista de similitud semántica entre conceptos normalizados."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class SemanticSimilarityResult:
    """
    Resultado explicable de una comparación semántica.

    Este resultado NO declara equivalencia.

    Solamente responde:
        "¿Qué tan parecidos son estos dos conceptos según la evidencia
         disponible en sus representaciones normalizadas?"

    La decisión final de equivalencia continúa perteneciendo a EDE.
    """

    score: float
    lexical_score: float
    type_score: float
    fact_overlap_score: float
    attribute_overlap_score: float
    entity_overlap_score: float
    evidence_overlap_score: float
    numeric_compatibility_score: float
    unit_compatibility_score: float
    semantic_context_score: float
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    compared_concept_ids: tuple[str, str]

    @property
    def classification_hint(self) -> str:
        """
        Clasificación orientativa.

        No es una decisión de equivalencia.
        """
        if self.score >= 0.85:
            return "very_similar"

        if self.score >= 0.70:
            return "similar"

        if self.score >= 0.50:
            return "related"

        return "weak_or_unrelated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "lexical_score": self.lexical_score,
            "type_score": self.type_score,
            "fact_overlap_score": self.fact_overlap_score,
            "attribute_overlap_score": self.attribute_overlap_score,
            "entity_overlap_score": self.entity_overlap_score,
            "evidence_overlap_score": self.evidence_overlap_score,
            "numeric_compatibility_score": self.numeric_compatibility_score,
            "unit_compatibility_score": self.unit_compatibility_score,
            "semantic_context_score": self.semantic_context_score,
            "classification_hint": self.classification_hint,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
            "compared_concept_ids": list(self.compared_concept_ids),
        }


class SemanticSimilarityScorer:
    """
    Calcula similitud semántica determinista.

    No depende de modelos externos, embeddings ni APIs.

    Utiliza:

    - nombre/valor normalizado;
    - tipo conceptual;
    - hechos semánticos;
    - atributos semánticos;
    - entidades;
    - evidencias;
    - números;
    - unidades;
    - contexto semántico.

    La finalidad es proporcionar una puntuación explicable que después
    podrá consumir el EDE sin convertir similitud en equivalencia automática.
    """

    MODEL_VERSION = "1.0-deterministic-semantic-similarity"

    _STOPWORDS = frozenset(
        {
            "a",
            "al",
            "con",
            "de",
            "del",
            "el",
            "en",
            "la",
            "las",
            "los",
            "para",
            "por",
            "un",
            "una",
            "y",
            "x",
            "e",
        }
    )

    _NUMBER_PATTERN = re.compile(
        r"[-+]?\d+(?:[.,]\d+)?"
    )

    _UNIT_PATTERN = re.compile(
    r"\b("
    r"kg|g|mg|t|"
    r"mt|m|cm|mm|km|"
    r"m2|m²|m3|m³|"
    r"l|ml|"
    r"v|kv|w|kw|hz|"
    r"a|ma|"
    r"und|unidad|unidades|"
    r"hrs?|horas?|"
    r"dias?|días?|"
    r"meses?|años?"
    r")\b",
    re.IGNORECASE,
)

    def compare(
        self,
        left: Any,
        right: Any,
    ) -> SemanticSimilarityResult:
        """
        Compara dos NormalizedConceptRecord compatibles con el contrato
        utilizado actualmente por ZOVRAKE.

        No exige importar directamente NormalizedConceptRecord para mantener
        esta capa desacoplada.
        """
        left_id = self._concept_id(
            left
        )
        right_id = self._concept_id(
            right
        )

        left_value = self._concept_value(
            left
        )
        right_value = self._concept_value(
            right
        )

        lexical_score = self._lexical_similarity(
            left_value,
            right_value,
        )

        type_score = self._type_similarity(
            left,
            right,
        )

        left_semantic = self._semantic_knowledge(
            left
        )
        right_semantic = self._semantic_knowledge(
            right
        )

        fact_overlap_score = self._set_similarity(
            self._ids_from_semantic(
                left_semantic,
                "fact_ids",
            ),
            self._ids_from_semantic(
                right_semantic,
                "fact_ids",
            ),
        )

        attribute_overlap_score = self._set_similarity(
            self._ids_from_semantic(
                left_semantic,
                "attribute_ids",
            ),
            self._ids_from_semantic(
                right_semantic,
                "attribute_ids",
            ),
        )

        entity_overlap_score = self._set_similarity(
            self._ids_from_semantic(
                left_semantic,
                "entity_ids",
            ),
            self._ids_from_semantic(
                right_semantic,
                "entity_ids",
            ),
        )

        evidence_overlap_score = self._set_similarity(
            self._ids_from_semantic(
                left_semantic,
                "evidence_ids",
            ),
            self._ids_from_semantic(
                right_semantic,
                "evidence_ids",
            ),
        )

        numeric_compatibility_score = (
            self._numeric_compatibility(
                left_value,
                right_value,
            )
        )

        unit_compatibility_score = (
            self._unit_compatibility(
                left_value,
                right_value,
            )
        )

        semantic_context_score = (
            self._semantic_context_similarity(
                left_semantic,
                right_semantic,
            )
        )

        score = self._weighted_score(
            lexical_score=lexical_score,
            type_score=type_score,
            fact_overlap_score=fact_overlap_score,
            attribute_overlap_score=attribute_overlap_score,
            entity_overlap_score=entity_overlap_score,
            evidence_overlap_score=evidence_overlap_score,
            numeric_compatibility_score=(
                numeric_compatibility_score
            ),
            unit_compatibility_score=(
                unit_compatibility_score
            ),
            semantic_context_score=(
                semantic_context_score
            ),
        )

        reasons = self._build_reasons(
            lexical_score=lexical_score,
            type_score=type_score,
            fact_overlap_score=fact_overlap_score,
            attribute_overlap_score=attribute_overlap_score,
            entity_overlap_score=entity_overlap_score,
            evidence_overlap_score=evidence_overlap_score,
            numeric_compatibility_score=(
                numeric_compatibility_score
            ),
            unit_compatibility_score=(
                unit_compatibility_score
            ),
            semantic_context_score=(
                semantic_context_score
            ),
        )

        limitations = self._build_limitations(
            left_semantic,
            right_semantic,
            lexical_score,
            type_score,
        )

        return SemanticSimilarityResult(
            score=round(
                max(
                    0.0,
                    min(
                        1.0,
                        score,
                    ),
                ),
                4,
            ),
            lexical_score=round(
                lexical_score,
                4,
            ),
            type_score=round(
                type_score,
                4,
            ),
            fact_overlap_score=round(
                fact_overlap_score,
                4,
            ),
            attribute_overlap_score=round(
                attribute_overlap_score,
                4,
            ),
            entity_overlap_score=round(
                entity_overlap_score,
                4,
            ),
            evidence_overlap_score=round(
                evidence_overlap_score,
                4,
            ),
            numeric_compatibility_score=round(
                numeric_compatibility_score,
                4,
            ),
            unit_compatibility_score=round(
                unit_compatibility_score,
                4,
            ),
            semantic_context_score=round(
                semantic_context_score,
                4,
            ),
            reasons=reasons,
            limitations=limitations,
            compared_concept_ids=(
                left_id,
                right_id,
            ),
        )

    @classmethod
    def _weighted_score(
        cls,
        *,
        lexical_score: float,
        type_score: float,
        fact_overlap_score: float,
        attribute_overlap_score: float,
        entity_overlap_score: float,
        evidence_overlap_score: float,
        numeric_compatibility_score: float,
        unit_compatibility_score: float,
        semantic_context_score: float,
    ) -> float:
        """
        Combina señales sin permitir que una señal débil domine la decisión.

        El valor normalizado tiene mayor peso porque continúa siendo la
        representación conceptual principal del CNE.
        """
        weights = {
    "lexical": 0.55,
    "type": 0.20,
    "facts": 0.07,
    "attributes": 0.05,
    "entities": 0.04,
    "evidence": 0.03,
    "numeric": 0.025,
    "unit": 0.02,
    "context": 0.02,
}

        return (
            lexical_score
            * weights["lexical"]
            + type_score
            * weights["type"]
            + fact_overlap_score
            * weights["facts"]
            + attribute_overlap_score
            * weights["attributes"]
            + entity_overlap_score
            * weights["entities"]
            + evidence_overlap_score
            * weights["evidence"]
            + numeric_compatibility_score
            * weights["numeric"]
            + unit_compatibility_score
            * weights["unit"]
            + semantic_context_score
            * weights["context"]
        )

    @classmethod
    def _lexical_similarity(
        cls,
        left: str,
        right: str,
    ) -> float:
        left_tokens = cls._tokens(
            left
        )
        right_tokens = cls._tokens(
            right
        )

        if not left_tokens or not right_tokens:
            return 0.0

        if left_tokens == right_tokens:
            return 1.0

        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens

        if not union:
            return 0.0

        jaccard = len(
            intersection
        ) / len(
            union
        )

        containment = max(
            len(intersection)
            / len(left_tokens),
            len(intersection)
            / len(right_tokens),
        )

        return (
            (jaccard * 0.45)
            + (containment * 0.55)
        )

    @classmethod
    def _tokens(
        cls,
        value: str,
    ) -> set[str]:
        normalized = cls._normalize_text(
            value
        )

        tokens = {
            token
            for token in re.findall(
                r"[a-záéíóúüñ0-9]+",
                normalized,
            )
            if token
            and token not in cls._STOPWORDS
        }

        return tokens

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:
        return " ".join(
            str(value)
            .casefold()
            .split()
        )

    @staticmethod
    def _concept_id(
        concept: Any,
    ) -> str:
        value = getattr(
            concept,
            "normalized_concept_id",
            "",
        )

        if not value:
            value = getattr(
                concept,
                "concept_id",
                "",
            )

        return str(
            value
        )

    @staticmethod
    def _concept_value(
        concept: Any,
    ) -> str:
        value = getattr(
            concept,
            "normalized_value",
            "",
        )

        if not value:
            value = getattr(
                concept,
                "original_value",
                "",
            )

        return str(
            value
        )

    @staticmethod
    def _concept_type(
        concept: Any,
    ) -> str:
        return SemanticSimilarityScorer._normalize_text(
            getattr(
                concept,
                "concept_type",
                "",
            )
        )

    @classmethod
    def _type_similarity(
        cls,
        left: Any,
        right: Any,
    ) -> float:
        left_type = cls._concept_type(
            left
        )
        right_type = cls._concept_type(
            right
        )

        if not left_type or not right_type:
            return 0.0

        return (
            1.0
            if left_type == right_type
            else 0.0
        )

    @staticmethod
    def _semantic_knowledge(
        concept: Any,
    ) -> dict[str, Any]:
        metadata = getattr(
            concept,
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            return {}

        semantic = metadata.get(
            "semantic_knowledge",
            {},
        )

        if not isinstance(
            semantic,
            dict,
        ):
            return {}

        return semantic

    @staticmethod
    def _ids_from_semantic(
        semantic: dict[str, Any],
        key: str,
    ) -> set[str]:
        values = semantic.get(
            key,
            (),
        )

        if not isinstance(
            values,
            (list, tuple, set, frozenset),
        ):
            return set()

        return {
            str(value).strip()
            for value in values
            if str(value).strip()
        }

    @staticmethod
    def _set_similarity(
        left: set[str],
        right: set[str],
    ) -> float:
        if not left or not right:
            return 0.0

        if left == right:
            return 1.0

        intersection = left & right

        if not intersection:
            return 0.0

        union = left | right

        return len(
            intersection
        ) / len(
            union
        )

    @classmethod
    def _numeric_compatibility(
        cls,
        left: str,
        right: str,
    ) -> float:
        left_numbers = cls._numbers(
            left
        )
        right_numbers = cls._numbers(
            right
        )

        if not left_numbers or not right_numbers:
            return 0.0

        if left_numbers == right_numbers:
            return 1.0

        intersection = (
            left_numbers
            & right_numbers
        )

        if intersection:
            return len(
                intersection
            ) / len(
                left_numbers
                | right_numbers
            )

        return 0.0

    @classmethod
    def _numbers(
        cls,
        value: str,
    ) -> set[str]:
        numbers = set()

        for raw in cls._NUMBER_PATTERN.findall(
            value
        ):
            normalized = cls._normalize_number(
                raw
            )

            if normalized is not None:
                numbers.add(
                    normalized
                )

        return numbers

    @staticmethod
    def _normalize_number(
        value: str,
    ) -> str | None:
        cleaned = re.sub(
            r"[^\d,.\-+]",
            "",
            str(value),
        )

        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(
                    ".",
                    "",
                )
                cleaned = cleaned.replace(
                    ",",
                    ".",
                )
            else:
                cleaned = cleaned.replace(
                    ",",
                    "",
                )

        elif "," in cleaned:
            parts = cleaned.split(",")

            if (
                len(parts) == 2
                and len(parts[1]) <= 2
            ):
                cleaned = cleaned.replace(
                    ",",
                    ".",
                )
            else:
                cleaned = cleaned.replace(
                    ",",
                    "",
                )

        elif "." in cleaned:
            parts = cleaned.split(".")

            if (
                len(parts) > 2
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):
                cleaned = "".join(
                    parts
                )

        try:
            number = float(
                cleaned
            )
        except ValueError:
            return None

        if number.is_integer():
            return str(
                int(number)
            )

        return format(
            number,
            ".12g",
        )

    @classmethod
    def _unit_compatibility(
        cls,
        left: str,
        right: str,
    ) -> float:
        left_units = cls._units(
            left
        )
        right_units = cls._units(
            right
        )

        if not left_units or not right_units:
            return 0.0

        if left_units == right_units:
            return 1.0

        if left_units & right_units:
            return 0.5

        return 0.0

    @classmethod
    def _units(
        cls,
        value: str,
    ) -> set[str]:
        return {
            unit.casefold()
            for unit in cls._UNIT_PATTERN.findall(
                value
            )
        }

    @classmethod
    def _semantic_context_similarity(
        cls,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> float:
        left_facts = cls._fact_context_labels(
            left
        )
        right_facts = cls._fact_context_labels(
            right
        )

        if not left_facts or not right_facts:
            return 0.0

        return cls._set_similarity(
            left_facts,
            right_facts,
        )

    @classmethod
    def _fact_context_labels(
        cls,
        semantic: dict[str, Any],
    ) -> set[str]:
        raw_facts = semantic.get(
            "facts",
            (),
        )

        if not isinstance(
            raw_facts,
            (list, tuple),
        ):
            return set()

        labels: set[str] = set()

        for fact in raw_facts:
            if not isinstance(
                fact,
                dict,
            ):
                continue

            fact_type = cls._normalize_text(
                fact.get(
                    "fact_type",
                    "",
                )
            )

            label = cls._normalize_text(
                fact.get(
                    "label",
                    "",
                )
            )

            raw_value = cls._normalize_text(
                fact.get(
                    "raw_value",
                    fact.get(
                        "value",
                        "",
                    ),
                )
            )

            if fact_type:
                labels.add(
                    f"type:{fact_type}"
                )

            if label:
                labels.add(
                    f"label:{label}"
                )

            if raw_value:
                tokens = cls._tokens(
                    raw_value
                )

                labels.update(
                    f"value:{token}"
                    for token in tokens
                )

        return labels

    @staticmethod
    def _build_reasons(
        *,
        lexical_score: float,
        type_score: float,
        fact_overlap_score: float,
        attribute_overlap_score: float,
        entity_overlap_score: float,
        evidence_overlap_score: float,
        numeric_compatibility_score: float,
        unit_compatibility_score: float,
        semantic_context_score: float,
    ) -> tuple[str, ...]:
        reasons: list[str] = []

        if lexical_score >= 0.90:
            reasons.append(
                "strong_normalized_text_similarity"
            )
        elif lexical_score >= 0.70:
            reasons.append(
                "moderate_normalized_text_similarity"
            )

        if type_score == 1.0:
            reasons.append(
                "same_concept_type"
            )

        if fact_overlap_score > 0.0:
            reasons.append(
                "shared_semantic_facts"
            )

        if attribute_overlap_score > 0.0:
            reasons.append(
                "shared_semantic_attributes"
            )

        if entity_overlap_score > 0.0:
            reasons.append(
                "shared_semantic_entities"
            )

        if evidence_overlap_score > 0.0:
            reasons.append(
                "shared_evidence"
            )

        if numeric_compatibility_score == 1.0:
            reasons.append(
                "matching_numeric_information"
            )

        if unit_compatibility_score == 1.0:
            reasons.append(
                "matching_units"
            )
        elif unit_compatibility_score == 0.5:
            reasons.append(
                "partially_matching_units"
            )

        if semantic_context_score > 0.0:
            reasons.append(
                "similar_semantic_context"
            )

        if not reasons:
            reasons.append(
                "no_strong_similarity_signal"
            )

        return tuple(
            dict.fromkeys(
                reasons
            )
        )

    @staticmethod
    def _build_limitations(
        left_semantic: dict[str, Any],
        right_semantic: dict[str, Any],
        lexical_score: float,
        type_score: float,
    ) -> tuple[str, ...]:
        limitations: list[str] = []

        if not left_semantic:
            limitations.append(
                "left_concept_has_no_semantic_knowledge"
            )

        if not right_semantic:
            limitations.append(
                "right_concept_has_no_semantic_knowledge"
            )

        if lexical_score < 0.50:
            limitations.append(
                "weak_textual_similarity"
            )

        if type_score == 0.0:
            limitations.append(
                "concept_type_not_matching"
            )

        limitations.extend(
            (
                "similarity_is_not_equivalence",
                "deterministic_evaluation_without_external_model",
                "requires_downstream_evidence_decision",
            )
        )

        return tuple(
            dict.fromkeys(
                limitations
            )
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "model_version": self.MODEL_VERSION,
            "deterministic": True,
            "external_model_required": False,
            "does_not_decide_equivalence": True,
            "signals": [
                "normalized_text",
                "concept_type",
                "semantic_facts",
                "semantic_attributes",
                "semantic_entities",
                "semantic_evidence",
                "numeric_compatibility",
                "unit_compatibility",
                "semantic_context",
            ],
        }