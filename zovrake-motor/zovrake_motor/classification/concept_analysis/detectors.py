"""Detectores especializados del Concept Analysis Engine."""

from __future__ import annotations

from zovrake_motor.classification.concept_analysis.builders import build_concept
from zovrake_motor.classification.concept_analysis.enums import (
    ConceptDetectorType,
    ConceptKind,
)
from zovrake_motor.classification.concept_analysis.gateway import InternalModelView
from zovrake_motor.classification.concept_analysis.models import DetectorResult
from zovrake_motor.classification.concept_analysis.port import ConceptDetectorPort


class ItemConceptDetector(ConceptDetectorPort):
    """Identifica partidas e ítems del modelo interno como conceptos candidatos."""

    @property
    def detector_name(self) -> str:
        return "item_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Ítems y Partidas"

    @property
    def detector_type(self) -> ConceptDetectorType:
        return ConceptDetectorType.ITEM

    def detect(
        self,
        model_view: InternalModelView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = []
        sequence = start_sequence

        for index, item in enumerate(model_view.items):
            description = str(
                item.get("description", "")
            ).strip()

            if not description:
                continue

            kind = (
                ConceptKind.PARTIDA
                if item.get("quantity") or item.get("unit")
                else ConceptKind.ITEM
            )

            raw_fields = item.get(
                "fields",
                {},
            )

            if isinstance(raw_fields, dict):
                item_fields = dict(raw_fields)
            else:
                item_fields = {}

            semantic_values = item_fields.get(
                "values",
                {},
            )

            if isinstance(
                semantic_values,
                dict,
            ):
                normalized_semantic_values = dict(
                    semantic_values
                )
            else:
                normalized_semantic_values = {}

            semantic_columns = item_fields.get(
                "semantic_columns",
                (),
            )

            if isinstance(
                semantic_columns,
                (list, tuple),
            ):
                normalized_semantic_columns = tuple(
                    str(column).strip()
                    for column in semantic_columns
                    if str(column).strip()
                )
            else:
                normalized_semantic_columns = ()

            metadata = {
                "item_id": item.get(
                    "item_id",
                    "",
                ),
                "quantity": item.get(
                    "quantity",
                    "",
                ),
                "unit": item.get(
                    "unit",
                    "",
                ),
                "unit_price": item.get(
                    "unit_price",
                    "",
                ),
                "fields": item_fields,
                "semantic_values": normalized_semantic_values,
                "semantic_columns": normalized_semantic_columns,
            }

            # Las columnas semánticas descubiertas por el documento
            # también quedan disponibles directamente para las capas
            # posteriores, sin perder su representación original.
            for key, value in normalized_semantic_values.items():
                normalized_key = str(
                    key
                ).strip()

                if not normalized_key:
                    continue

                if normalized_key not in metadata:
                    metadata[normalized_key] = value

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=kind,
                    original_description=description,
                    section="items",
                    entity_id=str(
                        item.get(
                            "entity_id",
                            item.get(
                                "item_id",
                                f"item-{index}",
                            ),
                        )
                    ),
                    source_reference=str(
                        item.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        item.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        item.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    entity_index=index,
                    metadata=metadata,
                ),
            )

            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"items_scanned={len(model_view.items)}",
            ),
        )


class TechnicalConceptDetector(ConceptDetectorPort):
    """Identifica elementos técnicos y especificaciones del modelo interno."""

    @property
    def detector_name(self) -> str:
        return "technical_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Elementos Técnicos"

    @property
    def detector_type(self) -> ConceptDetectorType:
        return ConceptDetectorType.TECHNICAL

    def detect(
        self,
        model_view: InternalModelView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = []
        sequence = start_sequence
        technical = model_view.technical_information
        entity_id = str(
            technical.get(
                "entity_id",
                "technical_information",
            )
        )

        for index, specification in enumerate(
            technical.get("specifications", ())
        ):
            description = str(specification).strip()

            if not description:
                continue

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.TECHNICAL_ELEMENT,
                    original_description=description,
                    section="technical_information",
                    entity_id=entity_id,
                    source_reference=str(
                        technical.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        technical.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        technical.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    entity_index=index,
                    field_name="specifications",
                ),
            )

            sequence += 1

        for field_name, value in technical.get(
            "fields",
            {},
        ).items():
            description = str(value).strip()

            if not description:
                continue

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.TECHNICAL_ELEMENT,
                    original_description=description,
                    section="technical_information",
                    entity_id=entity_id,
                    source_reference=str(
                        technical.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        technical.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        technical.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    field_name=str(field_name),
                ),
            )

            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                "technical_section_scanned=True",
            ),
        )


class CommercialConceptDetector(ConceptDetectorPort):
    """Identifica elementos comerciales del modelo interno."""

    COMMERCIAL_FIELDS: tuple[tuple[str, str], ...] = (
        ("currency", "Moneda"),
        ("total_amount", "Monto total"),
        ("payment_terms", "Condiciones de pago"),
    )

    @property
    def detector_name(self) -> str:
        return "commercial_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Elementos Comerciales"

    @property
    def detector_type(self) -> ConceptDetectorType:
        return ConceptDetectorType.COMMERCIAL

    def detect(
        self,
        model_view: InternalModelView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = []
        sequence = start_sequence
        commercial = model_view.commercial_information
        entity_id = str(
            commercial.get(
                "entity_id",
                "commercial_information",
            )
        )

        for field_name, label in self.COMMERCIAL_FIELDS:
            description = str(
                commercial.get(
                    field_name,
                    "",
                )
            ).strip()

            if not description:
                continue

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.COMMERCIAL_ELEMENT,
                    original_description=f"{label}: {description}",
                    section="commercial_information",
                    entity_id=entity_id,
                    source_reference=str(
                        commercial.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        commercial.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        commercial.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    field_name=field_name,
                    metadata={
                        "commercial_field": field_name,
                    },
                ),
            )

            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                "commercial_section_scanned=True",
            ),
        )


class CommercialConditionDetector(ConceptDetectorPort):
    """Identifica condiciones comerciales como conceptos candidatos."""

    @property
    def detector_name(self) -> str:
        return "condition_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Condiciones Comerciales"

    @property
    def detector_type(self) -> ConceptDetectorType:
        return ConceptDetectorType.CONDITION

    def detect(
        self,
        model_view: InternalModelView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = []
        sequence = start_sequence

        for index, condition in enumerate(
            model_view.commercial_conditions
        ):
            description = str(
                condition.get(
                    "content",
                    "",
                )
            ).strip()

            if not description:
                continue

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.COMMERCIAL_CONDITION,
                    original_description=description,
                    section="commercial_conditions",
                    entity_id=str(
                        condition.get(
                            "entity_id",
                            condition.get(
                                "condition_id",
                                f"cond-{index}",
                            ),
                        )
                    ),
                    source_reference=str(
                        condition.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        condition.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        condition.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    entity_index=index,
                    metadata={
                        "condition_type": condition.get(
                            "condition_type",
                            "",
                        )
                    },
                ),
            )

            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"conditions_scanned="
                f"{len(model_view.commercial_conditions)}",
            ),
        )


class ObservationConceptDetector(ConceptDetectorPort):
    """Identifica observaciones de negocio como conceptos candidatos.

    Las observaciones técnicas y las incidencias generadas por las capas
    de extracción/comprensión permanecen en el modelo documental para
    trazabilidad, pero no se convierten en conceptos de negocio.
    """

    EXCLUDED_OBSERVATION_TYPES: frozenset[str] = frozenset(
        {
            "extraction_incident",
            "technical_observation",
        }
    )

    @property
    def detector_name(self) -> str:
        return "observation_detector"

    @property
    def detector_label(self) -> str:
        return "Detector de Observaciones"

    @property
    def detector_type(self) -> ConceptDetectorType:
        return ConceptDetectorType.OBSERVATION

    def detect(
        self,
        model_view: InternalModelView,
        *,
        start_sequence: int,
    ) -> DetectorResult:
        concepts = []
        sequence = start_sequence

        for index, observation in enumerate(
            model_view.observations
        ):
            observation_type = str(
                observation.get(
                    "observation_type",
                    "",
                )
            ).strip().lower()

            # Las incidencias del extractor y las observaciones
            # técnicas describen el funcionamiento/proceso de
            # comprensión. Se conservan en el Modelo Documental
            # Interno para trazabilidad, pero NO son conceptos de
            # negocio ni deben entrar en clasificación,
            # normalización o comparación.
            if observation_type in self.EXCLUDED_OBSERVATION_TYPES:
                continue

            description = str(
                observation.get(
                    "content",
                    "",
                )
            ).strip()

            if not description:
                continue

            concepts.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.OBSERVATION,
                    original_description=description,
                    section="observations",
                    entity_id=str(
                        observation.get(
                            "entity_id",
                            observation.get(
                                "observation_id",
                                f"obs-{index}",
                            ),
                        )
                    ),
                    source_reference=str(
                        observation.get(
                            "source_reference",
                            "",
                        )
                    ),
                    canonical_reference=str(
                        observation.get(
                            "canonical_reference",
                            "",
                        )
                    ),
                    extraction_reference=str(
                        observation.get(
                            "extraction_reference",
                            "",
                        )
                    ),
                    entity_index=index,
                    metadata={
                        "observation_type": observation.get(
                            "observation_type",
                            "",
                        )
                    },
                ),
            )

            sequence += 1

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"observations_scanned="
                f"{len(model_view.observations)}",
            ),
        )