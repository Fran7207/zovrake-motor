"""Ejecutor de clasificadores del Material Classification Engine."""

from __future__ import annotations

from zovrake_motor.classification.material_classification.builders import build_material_catalog
from zovrake_motor.classification.material_classification.enums import MaterialClassificationStatus
from zovrake_motor.classification.material_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.material_classification.models import (
    MaterialClassificationIncident,
    MaterialClassificationResult,
    MaterialRecord,
)
from zovrake_motor.classification.material_classification.registry import MaterialClassifierRegistry
from zovrake_motor.config.categories.classification import MaterialClassificationSettings


class MaterialClassificationExecutor:
    """Coordina la ejecución secuencial de clasificadores sin modificar el catálogo CAE."""

    def __init__(self, registry: MaterialClassifierRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: ConceptCatalogView,
        *,
        settings: MaterialClassificationSettings,
    ) -> MaterialClassificationResult:
        materials: list[MaterialRecord] = []
        incidents: list[MaterialClassificationIncident] = []
        observations: list[str] = []
        sequence = 1

        for classifier in self._registry.all_classifiers():
            result = classifier.classify(catalog_view, start_sequence=sequence)
            materials.extend(result.materials)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.materials)

        if len(materials) > settings.max_materials_per_process:
            incidents.append(
                MaterialClassificationIncident(
                    classifier_name="material_classification_executor",
                    message=(
                        f"Se clasificaron {len(materials)} materiales; "
                        f"límite configurado: {settings.max_materials_per_process}"
                    ),
                    severity="warning",
                ),
            )
            materials = materials[: settings.max_materials_per_process]

        catalog = build_material_catalog(
            catalog_view=catalog_view,
            materials=tuple(materials),
            service_classification_prepared=settings.service_classification_prepared,
            normalization_prepared=settings.normalization_prepared,
            equivalence_detection_prepared=settings.equivalence_detection_prepared,
            comparable_group_builder_prepared=settings.comparable_group_builder_prepared,
        )

        status = MaterialClassificationStatus.CLASSIFIED if materials else MaterialClassificationStatus.SKIPPED
        observations.extend(
            (
                "concept_catalog_preserved=True",
                "internal_model_unmodified=True",
                "original_document_unaccessed=True",
                f"materials_classified={len(materials)}",
            ),
        )

        return MaterialClassificationResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            concept_catalog_preserved=True,
            classifiers_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
