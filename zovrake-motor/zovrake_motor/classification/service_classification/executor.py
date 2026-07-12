"""Ejecutor de clasificadores del Service Classification Engine."""

from __future__ import annotations

from zovrake_motor.classification.service_classification.builders import build_service_catalog
from zovrake_motor.classification.service_classification.enums import ServiceClassificationStatus
from zovrake_motor.classification.service_classification.gateway import ConceptCatalogView
from zovrake_motor.classification.service_classification.models import (
    ServiceClassificationIncident,
    ServiceClassificationResult,
    ServiceRecord,
)
from zovrake_motor.classification.service_classification.registry import ServiceClassifierRegistry
from zovrake_motor.config.categories.classification import ServiceClassificationSettings


class ServiceClassificationExecutor:
    """Coordina la ejecución secuencial de clasificadores sin modificar el catálogo CAE."""

    def __init__(self, registry: ServiceClassifierRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: ConceptCatalogView,
        *,
        settings: ServiceClassificationSettings,
    ) -> ServiceClassificationResult:
        services: list[ServiceRecord] = []
        incidents: list[ServiceClassificationIncident] = []
        observations: list[str] = []
        sequence = 1

        for classifier in self._registry.all_classifiers():
            result = classifier.classify(catalog_view, start_sequence=sequence)
            services.extend(result.services)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.services)

        if len(services) > settings.max_services_per_process:
            incidents.append(
                ServiceClassificationIncident(
                    classifier_name="service_classification_executor",
                    message=(
                        f"Se clasificaron {len(services)} servicios; "
                        f"límite configurado: {settings.max_services_per_process}"
                    ),
                    severity="warning",
                ),
            )
            services = services[: settings.max_services_per_process]

        catalog = build_service_catalog(
            catalog_view=catalog_view,
            services=tuple(services),
            normalization_prepared=settings.normalization_prepared,
            equivalence_detection_prepared=settings.equivalence_detection_prepared,
            comparable_group_builder_prepared=settings.comparable_group_builder_prepared,
        )

        status = ServiceClassificationStatus.CLASSIFIED if services else ServiceClassificationStatus.SKIPPED
        observations.extend(
            (
                "concept_catalog_preserved=True",
                "internal_model_unmodified=True",
                "material_catalog_untouched=True",
                "original_document_unaccessed=True",
                f"services_classified={len(services)}",
            ),
        )

        return ServiceClassificationResult(
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
