"""Registro centralizado de clasificadores del SCE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.service_classification.classifiers import (
    CommercialConditionServiceClassifier,
    ObservationServiceClassifier,
    TechnicalElementServiceClassifier,
)
from zovrake_motor.classification.service_classification.exceptions import ServiceClassifierNotFoundError
from zovrake_motor.classification.service_classification.port import ServiceClassifierPort
from zovrake_motor.config.categories.classification import ServiceClassificationSettings


class ServiceClassifierRegistry:
    """
    Registro único de clasificadores de servicios.

    Todo clasificador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._classifiers_by_name: dict[str, ServiceClassifierPort] = {}
        self._classifiers_ordered: list[ServiceClassifierPort] = []

    def register(self, classifier: ServiceClassifierPort) -> None:
        if classifier.classifier_name in self._classifiers_by_name:
            raise ValueError(f"Clasificador ya registrado: {classifier.classifier_name}")
        self._classifiers_by_name[classifier.classifier_name] = classifier
        self._classifiers_ordered.append(classifier)

    def register_defaults(self, *, settings: ServiceClassificationSettings | None = None) -> None:
        settings = settings or ServiceClassificationSettings.default()
        candidates: list[tuple[bool, ServiceClassifierPort]] = [
            (settings.commercial_condition_classifier_enabled, CommercialConditionServiceClassifier()),
            (settings.observation_classifier_enabled, ObservationServiceClassifier()),
            (settings.technical_element_classifier_enabled, TechnicalElementServiceClassifier()),
        ]
        for enabled, classifier in candidates:
            if enabled:
                self.register(classifier)

    def get(self, name: str) -> ServiceClassifierPort | None:
        return self._classifiers_by_name.get(name)

    def require(self, name: str) -> ServiceClassifierPort:
        classifier = self.get(name)
        if classifier is None:
            raise ServiceClassifierNotFoundError(f"Clasificador no registrado: {name}")
        return classifier

    def all_classifiers(self) -> tuple[ServiceClassifierPort, ...]:
        return tuple(self._classifiers_ordered)

    def count(self) -> int:
        return len(self._classifiers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [classifier.snapshot() for classifier in self._classifiers_ordered]
