"""Ejecutor de detectores del Equivalence Detection Engine."""

from __future__ import annotations

from zovrake_motor.classification.equivalence_detection.builders import build_equivalence_catalog
from zovrake_motor.classification.equivalence_detection.enums import EquivalenceDetectionStatus
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogView
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceDetectionIncident,
    EquivalenceDetectionResult,
    EquivalenceRecord,
)
from zovrake_motor.classification.equivalence_detection.registry import EquivalenceDetectorRegistry
from zovrake_motor.config.categories.classification import EquivalenceDetectionSettings


class EquivalenceDetectionExecutor:
    """Coordina la ejecución secuencial de detectores sin modificar el catálogo normalizado."""

    def __init__(self, registry: EquivalenceDetectorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: NormalizedConceptCatalogView,
        *,
        settings: EquivalenceDetectionSettings,
    ) -> EquivalenceDetectionResult:
        equivalences: list[EquivalenceRecord] = []
        incidents: list[EquivalenceDetectionIncident] = []
        observations: list[str] = []
        sequence = 1

        for detector in self._registry.all_detectors():
            result = detector.detect(catalog_view, start_sequence=sequence)
            equivalences.extend(result.equivalences)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.equivalences)

        if len(equivalences) > settings.max_equivalences_per_process:
            incidents.append(
                EquivalenceDetectionIncident(
                    detector_name="equivalence_detection_executor",
                    message=(
                        f"Se detectaron {len(equivalences)} relaciones; "
                        f"límite configurado: {settings.max_equivalences_per_process}"
                    ),
                    severity="warning",
                ),
            )
            equivalences = equivalences[: settings.max_equivalences_per_process]

        catalog = build_equivalence_catalog(
            catalog_view=catalog_view,
            equivalences=tuple(equivalences),
            comparable_group_builder_prepared=settings.comparable_group_builder_prepared,
            context_association_prepared=settings.context_association_prepared,
            comparative_domain_model_prepared=settings.comparative_domain_model_prepared,
        )

        status = (
            EquivalenceDetectionStatus.DETECTED if equivalences else EquivalenceDetectionStatus.SKIPPED
        )
        observations.extend(
            (
                "normalized_catalog_preserved=True",
                "original_values_unmodified=True",
                "original_document_unaccessed=True",
                f"equivalences_detected={len(equivalences)}",
            ),
        )

        return EquivalenceDetectionResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            normalized_catalog_preserved=True,
            detectors_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
