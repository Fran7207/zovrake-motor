"""Clasificadores especializados del Material Classification Engine."""

from __future__ import annotations

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.material_classification.builders import build_material_from_concept
from zovrake_motor.classification.material_classification.enums import MaterialClassifierType
from zovrake_motor.classification.material_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.material_classification.models import ClassifierResult
from zovrake_motor.classification.material_classification.port import MaterialClassifierPort


class _BaseMaterialClassifier(MaterialClassifierPort):
    """Base común para clasificadores de materiales por tipo de concepto."""

    def classify(self, catalog_view: ConceptCatalogView, *, start_sequence: int) -> ClassifierResult:
        materials = []
        sequence = start_sequence
        for concept in catalog_view.concepts:
            if concept.kind != self.supported_concept_kind:
                continue
            if not concept.original_description.strip():
                continue
            materials.append(
                build_material_from_concept(
                    catalog_view=catalog_view,
                    concept=concept,
                    sequence=sequence,
                ),
            )
            sequence += 1

        return ClassifierResult(
            classifier_type=self.classifier_type,
            classifier_name=self.classifier_name,
            materials=tuple(materials),
            technical_observations=(
                f"concept_kind={self.supported_concept_kind.value}",
                f"materials_classified={len(materials)}",
            ),
        )


class ItemMaterialClassifier(_BaseMaterialClassifier):
    """Clasifica conceptos de tipo ítem como materiales."""

    @property
    def classifier_name(self) -> str:
        return "item_material_classifier"

    @property
    def classifier_label(self) -> str:
        return "Clasificador de Materiales — Ítems"

    @property
    def classifier_type(self) -> MaterialClassifierType:
        return MaterialClassifierType.ITEM

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.ITEM


class PartidaMaterialClassifier(_BaseMaterialClassifier):
    """Clasifica conceptos de tipo partida como materiales."""

    @property
    def classifier_name(self) -> str:
        return "partida_material_classifier"

    @property
    def classifier_label(self) -> str:
        return "Clasificador de Materiales — Partidas"

    @property
    def classifier_type(self) -> MaterialClassifierType:
        return MaterialClassifierType.PARTIDA

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.PARTIDA
