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
    """
    Identifica partidas/ítems y, cuando no existe una lista estructurada,
    recupera candidatos desde el conocimiento semántico del documento.

    La ruta tradicional sigue teniendo prioridad. La ruta semántica funciona
    como fallback para que un PDF con información distribuida en texto/tablas
    no quede sin conceptos candidatos.
    """

    _SEMANTIC_DESCRIPTION_LABELS = {
        "description",
        "descripcion",
        "descripción",
        "item",
        "ítem",
        "producto",
        "product",
        "servicio",
        "service",
        "concepto",
        "material",
        "detalle",
        "detalle del producto",
        "nombre del producto",
        "nombre del servicio",
    }

    _EXCLUDED_SEMANTIC_LABELS = {
        "legal_name",
        "name",
        "tax_id",
        "identity_document",
        "email",
        "phone",
        "address",
        "bank",
        "account",
        "bank_account_cci",
        "bank_account_swift",
        "bank_account_iban",
        "price",
        "unit_price",
        "amount",
        "total",
        "subtotal",
        "discount",
        "tax",
        "percentage",
        "date",
        "payment_method",
        "payment_terms",
        "delivery_time",
        "validity",
        "warranty",
    }

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

        # ---------------------------------------------------------
        # Ruta principal: estructura de ítems ya normalizada.
        # ---------------------------------------------------------
        for index, item in enumerate(
            model_view.items
        ):
            description = str(
                item.get(
                    "description",
                    "",
                )
            ).strip()

            if not description:
                continue

            kind = (
                ConceptKind.PARTIDA
                if item.get("quantity")
                or item.get("unit")
                else ConceptKind.ITEM
            )

            raw_fields = item.get(
                "fields",
                {},
            )

            if isinstance(
                raw_fields,
                dict,
            ):
                item_fields = dict(
                    raw_fields
                )
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
                "knowledge_enrichment_used": False,
            }

            for key, value in normalized_semantic_values.items():
                normalized_key = str(
                    key
                ).strip()

                if not normalized_key:
                    continue

                if normalized_key not in metadata:
                    metadata[
                        normalized_key
                    ] = value

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

        # ---------------------------------------------------------
        # Fallback semántico:
        # si el modelo interno no contiene items estructurados,
        # utilizamos el conocimiento documental ya transportado.
        #
        # NO convertimos RUC, totales, bancos, fechas, etc. en conceptos.
        # Solo usamos hechos cuyo campo representa razonablemente un
        # producto/servicio/concepto descriptivo.
        # ---------------------------------------------------------
        semantic_concepts = self._detect_semantic_candidates(
            model_view=model_view,
            start_sequence=sequence,
        )

        concepts.extend(
            semantic_concepts
        )

        return DetectorResult(
            detector_type=self.detector_type,
            detector_name=self.detector_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"items_scanned={len(model_view.items)}",
                (
                    "semantic_fallback_used=True"
                    if not model_view.items
                    and bool(
                        semantic_concepts
                    )
                    else "semantic_fallback_used=False"
                ),
                (
                    f"semantic_fallback_candidates="
                    f"{len(semantic_concepts)}"
                ),
            ),
        )

    def _detect_semantic_candidates(
        self,
        *,
        model_view: InternalModelView,
        start_sequence: int,
    ) -> tuple[Any, ...]:
        if model_view.items:
            return ()

        if not model_view.has_document_knowledge:
            return ()

        facts = model_view.knowledge_facts

        if not facts:
            return ()

        relationship_by_fact: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for relationship in model_view.knowledge_relationships:
            source_id = str(
                relationship.get(
                    "source_id",
                    "",
                )
            ).strip()

            if not source_id:
                continue

            relationship_by_fact.setdefault(
                source_id,
                [],
            ).append(
                relationship
            )

        candidates: list[Any] = []
        seen: set[
            tuple[str, str, str]
        ] = set()

        sequence = start_sequence

        for fact in facts:
            fact_id = str(
                fact.get(
                    "fact_id",
                    "",
                )
            ).strip()

            if not fact_id:
                continue

            label = self._normalize(
                str(
                    fact.get(
                        "normalized_label",
                        fact.get(
                            "label",
                            "",
                        ),
                    )
                )
            )

            if not self._is_semantic_description_label(
                label
            ):
                continue

            raw_value = str(
                fact.get(
                    "raw_value",
                    "",
                )
            ).strip()

            if not self._valid_semantic_description(
                raw_value
            ):
                continue

            source_kind = str(
                fact.get(
                    "source_kind",
                    "",
                )
            ).strip()

            page_number = fact.get(
                "page_number"
            )

            region_id = str(
                fact.get(
                    "region_id",
                    "",
                )
            ).strip()

            signature = (
                label,
                self._normalize(raw_value),
                region_id,
            )

            if signature in seen:
                continue

            seen.add(signature)

            entity_id = self._linked_entity_id(
                fact_id=fact_id,
                relationships=relationship_by_fact,
            )

            metadata = {
                "semantic_source": True,
                "knowledge_fact_id": fact_id,
                "knowledge_fact_type": fact.get(
                    "fact_type",
                    "",
                ),
                "knowledge_label": fact.get(
                    "label",
                    "",
                ),
                "knowledge_normalized_label": label,
                "knowledge_raw_value": raw_value,
                "knowledge_page_number": page_number,
                "knowledge_region_id": region_id,
                "knowledge_evidence_id": fact.get(
                    "evidence_id",
                    "",
                ),
                "knowledge_source_kind": source_kind,
                "knowledge_confidence": fact.get(
                    "confidence",
                    0.0,
                ),
                "linked_entity_id": entity_id,
                "knowledge_relationships": relationship_by_fact.get(
                    fact_id,
                    [],
                ),
            }

            candidates.append(
                build_concept(
                    model_view=model_view,
                    sequence=sequence,
                    kind=ConceptKind.ITEM,
                    original_description=raw_value,
                    section=self._semantic_section(
                        fact
                    ),
                    entity_id=(
                        entity_id
                        or region_id
                        or "semantic-document"
                    ),
                    source_reference=(
                        f"knowledge://fact/{fact_id}"
                    ),
                    canonical_reference="",
                    extraction_reference=(
                        str(
                            fact.get(
                                "evidence_id",
                                "",
                            )
                        )
                    ),
                    entity_index=None,
                    field_name=label,
                    metadata=metadata,
                )
            )

            sequence += 1

        return tuple(
            candidates
        )

    def _is_semantic_description_label(
        self,
        label: str,
    ) -> bool:
        normalized = self._normalize(
            label
        )

        if (
            normalized
            in self._EXCLUDED_SEMANTIC_LABELS
        ):
            return False

        if (
            normalized
            in self._SEMANTIC_DESCRIPTION_LABELS
        ):
            return True

        # También permitimos etiquetas descriptivas no presentes en el
        # diccionario cuando contienen una señal léxica fuerte.
        tokens = set(
            normalized.split()
        )

        return bool(
            tokens
            & {
                "producto",
                "productos",
                "servicio",
                "servicios",
                "material",
                "materiales",
                "item",
                "ítem",
                "concepto",
                "descripcion",
                "descripción",
                "detalle",
            }
        )

    @staticmethod
    def _valid_semantic_description(
        value: str,
    ) -> bool:
        normalized = " ".join(
            value.split()
        )

        if len(normalized) < 3:
            return False

        if normalized.casefold() in {
            "n/a",
            "na",
            "no aplica",
            "no especificado",
            "pendiente",
            "sin especificar",
        }:
            return False

        # Una descripción de concepto no debe ser exclusivamente numérica.
        if not any(
            character.isalpha()
            for character in normalized
        ):
            return False

        return True

    @staticmethod
    def _linked_entity_id(
        *,
        fact_id: str,
        relationships: dict[
            str,
            list[dict[str, Any]],
        ],
    ) -> str:
        candidates = relationships.get(
            fact_id,
            [],
        )

        for relationship in candidates:
            relationship_type = str(
                relationship.get(
                    "relationship_type",
                    "",
                )
            )

            if relationship_type in {
                "fact_belongs_to",
                "attribute_belongs_to",
            }:
                target = str(
                    relationship.get(
                        "target_id",
                        "",
                    )
                ).strip()

                if target:
                    return target

        return ""

    @staticmethod
    def _semantic_section(
        fact: dict[str, Any],
    ) -> str:
        section = str(
            fact.get(
                "semantic_context",
                "",
            )
        ).strip()

        return (
            section
            if section
            else "document_knowledge"
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            value.casefold().split()
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