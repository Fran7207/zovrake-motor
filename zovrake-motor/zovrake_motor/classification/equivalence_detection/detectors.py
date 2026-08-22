"""Detectores especializados del Equivalence Detection Engine."""

from __future__ import annotations

from itertools import combinations

from zovrake_motor.classification.equivalence_detection.builders import build_equivalence_record
from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectorType,
    EquivalenceRelationType,
    EvidenceLevel,
)
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogView
from zovrake_motor.classification.equivalence_detection.models import DetectorResult
from zovrake_motor.classification.equivalence_detection.port import EquivalenceDetectorPort


def _is_cross_document_pair(
    catalog_view: NormalizedConceptCatalogView,
    left,
    right,
) -> bool:
    """Permite restringir un catálogo colectivo a equivalencias entre documentos."""
    if not bool(catalog_view.raw_catalog.get("cross_document_only", False)):
        return True
    left_document_id = str(left.traceability.document_id)
    right_document_id = str(right.traceability.document_id)
    return bool(left_document_id) and bool(right_document_id) and left_document_id != right_document_id



class ExactNormalizedMatchDetector(EquivalenceDetectorPort):
    """
    Detecta equivalencias cuando el valor normalizado y el tipo de concepto coinciden.

    No asume equivalencia por similitud superficial sin coincidencia estructurada.
    """

    @property
    def detector_name(self) -> str:
        return "exact_normalized_match_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Equivalencias — Coincidencia Normalizada Exacta"

    @property
    def detector_type(self) -> EquivalenceDetectorType:
        return EquivalenceDetectorType.EXACT_NORMALIZED_MATCH

    def detect(self, catalog_view: NormalizedConceptCatalogView, *, start_sequence: int) -> DetectorResult:
        equivalences = []
        sequence = start_sequence
        concepts = [concept for concept in catalog_view.concepts if concept.normalized_value.strip()]

        for left, right in combinations(concepts, 2):
            if not _is_cross_document_pair(catalog_view, left, right):
                continue
            if left.normalized_concept_id == right.normalized_concept_id:
                continue
            if left.normalized_value != right.normalized_value:
                continue
            if left.concept_type != right.concept_type:
                continue

            equivalences.append(
                build_equivalence_record(
                    catalog_view=catalog_view,
                    concepts=(left, right),
                    sequence=sequence,
                    relation_type=EquivalenceRelationType.EQUIVALENT,
                    evidence_level=EvidenceLevel.HIGH,
                    detector_type=self.detector_type.value,
                    detector_name=self.detector_name,
                    criteria_used=(
                        "normalized_value_exact_match",
                        "concept_type_match",
                        "distinct_normalized_concept_ids",
                    ),
                    information_used=(
                        f"normalized_value={left.normalized_value}",
                        f"concept_type={left.concept_type}",
                        f"concept_ids=({left.concept_id},{right.concept_id})",
                    ),
                    limitations=(
                        "sin_modelos_generativos",
                        "evaluacion_estructurada_exclusiva",
                        "sin_reglas_de_negocio",
                    ),
                    rationale=(
                        "Los conceptos comparten valor normalizado y tipo conceptual, "
                        "indicando representación del mismo elemento de dominio."
                    ),
                    metadata={
                        "shared_normalized_value": left.normalized_value,
                        "shared_concept_type": left.concept_type,
                    },
                ),
            )
            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            equivalences=tuple(equivalences),
            technical_observations=(
                f"detector_type={self.detector_type.value}",
                f"equivalences_detected={len(equivalences)}",
            ),
        )


class CrossTypeDistinctDetector(EquivalenceDetectorPort):
    """
    Identifica conceptos similares que no representan el mismo elemento.

    Diferencia explícitamente cuando el valor normalizado coincide pero el tipo difiere.
    """

    @property
    def detector_name(self) -> str:
        return "cross_type_distinct_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Equivalencias — Diferenciación entre Tipos"

    @property
    def detector_type(self) -> EquivalenceDetectorType:
        return EquivalenceDetectorType.CROSS_TYPE_DISTINCT

    def detect(self, catalog_view: NormalizedConceptCatalogView, *, start_sequence: int) -> DetectorResult:
        equivalences = []
        sequence = start_sequence
        concepts = [concept for concept in catalog_view.concepts if concept.normalized_value.strip()]

        for left, right in combinations(concepts, 2):
            if not _is_cross_document_pair(catalog_view, left, right):
                continue
            if left.normalized_value != right.normalized_value:
                continue
            if left.concept_type == right.concept_type:
                continue

            equivalences.append(
                build_equivalence_record(
                    catalog_view=catalog_view,
                    concepts=(left, right),
                    sequence=sequence,
                    relation_type=EquivalenceRelationType.DISTINCT,
                    evidence_level=EvidenceLevel.MEDIUM,
                    detector_type=self.detector_type.value,
                    detector_name=self.detector_name,
                    criteria_used=(
                        "normalized_value_exact_match",
                        "concept_type_mismatch",
                    ),
                    information_used=(
                        f"normalized_value={left.normalized_value}",
                        f"left_concept_type={left.concept_type}",
                        f"right_concept_type={right.concept_type}",
                    ),
                    limitations=(
                        "similitud_superficial_no_implica_equivalencia",
                        "sin_modelos_generativos",
                    ),
                    rationale=(
                        "Los conceptos comparten valor normalizado pero pertenecen a tipos "
                        "conceptuales distintos; no se consideran equivalentes."
                    ),
                    metadata={
                        "shared_normalized_value": left.normalized_value,
                        "left_concept_type": left.concept_type,
                        "right_concept_type": right.concept_type,
                    },
                ),
            )
            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            equivalences=tuple(equivalences),
            technical_observations=(
                f"detector_type={self.detector_type.value}",
                f"distinct_relations_detected={len(equivalences)}",
            ),
        )


class SharedOriginRelationDetector(EquivalenceDetectorPort):
    """
    Identifica conceptos relacionados por origen común sin declararlos equivalentes.

    Útil cuando múltiples representaciones normalizadas provienen del mismo concepto CAE.
    """

    @property
    def detector_name(self) -> str:
        return "shared_origin_relation_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Equivalencias — Relación por Origen Compartido"

    @property
    def detector_type(self) -> EquivalenceDetectorType:
        return EquivalenceDetectorType.SHARED_ORIGIN_RELATION

    def detect(self, catalog_view: NormalizedConceptCatalogView, *, start_sequence: int) -> DetectorResult:
        equivalences = []
        sequence = start_sequence
        concepts = list(catalog_view.concepts)

        for left, right in combinations(concepts, 2):
            if not _is_cross_document_pair(catalog_view, left, right):
                continue
            if left.concept_id != right.concept_id:
                continue
            if left.normalized_concept_id == right.normalized_concept_id:
                continue

            equivalences.append(
                build_equivalence_record(
                    catalog_view=catalog_view,
                    concepts=(left, right),
                    sequence=sequence,
                    relation_type=EquivalenceRelationType.RELATED,
                    evidence_level=EvidenceLevel.LOW,
                    detector_type=self.detector_type.value,
                    detector_name=self.detector_name,
                    criteria_used=(
                        "shared_cae_concept_id",
                        "distinct_normalized_representations",
                    ),
                    information_used=(
                        f"concept_id={left.concept_id}",
                        f"left_type={left.concept_type}",
                        f"right_type={right.concept_type}",
                    ),
                    limitations=(
                        "relacion_no_implica_equivalencia",
                        "requiere_evaluacion_adicional_para_equivalencia",
                    ),
                    rationale=(
                        "Los conceptos comparten origen CAE pero mantienen representaciones "
                        "normalizadas distintas; se registran como relacionados, no equivalentes."
                    ),
                    metadata={
                        "shared_concept_id": left.concept_id,
                        "left_concept_type": left.concept_type,
                        "right_concept_type": right.concept_type,
                    },
                ),
            )
            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            equivalences=tuple(equivalences),
            technical_observations=(
                f"detector_type={self.detector_type.value}",
                f"related_relations_detected={len(equivalences)}",
            ),
        )