"""Registro centralizado de clasificadores del MCE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.material_classification.classifiers import (
    ItemMaterialClassifier,
    PartidaMaterialClassifier,
)
from zovrake_motor.classification.material_classification.exceptions import MaterialClassifierNotFoundError
from zovrake_motor.classification.material_classification.port import MaterialClassifierPort
from zovrake_motor.config.categories.classification import MaterialClassificationSettings


class MaterialClassifierRegistry:
    """
    Registro único de clasificadores de materiales.

    Todo clasificador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._classifiers_by_name: dict[str, MaterialClassifierPort] = {}
        self._classifiers_ordered: list[MaterialClassifierPort] = []

    def register(self, classifier: MaterialClassifierPort) -> None:
        if classifier.classifier_name in self._classifiers_by_name:
            raise ValueError(f"Clasificador ya registrado: {classifier.classifier_name}")
        self._classifiers_by_name[classifier.classifier_name] = classifier
        self._classifiers_ordered.append(classifier)

    def register_defaults(self, *, settings: MaterialClassificationSettings | None = None) -> None:
        settings = settings or MaterialClassificationSettings.default()
        candidates: list[tuple[bool, MaterialClassifierPort]] = [
            (settings.item_classifier_enabled, ItemMaterialClassifier()),
            (settings.partida_classifier_enabled, PartidaMaterialClassifier()),
        ]
        for enabled, classifier in candidates:
            if enabled:
                self.register(classifier)

    def get(self, name: str) -> MaterialClassifierPort | None:
        return self._classifiers_by_name.get(name)

    def require(self, name: str) -> MaterialClassifierPort:
        classifier = self.get(name)
        if classifier is None:
            raise MaterialClassifierNotFoundError(f"Clasificador no registrado: {name}")
        return classifier

    def all_classifiers(self) -> tuple[MaterialClassifierPort, ...]:
        return tuple(self._classifiers_ordered)

    def count(self) -> int:
        return len(self._classifiers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [classifier.snapshot() for classifier in self._classifiers_ordered]
