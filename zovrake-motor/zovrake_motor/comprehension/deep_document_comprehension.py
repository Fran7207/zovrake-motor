"""Comprensión profunda unificada y determinista de DocumentKnowledge.

Esta capa no vuelve a leer el PDF. Toma la evidencia ya adquirida y la
convierte en una representación semántica más rica para las capas posteriores.
No utiliza LLM, tokenizer externo ni modelos/servicios remotos.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from decimal import Decimal, InvalidOperation
import re
from hashlib import sha256
from typing import Any

from zovrake_motor.comprehension.models import (
    DocumentEvidence,
    DocumentKnowledge,
    DocumentRelationship,
)


class DeepDocumentComprehensionEngine:
    """Integra contexto, entidades, hechos, visual y relaciones documentales."""

    MODEL_VERSION = "1.0-unified-deep-deterministic"

    _LABEL_ALIASES = {
        "costo": "cost",
        "coste": "cost",
        "precio": "price",
        "precio unitario": "unit_price",
        "importe": "amount",
        "total": "total",
        "subtotal": "subtotal",
        "cantidad": "quantity",
        "unidad": "unit",
        "producto": "product",
        "material": "material",
        "servicio": "service",
        "marca": "brand",
        "modelo": "model",
        "codigo": "code",
        "código": "code",
        "sku": "sku",
        "serie": "serial_number",
        "moneda": "currency",
        "forma de pago": "payment_method",
        "condiciones de pago": "payment_terms",
        "tiempo de entrega": "delivery_time",
        "plazo de entrega": "delivery_time",
        "lugar de entrega": "delivery_location",
        "validez": "validity",
        "vigencia": "validity",
        "garantia": "warranty",
        "garantía": "warranty",
        "ruc": "tax_id",
        "razon social": "legal_name",
        "razón social": "legal_name",
    }

    _UNIT_FACTORS = {
    }

    _MONEY_RE = re.compile(
        r"(?P<prefix>US\$|U\$S|S\.?/|S\/\.?|€|£|¥|\$)?\s*"
        r"(?P<number>\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)"
        r"\s*(?P<currency>PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL)?",
        re.IGNORECASE,
    )

    def comprehend(self, knowledge: DocumentKnowledge) -> DocumentKnowledge:
        if not isinstance(knowledge, DocumentKnowledge):
            raise TypeError("knowledge debe ser una instancia de DocumentKnowledge")

        semantic_concepts = self._build_semantic_concepts(knowledge)
        document_profile = self._build_document_profile(knowledge, semantic_concepts)
        consistency = self._evaluate_consistency(knowledge)
        cross_region_links = self._build_cross_region_links(knowledge)
        semantic_index = self._build_semantic_index(knowledge, semantic_concepts)

        relationships = list(knowledge.relationships)
        relationships.extend(cross_region_links)
        relationships = self._dedupe_relationships(relationships)

        unresolved = list(knowledge.unresolved)
        unresolved.extend(consistency["unresolved"])

        semantic_confidence = self._semantic_confidence(
            knowledge=knowledge,
            semantic_concepts=semantic_concepts,
            consistency=consistency,
        )

        metadata = dict(knowledge.metadata)
        metadata.update(
            {
                "deep_comprehension_model_version": self.MODEL_VERSION,
                "deep_comprehension_stage": "unified_semantic_reasoning",
                "deep_comprehension_profile": document_profile,
                "deep_semantic_concepts": semantic_concepts,
                "deep_semantic_index": semantic_index,
                "deep_consistency": consistency["summary"],
                "deep_cross_region_relationship_count": len(cross_region_links),
                "deep_comprehension_confidence": semantic_confidence,
                "deep_comprehension_unresolved_count": len(unresolved),
            }
        )

        return replace(
            knowledge,
            relationships=tuple(relationships),
            unresolved=tuple(unresolved),
            confidence=semantic_confidence,
            metadata=metadata,
        )

    def _build_semantic_concepts(
        self,
        knowledge: DocumentKnowledge,
    ) -> list[dict[str, Any]]:
        concepts: list[dict[str, Any]] = []

        for attribute in knowledge.attributes:
            label = self._normalize(attribute.get("name") or attribute.get("raw_label"))
            value = self._clean(attribute.get("value"))
            if not label or not value:
                continue

            canonical = self._LABEL_ALIASES.get(label, label)
            concepts.append(
                {
                    "concept_id": self._concept_id(attribute, canonical, value),
                    "kind": "attribute",
                    "name": canonical,
                    "raw_label": label,
                    "value": value,
                    "normalized_value": self._normalize_value(canonical, value),
                    "page_number": attribute.get("page_number"),
                    "region_id": attribute.get("region_id", ""),
                    "evidence_id": attribute.get("evidence_id", ""),
                    "confidence": float(attribute.get("confidence", 0.0) or 0.0),
                }
            )

        for fact in knowledge.facts:
            label = self._normalize(fact.get("normalized_label") or fact.get("label"))
            value = self._clean(fact.get("raw_value"))
            if not label or not value:
                continue
            canonical = self._LABEL_ALIASES.get(label, label)
            concepts.append(
                {
                    "concept_id": self._concept_id(fact, canonical, value),
                    "kind": "fact",
                    "name": canonical,
                    "raw_label": label,
                    "value": value,
                    "normalized_value": self._normalize_value(canonical, value),
                    "page_number": fact.get("page_number"),
                    "region_id": fact.get("region_id", ""),
                    "evidence_id": fact.get("evidence_id", ""),
                    "confidence": float(fact.get("confidence", 0.0) or 0.0),
                    "fact_type": fact.get("fact_type", ""),
                }
            )

        # Las observaciones visuales también son conceptos documentales.
        for image in knowledge.images:
            visual = image.get("visual_understanding") or {}
            if not visual:
                continue
            concepts.append(
                {
                    "concept_id": f"visual:{image.get('image_id', '')}",
                    "kind": "visual",
                    "name": str(visual.get("object_type", "visual_content")),
                    "description": str(visual.get("description", "")),
                    "detected_text": str(visual.get("detected_text", "")),
                    "semantic_hints": list(visual.get("semantic_hints", ())),
                    "page_number": image.get("page_number"),
                    "confidence": float(visual.get("visual_confidence", 0.0) or 0.0),
                    "source_image_id": image.get("image_id", ""),
                }
            )

        return self._dedupe_concepts(concepts)

    def _build_document_profile(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        roles = defaultdict(int)
        concept_names = defaultdict(int)

        for entity in knowledge.entities:
            roles[entity.role or "unknown"] += 1

        for concept in concepts:
            concept_names[concept.get("name", "unknown")] += 1

        commercial_signals = sum(
            1
            for name in concept_names
            if name in {"price", "unit_price", "total", "quantity", "product", "material", "service"}
        )
        condition_signals = sum(
            1
            for name in concept_names
            if name in {"payment_method", "payment_terms", "delivery_time", "delivery_location", "validity", "warranty"}
        )

        if commercial_signals >= 2:
            document_kind = "commercial_document"
        elif knowledge.images or knowledge.tables:
            document_kind = "structured_document"
        else:
            document_kind = "general_document"

        return {
            "document_kind": document_kind,
            "page_count": knowledge.page_count,
            "entity_roles": dict(roles),
            "commercial_signal_count": commercial_signals,
            "condition_signal_count": condition_signals,
            "concept_count": len(concepts),
            "entity_count": len(knowledge.entities),
            "fact_count": len(knowledge.facts),
            "image_count": len(knowledge.images),
            "table_count": len(knowledge.tables),
            "relationship_count": len(knowledge.relationships),
        }

    def _evaluate_consistency(
        self,
        knowledge: DocumentKnowledge,
    ) -> dict[str, Any]:
        unresolved: list[dict[str, Any]] = []
        contradictions: list[dict[str, Any]] = []
        numeric_checks: list[dict[str, Any]] = []

        # Agrupar hechos por nombre canónico y detectar valores incompatibles
        # cuando aparecen en la misma región/documento sin contexto separador.
        groups: dict[tuple[str, int | None], list[dict[str, Any]]] = defaultdict(list)
        for fact in knowledge.facts:
            label = self._LABEL_ALIASES.get(
                self._normalize(fact.get("normalized_label") or fact.get("label")),
                self._normalize(fact.get("normalized_label") or fact.get("label")),
            )
            groups[(label, fact.get("page_number"))].append(fact)

        for (label, page_number), facts in groups.items():
            values = {
                self._normalize_value(label, self._clean(f.get("raw_value")))
                for f in facts
                if self._clean(f.get("raw_value"))
            }
            if len(values) > 1 and label in {"currency", "payment_method", "payment_terms", "validity"}:
                unresolved.append(
                    {
                        "type": "contextual_variation",
                        "label": label,
                        "page_number": page_number,
                        "values": sorted(values),
                        "message": "Se detectaron valores distintos y se conservan separados por contexto.",
                    }
                )

        # Verificaciones matemáticas cuando existen cantidad, precio unitario y total.
        for fact in knowledge.facts:
            if self._LABEL_ALIASES.get(self._normalize(fact.get("normalized_label") or fact.get("label"))) != "total":
                continue
            page = fact.get("page_number")
            total = self._to_decimal(fact.get("normalized_value") or fact.get("raw_value"))
            if total is None:
                continue
            qty = self._nearest_numeric_concept(knowledge, page, {"quantity"})
            unit_price = self._nearest_numeric_concept(knowledge, page, {"unit_price", "price"})
            if qty is None or unit_price is None:
                continue
            expected = qty * unit_price
            delta = abs(expected - total)
            ok = delta <= max(Decimal("0.01"), abs(total) * Decimal("0.005"))
            numeric_checks.append(
                {
                    "page_number": page,
                    "quantity": str(qty),
                    "unit_price": str(unit_price),
                    "reported_total": str(total),
                    "expected_total": str(expected),
                    "delta": str(delta),
                    "status": "consistent" if ok else "inconsistent",
                }
            )
            if not ok:
                contradictions.append(numeric_checks[-1])

        return {
            "summary": {
                "contradiction_count": len(contradictions),
                "contextual_variation_count": len(unresolved),
                "numeric_check_count": len(numeric_checks),
                "numeric_inconsistency_count": len(contradictions),
            },
            "numeric_checks": numeric_checks,
            "contradictions": contradictions,
            "unresolved": unresolved,
        }

    def _build_cross_region_links(
        self,
        knowledge: DocumentKnowledge,
    ) -> list[DocumentRelationship]:
        links: list[DocumentRelationship] = []

        # Conecta una entidad con conceptos/atributos cercanos únicamente cuando
        # comparten evidencia o región, evitando asociaciones arbitrarias.
        for entity in knowledge.entities:
            for concept in self._build_semantic_concepts(knowledge):
                evidence_id = str(concept.get("evidence_id", "")).strip()
                region_id = str(concept.get("region_id", "")).strip()
                entity_region = str(entity.attributes.get("source_region_id", "")).strip()
                same_evidence = evidence_id and evidence_id in set(entity.evidence_ids)
                same_region = region_id and entity_region and region_id == entity_region
                if not same_evidence and not same_region:
                    continue
                if concept.get("kind") not in {"attribute", "fact"}:
                    continue
                relation_type = "entity_has_attribute" if concept.get("kind") == "attribute" else "entity_has_fact"
                links.append(
                    DocumentRelationship(
                        relationship_id=f"deep:{entity.entity_id}:{concept['concept_id']}:{relation_type}",
                        source_id=entity.entity_id,
                        relationship_type=relation_type,
                        target_id=concept["concept_id"],
                        confidence=min(1.0, max(0.0, float(concept.get("confidence", 0.0)) + (0.2 if same_evidence else 0.05))),
                        evidence_ids=tuple(
                            dict.fromkeys(
                                list(entity.evidence_ids) + ([evidence_id] if evidence_id else [])
                            )
                        ),
                        metadata={
                            "reason": "shared_evidence" if same_evidence else "shared_region",
                            "concept_name": concept.get("name", ""),
                        },
                    )
                )
        return links

    def _build_semantic_index(
        self,
        knowledge: DocumentKnowledge,
        concepts: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        index: dict[str, list[str]] = defaultdict(list)
        for concept in concepts:
            name = str(concept.get("name", "")).strip()
            value = str(concept.get("normalized_value", "")).strip()
            cid = str(concept.get("concept_id", "")).strip()
            if name and cid:
                index[f"concept:{name}"].append(cid)
            if value and cid:
                index[f"value:{value}"].append(cid)

        for entity in knowledge.entities:
            if entity.name:
                index[f"entity:{self._normalize(entity.name)}"].append(entity.entity_id)
            if entity.identifier:
                index[f"identifier:{self._normalize(entity.identifier)}"].append(entity.entity_id)
        return {key: list(dict.fromkeys(values)) for key, values in index.items()}

    def _nearest_numeric_concept(
        self,
        knowledge: DocumentKnowledge,
        page: int | None,
        allowed_names: set[str],
    ) -> Decimal | None:
        candidates: list[tuple[int, Decimal]] = []
        for fact in knowledge.facts:
            if fact.get("page_number") != page:
                continue
            label = self._LABEL_ALIASES.get(
                self._normalize(fact.get("normalized_label") or fact.get("label")),
                self._normalize(fact.get("normalized_label") or fact.get("label")),
            )
            if label not in allowed_names:
                continue
            value = self._to_decimal(fact.get("normalized_value") or fact.get("raw_value"))
            if value is not None:
                candidates.append((0, value))
        return candidates[0][1] if candidates else None

    @staticmethod
    def _semantic_confidence(
        *,
        knowledge: DocumentKnowledge,
        semantic_concepts: list[dict[str, Any]],
        consistency: dict[str, Any],
    ) -> float:
        signals: list[float] = []
        signals.extend(
            float(entity.confidence)
            for entity in knowledge.entities
            if entity.confidence > 0
        )
        signals.extend(
            float(concept.get("confidence", 0.0))
            for concept in semantic_concepts
            if float(concept.get("confidence", 0.0)) > 0
        )
        base = sum(signals) / len(signals) if signals else 0.0
        penalty = min(0.35, 0.08 * consistency["summary"]["contradiction_count"])
        return round(max(0.0, min(1.0, base - penalty)), 4)

    @staticmethod
    def _clean(value: Any) -> str:
        return " ".join(str(value or "").replace("\x00", " ").split()).strip()

    @staticmethod
    def _normalize(value: Any) -> str:
        import unicodedata
        text = " ".join(str(value or "").split()).strip().casefold()
        return "".join(
            char
            for char in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(char)
        )

    def _normalize_value(self, label: str, value: str) -> str:
        normalized = self._clean(value).casefold()
        if label in {"price", "unit_price", "amount", "total", "subtotal", "cost"}:
            decimal_value = self._to_decimal(normalized)
            return format(decimal_value, "f") if decimal_value is not None else normalized
        if label in {"tax_id", "code", "sku", "serial_number"}:
            return re.sub(r"[^a-z0-9]", "", self._normalize(normalized))
        return self._normalize(normalized)

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        text = str(value or "").strip()
        if not text:
            return None
        match = DeepDocumentComprehensionEngine._MONEY_RE.search(text)
        candidate = match.group("number") if match else text
        candidate = candidate.replace(" ", "")
        try:
            if "." in candidate and "," in candidate:
                if candidate.rfind(",") > candidate.rfind("."):
                    candidate = candidate.replace(".", "").replace(",", ".")
                else:
                    candidate = candidate.replace(",", "")
            elif candidate.count(",") == 1 and candidate.count(".") == 0:
                candidate = candidate.replace(",", ".")
            elif candidate.count(",") > 1 and candidate.count(".") == 0:
                candidate = candidate.replace(",", "")
            elif candidate.count(".") > 1 and candidate.count(",") == 0:
                candidate = candidate.replace(".", "")
            return Decimal(candidate)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _concept_id(source: dict[str, Any], name: str, value: str) -> str:
        source_id = str(
            source.get("attribute_id")
            or source.get("fact_id")
            or source.get("evidence_id")
            or "source"
        )
        value_digest = sha256(
            value.encode("utf-8", errors="ignore")
        ).hexdigest()[:16]
        return f"concept:{source_id}:{name}:{value_digest}"

    @staticmethod
    def _dedupe_concepts(concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for concept in concepts:
            cid = str(concept.get("concept_id", ""))
            if not cid or cid in seen:
                continue
            seen.add(cid)
            result.append(concept)
        return result

    @staticmethod
    def _dedupe_relationships(
        relationships: list[DocumentRelationship],
    ) -> list[DocumentRelationship]:
        seen: set[str] = set()
        result: list[DocumentRelationship] = []
        for relationship in relationships:
            key = (
                f"{relationship.source_id}|{relationship.relationship_type}|"
                f"{relationship.target_id}"
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(relationship)
        return result


__all__ = ["DeepDocumentComprehensionEngine"]
