"""Clasificadores especializados del Service Classification Engine."""

from __future__ import annotations

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.service_classification.builders import build_service_from_concept
from zovrake_motor.classification.service_classification.enums import ServiceClassifierType
from zovrake_motor.classification.service_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.service_classification.models import ClassifierResult
from zovrake_motor.classification.service_classification.port import ServiceClassifierPort


class _BaseServiceClassifier(ServiceClassifierPort):
    """Base común para clasificadores de servicios por tipo de concepto."""

    def classify(self, catalog_view: ConceptCatalogView, *, start_sequence: int) -> ClassifierResult:
        services = []
        sequence = start_sequence
        for concept in catalog_view.concepts:
            if concept.kind != self.supported_concept_kind:
                continue
            if not concept.original_description.strip():
                continue
            services.append(
                build_service_from_concept(
                    catalog_view=catalog_view,
                    concept=concept,
                    sequence=sequence,
                ),
            )
            sequence += 1

        return ClassifierResult(
            classifier_type=self.classifier_type,
            classifier_name=self.classifier_name,
            services=tuple(services),
            technical_observations=(
                f"concept_kind={self.supported_concept_kind.value}",
                f"services_classified={len(services)}",
            ),
        )


class CommercialConditionServiceClassifier(_BaseServiceClassifier):
    """Clasifica condiciones comerciales como servicios."""

    @property
    def classifier_name(self) -> str:
        return "commercial_condition_service_classifier"

    @property
    def classifier_label(self) -> str:
        return "Clasificador de Servicios — Condiciones Comerciales"

    @property
    def classifier_type(self) -> ServiceClassifierType:
        return ServiceClassifierType.COMMERCIAL_CONDITION

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.COMMERCIAL_CONDITION


class ObservationServiceClassifier(_BaseServiceClassifier):
    """Clasifica observaciones como servicios."""

    @property
    def classifier_name(self) -> str:
        return "observation_service_classifier"

    @property
    def classifier_label(self) -> str:
        return "Clasificador de Servicios — Observaciones"

    @property
    def classifier_type(self) -> ServiceClassifierType:
        return ServiceClassifierType.OBSERVATION

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.OBSERVATION


class TechnicalElementServiceClassifier(_BaseServiceClassifier):
    """Clasifica elementos técnicos como servicios."""

    @property
    def classifier_name(self) -> str:
        return "technical_element_service_classifier"

    @property
    def classifier_label(self) -> str:
        return "Clasificador de Servicios — Elementos Técnicos"

    @property
    def classifier_type(self) -> ServiceClassifierType:
        return ServiceClassifierType.TECHNICAL_ELEMENT

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.TECHNICAL_ELEMENT
