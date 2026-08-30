"""Vinculación determinista entre hechos, atributos y entidades documentales."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from typing import Any, Iterable

from zovrake_motor.comprehension.models import (
    DocumentEntity,
    DocumentKnowledge,
    DocumentRelationship,
)


class DocumentFactEntityLinker:
    """
    Relaciona hechos y atributos con entidades documentales.

    Esta capa NO vuelve a leer el PDF ni vuelve a extraer información.

    Utiliza solamente la información que ya está presente en
    DocumentKnowledge:

    - región;
    - página;
    - evidence_id;
    - sección semántica;
    - rol de la entidad;
    - identificador;
    - nombre;
    - tipo de atributo.

    Si dos entidades podrían recibir el mismo hecho con evidencia similar,
    no se crea una relación arbitraria.

    Principio:
        evidencia compartida -> contexto -> puntuación -> relación
    """

    MODEL_VERSION = "1.0-deterministic-fact-entity-linking"

    _IDENTITY_ATTRIBUTES = {
        "legal_name",
        "name",
        "tax_id",
        "identity_document",
        "email",
        "phone",
        "address",
    }

    _ROLE_SECTION = {
        "provider": "provider_identity",
        "customer": "customer_identity",
        "manufacturer": "technical",
        "representative": "provider_identity",
    }

    def link(
        self,
        knowledge: DocumentKnowledge,
    ) -> DocumentKnowledge:
        """
        Añade relaciones fact_belongs_to / attribute_belongs_to.

        La representación original es inmutable y se devuelve una copia.
        """
        if not isinstance(
            knowledge,
            DocumentKnowledge,
        ):
            raise TypeError(
                "knowledge debe ser una instancia de DocumentKnowledge"
            )

        evidence_by_id = {
            evidence.evidence_id: evidence
            for evidence in knowledge.evidence
        }

        relationships: list[
            DocumentRelationship
        ] = []

        for fact in knowledge.facts:
            selected = self._resolve_fact_target(
                fact=fact,
                entities=knowledge.entities,
                evidence_by_id=evidence_by_id,
            )

            if selected is None:
                continue

            entity, score, reasons = selected

            relationships.append(
                self._relationship(
                    source_id=str(
                        fact.get(
                            "fact_id",
                            "",
                        )
                    ),
                    entity=entity,
                    fact=fact,
                    score=score,
                    reasons=reasons,
                    relationship_type="fact_belongs_to",
                )
            )

        # Los atributos producidos por DocumentFactExtractor usan el mismo
        # fact_id como attribute_id cuando provienen de labeled_value/table_field.
        existing_fact_ids = {
            str(
                fact.get(
                    "fact_id",
                    "",
                )
            )
            for fact in knowledge.facts
        }

        for attribute in knowledge.attributes:
            attribute_id = str(
                attribute.get(
                    "attribute_id",
                    "",
                )
            ).strip()

            if not attribute_id:
                continue

            # Evitamos duplicar exactamente la relación que ya fue generada
            # desde el hecho de origen.
            if attribute_id in existing_fact_ids:
                continue

            synthetic_fact = {
                "fact_id": attribute_id,
                "fact_type": "attribute",
                "label": attribute.get(
                    "raw_label",
                    "",
                ),
                "normalized_label": attribute.get(
                    "name",
                    "",
                ),
                "raw_value": attribute.get(
                    "value",
                    "",
                ),
                "normalized_value": attribute.get(
                    "normalized_value",
                ),
                "page_number": attribute.get(
                    "page_number",
                ),
                "region_id": attribute.get(
                    "region_id",
                    "",
                ),
                "evidence_id": attribute.get(
                    "evidence_id",
                    "",
                ),
                "semantic_context": attribute.get(
                    "semantic_context",
                    "unknown",
                ),
            }

            selected = self._resolve_fact_target(
                fact=synthetic_fact,
                entities=knowledge.entities,
                evidence_by_id=evidence_by_id,
            )

            if selected is None:
                continue

            entity, score, reasons = selected

            relationships.append(
                self._relationship(
                    source_id=attribute_id,
                    entity=entity,
                    fact=synthetic_fact,
                    score=score,
                    reasons=reasons,
                    relationship_type=(
                        "attribute_belongs_to"
                    ),
                )
            )

        merged = self._merge(
            knowledge.relationships,
            relationships,
        )

        metadata = dict(
            knowledge.metadata
        )

        linked_sources = {
            relationship.source_id
            for relationship in relationships
        }

        metadata.update(
            {
                "fact_entity_linking_model_version": (
                    self.MODEL_VERSION
                ),
                "fact_entity_linking_stage": (
                    "fact_to_entity_resolution"
                ),
                "fact_entity_link_count": len(
                    relationships
                ),
                "linked_fact_or_attribute_count": len(
                    linked_sources
                ),
                "relationship_count": len(
                    merged
                ),
            }
        )

        return replace(
            knowledge,
            relationships=tuple(
                merged
            ),
            metadata=metadata,
        )

    def _resolve_fact_target(
        self,
        *,
        fact: dict[str, Any],
        entities: tuple[DocumentEntity, ...],
        evidence_by_id: dict[str, Any],
    ) -> tuple[
        DocumentEntity,
        float,
        tuple[str, ...],
    ] | None:
        if not entities:
            return None

        scored: list[
            tuple[
                DocumentEntity,
                float,
                tuple[str, ...],
            ]
        ] = []

        fact_evidence_id = str(
            fact.get(
                "evidence_id",
                "",
            )
        ).strip()

        fact_region_id = str(
            fact.get(
                "region_id",
                "",
            )
        ).strip()

        fact_page = fact.get(
            "page_number"
        )

        semantic_context = self._normalize(
            str(
                fact.get(
                    "semantic_context",
                    "unknown",
                )
            )
        )

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

        raw_value = self._normalize(
            str(
                fact.get(
                    "raw_value",
                    "",
                )
            )
        )

        fact_type = self._normalize(
            str(
                fact.get(
                    "fact_type",
                    "",
                )
            )
        )

        for entity in entities:
            score = 0.0
            reasons: list[str] = []

            entity_evidence = set(
                entity.evidence_ids
            )

            # -----------------------------------------------------
            # Evidencia compartida: señal más fuerte.
            # -----------------------------------------------------
            if (
                fact_evidence_id
                and fact_evidence_id
                in entity_evidence
            ):
                score += 0.55
                reasons.append(
                    "shared_evidence"
                )

            # -----------------------------------------------------
            # Misma región.
            # -----------------------------------------------------
            entity_region = str(
                entity.attributes.get(
                    "source_region_id",
                    "",
                )
            ).strip()

            if (
                fact_region_id
                and entity_region
                and fact_region_id
                == entity_region
            ):
                score += 0.20
                reasons.append(
                    "same_region"
                )

            # -----------------------------------------------------
            # Misma página.
            # -----------------------------------------------------
            entity_page = entity.attributes.get(
                "source_page_number"
            )

            if (
                fact_page is not None
                and entity_page is not None
                and fact_page == entity_page
            ):
                score += 0.10
                reasons.append(
                    "same_page"
                )

            # -----------------------------------------------------
            # Contexto semántico compatible con el rol.
            # -----------------------------------------------------
            expected_section = self._ROLE_SECTION.get(
                entity.role.strip().lower()
            )

            if (
                expected_section
                and semantic_context
                == self._normalize(
                    expected_section
                )
            ):
                score += 0.15
                reasons.append(
                    "role_section_match"
                )

            # -----------------------------------------------------
            # Atributos de identidad.
            # -----------------------------------------------------
            if (
                label
                in self._IDENTITY_ATTRIBUTES
                and entity.role.strip().lower()
                in {
                    "provider",
                    "customer",
                    "manufacturer",
                    "representative",
                }
            ):
                score += 0.05
                reasons.append(
                    "identity_attribute"
                )

            # -----------------------------------------------------
            # Coincidencia del valor con nombre/identificador.
            # -----------------------------------------------------
            entity_name = self._normalize(
                entity.name
            )

            entity_identifier = self._normalize(
                entity.identifier
            )

            if raw_value:
                if (
                    entity_identifier
                    and raw_value
                    == entity_identifier
                ):
                    score += 0.18
                    reasons.append(
                        "value_matches_identifier"
                    )
                elif (
                    entity_name
                    and (
                        raw_value
                        == entity_name
                        or raw_value
                        in entity_name
                        or entity_name
                        in raw_value
                    )
                ):
                    score += 0.15
                    reasons.append(
                        "value_matches_name"
                    )

            # -----------------------------------------------------
            # Hechos de identidad reciben una pequeña prioridad
            # cuando la entidad ya tiene identificador.
            # -----------------------------------------------------
            if (
                fact_type == "identifier"
                and entity.identifier
            ):
                score += 0.05
                reasons.append(
                    "identifier_fact_with_identified_entity"
                )

            evidence = (
                evidence_by_id.get(
                    fact_evidence_id
                )
                if fact_evidence_id
                else None
            )

            if evidence is not None:
                evidence_page = evidence.page_number

                if (
                    evidence_page is not None
                    and entity_page is not None
                    and evidence_page
                    == entity_page
                ):
                    score += 0.03
                    reasons.append(
                        "evidence_page_match"
                    )

            if score > 0.0:
                scored.append(
                    (
                        entity,
                        min(
                            score,
                            1.0,
                        ),
                        tuple(
                            dict.fromkeys(
                                reasons
                            )
                        ),
                    )
                )

        scored.sort(
            key=lambda item: (
                item[1],
                item[0].confidence,
            ),
            reverse=True,
        )

        if not scored:
            return None

        best = scored[0]
        best_entity = best[0]
        best_score = best[1]
        best_reasons = best[2]

        # Umbral conservador.
        if best_score < 0.60:
            return None

        if len(scored) == 1:
            return best

        second_score = scored[1][1]

        # Cuando dos entidades pueden explicar el mismo hecho, no
        # asignamos arbitrariamente.
        if (
            best_score - second_score
            < 0.12
        ):
            return None

        return (
            best_entity,
            best_score,
            best_reasons,
        )

    @classmethod
    def _relationship(
        cls,
        *,
        source_id: str,
        entity: DocumentEntity,
        fact: dict[str, Any],
        score: float,
        reasons: Iterable[str],
        relationship_type: str,
    ) -> DocumentRelationship:
        raw_id = "|".join(
            (
                source_id,
                entity.entity_id,
                relationship_type,
            )
        )

        relationship_id = (
            "relationship-"
            + sha256(
                raw_id.encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        evidence_id = str(
            fact.get(
                "evidence_id",
                "",
            )
        ).strip()

        evidence_ids = (
            (evidence_id,)
            if evidence_id
            else ()
        )

        confidence = round(
            min(
                1.0,
                score
                * (
                    0.70
                    + (
                        0.30
                        * entity.confidence
                    )
                ),
            ),
            4,
        )

        return DocumentRelationship(
            relationship_id=relationship_id,
            source_id=source_id,
            relationship_type=relationship_type,
            target_id=entity.entity_id,
            confidence=confidence,
            evidence_ids=evidence_ids,
            metadata={
                "resolution_method": (
                    "deterministic_context_evidence"
                ),
                "reasons": list(
                    dict.fromkeys(
                        reasons
                    )
                ),
                "page_number": fact.get(
                    "page_number"
                ),
                "region_id": fact.get(
                    "region_id",
                    "",
                ),
                "fact_type": fact.get(
                    "fact_type",
                    "",
                ),
            },
        )

    @staticmethod
    def _merge(
        existing: tuple[
            DocumentRelationship,
            ...
        ],
        new: Iterable[
            DocumentRelationship
        ],
    ) -> list[
        DocumentRelationship
    ]:
        """
        Fusiona relaciones evitando duplicados por source/type/target.
        """
        merged: list[
            DocumentRelationship
        ] = []

        seen: set[
            tuple[str, str, str]
        ] = set()

        for relationship in (
            *existing,
            *tuple(new),
        ):
            signature = (
                relationship.source_id,
                relationship.relationship_type,
                relationship.target_id,
            )

            if signature in seen:
                continue

            seen.add(signature)
            merged.append(
                relationship
            )

        return merged

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            str(value)
            .casefold()
            .split()
        )