"""Transformador de la sección Observaciones."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalObservation,
    CanonicalTraceability,
    SectionTransformationResult,
    TransformationIncident,
)
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.canonical.port import ObservationsTransformerPort
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ObservationsTransformer(ObservationsTransformerPort):
    """Responsabilidad: transformar observaciones e incidencias de extracción."""

    @property
    def transformer_name(self) -> str:
        return "observations_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Observaciones"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.OBSERVATIONS

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_observations(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Observaciones transformadas desde incidencias y notas de extracción",
        )

    def build_observations(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalObservation, ...]:
        section_ref = source_reference(traceability.extraction_reference_id, self.section_type)
        observations: list[CanonicalObservation] = []

        for index, incident in enumerate(extraction_result.incidents):
            observations.append(
                CanonicalObservation(
                    observation_id=f"incident-{index}",
                    content=incident.message,
                    source_reference=f"{section_ref}/incident/{index}",
                    observation_type="extraction_incident",
                    fields={
                        "extractor_name": incident.extractor_name,
                        "severity": incident.severity.value,
                    },
                ),
            )

        for index, note in enumerate(extraction_result.technical_observations):
            observations.append(
                CanonicalObservation(
                    observation_id=f"note-{index}",
                    content=note,
                    source_reference=f"{section_ref}/note/{index}",
                    observation_type="technical_observation",
                ),
            )

        raw_observations = metadata_value(extraction_result, "observations", ())
        if isinstance(raw_observations, (list, tuple)):
            for index, observation_data in enumerate(raw_observations):
                if isinstance(observation_data, dict):
                    observations.append(
                        CanonicalObservation(
                            observation_id=str(
                                observation_data.get("observation_id", f"meta-observation-{index}"),
                            ),
                            content=str(observation_data.get("content", "")),
                            source_reference=f"{section_ref}/metadata/{index}",
                            observation_type=str(observation_data.get("observation_type", "")),
                            fields=observation_data,
                        ),
                    )

        return tuple(observations)
