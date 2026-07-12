"""Contrato base de clasificadores del Service Classification Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.service_classification.enums import ServiceClassifierType
from zovrake_motor.classification.service_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.service_classification.models import ClassifierResult


class ServiceClassifierPort(ABC):
    """
    Contrato común para clasificadores de servicios.

    Cada clasificador identifica servicios de un tipo de concepto del CAE.
    """

    @property
    @abstractmethod
    def classifier_name(self) -> str:
        """Identificador único del clasificador."""

    @property
    @abstractmethod
    def classifier_label(self) -> str:
        """Etiqueta descriptiva del clasificador."""

    @property
    @abstractmethod
    def classifier_type(self) -> ServiceClassifierType:
        """Tipo de conceptos que clasifica."""

    @property
    @abstractmethod
    def supported_concept_kind(self) -> ConceptKind:
        """Tipo de concepto CAE soportado."""

    @abstractmethod
    def classify(self, catalog_view: ConceptCatalogView, *, start_sequence: int) -> ClassifierResult:
        """Clasifica servicios — sin modificar el catálogo de conceptos."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "classifier_name": self.classifier_name,
            "classifier_label": self.classifier_label,
            "classifier_type": self.classifier_type.value,
            "supported_concept_kind": self.supported_concept_kind.value,
        }
