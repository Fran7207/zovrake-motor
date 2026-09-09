"""Interpretación semántica universal de DocumentKnowledge, local y trazable."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import re
from typing import Any, Iterable

from zovrake_motor.comprehension.models import DocumentKnowledge
from zovrake_motor.comprehension.document_semantic_lexicon import DocumentSemanticLexicon


@dataclass(frozen=True)
class UniversalSemanticObservation:
    observation_id: str
    page_number: int | None
    source_id: str
    source_type: str
    text: str
    semantic_role: str
    confidence: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "page_number": self.page_number,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "text": self.text,
            "semantic_role": self.semantic_role,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


class UniversalDocumentSemanticReasoner:
    """Construye un grafo semántico conservador a partir de evidencia existente."""

    MODEL_VERSION = "3.0-universal-evidence-graph-semantic-ontology"

    _LEGAL_ENTITY = re.compile(
        r"(?i)([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ0-9&.,'()\- ]{2,120}?"
        r"(?:S\.\s*A\.\s*C\.?|S\.A\.C\.?|SAC|S\.\s*R\.\s*L\.?|"
        r"S\.R\.L\.?|SRL|E\.\s*I\.\s*R\.\s*L\.?|EIRL|"
        r"S\.A\.?|SA|LTDA\.?|LIMITADA))"
    )
    _RUC = re.compile(
        r"(?i)\bR\.?\s*U\.?\s*C\.?(?:\s*(?:[:\-]\s*)+|\s+)(\d{11})\b"
    )
    _LABEL_VALUE = re.compile(
        r"^\s*(?P<label>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9./_%()\- ]{2,100})"
        r"\s*[:=]\s*(?P<value>.+?)\s*$"
    )
    _ROLE_MARKERS = {
        "provider": (
            "proveedor", "proveedora", "supplier", "vendor", "seller", "emisor",
            "emisor", "vendedor", "cotizado por", "cotiza por", "titular",
            "depositar a nombre", "cuentas bancarias", "cuentas a nombre",
            "atentamente", "quedamos de ustedes", "nuestra empresa",
        ),
        "customer": (
            "cliente", "comprador", "buyer", "customer", "destinatario", "señor",
            "señores", "cotizado a", "facturar a", "datos del cliente",
        ),
        "manufacturer": ("fabricante", "manufacturer"),
        "representative": ("representante", "asesor", "ejecutivo comercial"),
        "bank": ("banco", "bank", "cuenta bancaria", "cci", "iban", "swift"),
    }
    _SEMANTIC_LABELS = {
        "precio": "price", "precio unitario": "unit_price", "p.unit": "unit_price",
        "p/unit": "unit_price", "p/unit.": "unit_price", "unit price": "unit_price",
        "cantidad": "quantity", "cant": "quantity", "qty": "quantity",
        "unidad": "unit", "und": "unit", "unid": "unit", "medida": "unit",
        "producto": "product", "productos": "product", "descripcion": "description",
        "descripción": "description", "concepto": "concept", "material": "material",
        "servicio": "service", "marca": "brand", "modelo": "model", "codigo": "code",
        "código": "code", "sku": "sku", "serie": "serial_number", "ruc": "tax_id",
        "razon social": "legal_name", "razón social": "legal_name", "moneda": "currency",
        "forma de pago": "payment_method", "medio de pago": "payment_method",
        "condiciones de pago": "payment_terms", "tiempo de entrega": "delivery_time",
        "plazo de entrega": "delivery_time", "lugar de entrega": "delivery_location",
        "garantia": "warranty", "garantía": "warranty", "validez": "validity",
        "vigencia": "validity", "correo": "email", "email": "email",
        "telefono": "phone", "teléfono": "phone", "direccion": "address",
        "dirección": "address", "fecha": "date", "total": "total",
        "subtotal": "subtotal", "sub total": "subtotal", "igv": "tax", "iva": "tax",
        "importe": "amount", "monto": "amount", "costo": "cost", "coste": "cost",
    }
    _MONEY = re.compile(
        r"(?i)(?:US\$|U\$S|S\/?\.?|PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|CAD|€|£|¥|\$)"
        r"\s*[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|"
        r"[-+]?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s*(?:PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|CAD|€|£|¥|\$)"
    )
    _MEASUREMENT = re.compile(
        r"(?i)\b[-+]?\d+(?:[.,]\d+)?\s*(?:mm|cm|m2|m²|m3|m³|m|km|kg|g|mg|t|tn|l|lt|ml|w|kw|mw|v|kv|a|ma|hz|bar|psi|pa|kpa|mpa|°c|c|%|dias|días|meses|años|years)\b"
    )

    def analyze(self, knowledge: DocumentKnowledge) -> dict[str, Any]:
        if not isinstance(knowledge, DocumentKnowledge):
            raise TypeError("knowledge debe ser una instancia de DocumentKnowledge")

        observations = self._build_observations(knowledge)
        fields = self._build_fields(observations)
        semantic_dictionary = self._build_semantic_dictionary(knowledge, observations)
        mentions = self._build_entity_mentions(observations)
        roles = self._build_role_candidates(observations, knowledge.entities, mentions)
        visuals = self._build_visuals(knowledge)
        relations = self._build_relations(observations, mentions, roles)
        typed = self._build_typed_values(observations, fields)
        numeric = self._build_numeric_reasoning(knowledge)
        conflicts = self._build_conflicts(roles, fields)
        multimodal = self._build_multimodal_reasoning(knowledge, observations, mentions, fields, visuals, roles)
        resolved_roles = self._resolve_role_conclusions(roles, conflicts=self._build_conflicts(roles, fields))
        conflicts = self._build_conflicts(roles, fields)
        entity_profiles = self._build_entity_profiles(
            knowledge=knowledge,
            mentions=mentions,
            roles=roles,
            resolved_roles=resolved_roles,
            fields=fields,
            visuals=visuals,
        )
        semantic_graph = self._build_semantic_graph(
            entity_profiles=entity_profiles,
            relations=relations,
            multimodal=multimodal,
            numeric=numeric,
        )
        coverage = self._build_coverage(knowledge, observations, visuals)
        page_summary = self._build_page_summary(knowledge, observations)
        understanding = self._build_document_understanding(
            knowledge=knowledge,
            mentions=mentions,
            fields=fields,
            roles=roles,
            resolved_roles=resolved_roles,
            visuals=visuals,
            relations=relations,
            multimodal=multimodal,
            numeric=numeric,
            conflicts=conflicts,
        )

        return {
            "model_version": self.MODEL_VERSION,
            "schema_version": "universal-semantic-understanding-v1",
            "stage": "evidence_graph_reasoning",
            "document_id": knowledge.document_id,
            "document_kind": self._infer_document_kind(knowledge, fields),
            "semantic_dictionary": semantic_dictionary,
            "observations": [item.to_dict() for item in observations],
            "semantic_fields": fields,
            "entity_mentions": mentions,
            "role_candidates": roles,
            "resolved_roles": resolved_roles,
            "entity_profiles": entity_profiles,
            "semantic_graph": semantic_graph,
            "visual_understanding": visuals,
            "relations": relations,
            "multimodal_reasoning": multimodal,
            "document_understanding": understanding,
            "typed_values": typed,
            "numeric_reasoning": numeric,
            "conflicts": conflicts,
            "page_summary": page_summary,
            "coverage": coverage,
            "answer_context": {
                "document_summary": {
                    "file_name": knowledge.file_name,
                    "page_count": knowledge.page_count,
                    "entity_names": list(dict.fromkeys(item["name"] for item in mentions)),
                    "semantic_keys": sorted({item["semantic_key"] for item in fields}),
                },
                "ordered_evidence": [
                    {
                        "sequence": index,
                        "page_number": obs.page_number,
                        "source_id": obs.source_id,
                        "type": obs.source_type,
                        "text": obs.text,
                        "confidence": obs.confidence,
                    }
                    for index, obs in enumerate(observations, 1)
                ],
                "entities": mentions,
                "fields": fields,
                "semantic_dictionary": semantic_dictionary,
                "entity_profiles": entity_profiles,
                "semantic_graph": semantic_graph,
                "visual": visuals,
                "resolved_roles": resolved_roles,
                "multimodal_reasoning": multimodal,
                "document_understanding": understanding,
            },
        }

    def _build_observations(self, knowledge: DocumentKnowledge) -> list[UniversalSemanticObservation]:
        result: list[UniversalSemanticObservation] = []
        for entry in knowledge.reading_order:
            source_id = str(entry.get("source_id") or "")
            if not source_id:
                continue
            metadata = entry.get("metadata") or {}
            visual = metadata.get("visual_understanding") or {}
            result.append(UniversalSemanticObservation(
                observation_id=f"obs:{self._digest(source_id + '|' + str(entry.get('text') or ''))}",
                page_number=self._as_int(entry.get("page_number")),
                source_id=source_id,
                source_type=str(entry.get("content_type") or "unknown"),
                text=str(entry.get("text") or "").strip(),
                semantic_role=str(visual.get("object_type") or ""),
                confidence=self._confidence(entry.get("confidence")),
                metadata={
                    "bbox": entry.get("bbox"),
                    "source_kind": entry.get("source_kind"),
                    "entry_metadata": metadata,
                },
            ))
        known = {item.source_id for item in result}
        for region in knowledge.regions:
            if not region.content.strip() or region.region_id in known:
                continue
            result.append(UniversalSemanticObservation(
                observation_id=f"obs:region:{self._digest(region.region_id)}",
                page_number=region.page_number,
                source_id=region.region_id,
                source_type=region.region_type,
                text=region.content.strip(),
                semantic_role=str(region.metadata.get("semantic_section") or ""),
                confidence=self._confidence(region.confidence),
                metadata={"bbox": region.bbox, "source_kind": region.source_kind},
            ))
        return result

    def _build_fields(self, observations: list[UniversalSemanticObservation]) -> list[dict[str, Any]]:
        result = []
        for obs in observations:
            match = self._LABEL_VALUE.match(obs.text)
            if not match:
                continue
            raw_label = " ".join(match.group("label").split())
            value = " ".join(match.group("value").split())
            semantic_key = self._canonical_label(raw_label)
            lexical_match = DocumentSemanticLexicon.match(raw_label)
            if lexical_match and lexical_match.confidence >= 0.80:
                semantic_key = lexical_match.semantic_key
            if not semantic_key:
                continue
            result.append({
                "field_id": f"field:{self._digest(obs.observation_id + raw_label + value)}",
                "semantic_key": semantic_key,
                "raw_label": raw_label,
                "value": value,
                "page_number": obs.page_number,
                "source_id": obs.source_id,
                "observation_id": obs.observation_id,
                "confidence": round(min(0.999, obs.confidence * (lexical_match.confidence if lexical_match else 1.0)), 4),
                "meaning": self._semantic_meaning(semantic_key),
                "lexical_match": (
                    {
                        "alias": lexical_match.matched_alias,
                        "confidence": lexical_match.confidence,
                    }
                    if lexical_match
                    else None
                ),
            })
        return self._dedupe_dicts(result, ("semantic_key", "raw_label", "value", "page_number", "source_id"))

    def _build_semantic_dictionary(
        self,
        knowledge: DocumentKnowledge,
        observations: list[UniversalSemanticObservation],
    ) -> list[dict[str, Any]]:
        """Construye un inventario de significados observados, no solo de alias conocidos."""
        terms: list[str] = []
        for obs in observations:
            match = self._LABEL_VALUE.match(obs.text)
            if match:
                terms.append(match.group("label"))
            # También capturamos palabras suficientemente estables como
            # títulos/encabezados, pero no pretendemos definir cada token del
            # idioma como si tuviéramos un diccionario general.
            if obs.source_type in {"table", "semantic_table"}:
                for token in re.split(r"\|", obs.text):
                    token = " ".join(token.split())
                    if 2 <= len(token) <= 80:
                        terms.append(token)
        terms.extend(
            field.get("raw_label", "")
            for field in self._build_fields(observations)
        )
        unique = list(dict.fromkeys(t for t in terms if str(t).strip()))
        return DocumentSemanticLexicon.explain(unique)

    @staticmethod
    def _semantic_meaning(semantic_key: str) -> str:
        meanings = {
            "provider": "entidad que suministra, vende, cotiza o emite el bien/servicio según la evidencia documental",
            "customer": "entidad destinataria o compradora según la evidencia documental",
            "manufacturer": "entidad que fabrica o produce el bien",
            "product": "bien, artículo o producto identificado en el documento",
            "description": "texto que describe o identifica el concepto/bien/servicio",
            "quantity": "cantidad numérica asociada a un concepto",
            "unit": "unidad, medida o presentación en la que se expresa una cantidad",
            "price": "valor económico expresado como precio",
            "unit_price": "valor económico por unidad de medida o presentación",
            "amount": "importe monetario asociado a un concepto",
            "total": "importe final o total declarado en el contexto correspondiente",
            "subtotal": "importe intermedio antes de impuestos u otros ajustes",
            "tax": "impuesto aplicado a una operación o importe",
            "cost": "costo económico asociado a un concepto",
            "currency": "moneda en la que se expresa un importe",
            "payment_method": "medio o forma mediante la que se realiza el pago",
            "payment_terms": "condiciones, plazos o reglas acordadas para el pago",
            "delivery_time": "plazo o tiempo de entrega",
            "delivery_location": "lugar al que se entrega el bien o servicio",
            "warranty": "garantía ofrecida para el bien o servicio",
            "validity": "periodo durante el cual la oferta o condición mantiene vigencia",
            "tax_id": "identificador fiscal de una entidad o persona",
            "email": "dirección de correo electrónico",
            "phone": "número telefónico de contacto",
            "address": "dirección o domicilio",
            "date": "fecha documentada",
            "reference": "referencia, proyecto, obra o identificador contextual",
            "brand": "marca comercial asociada a un bien",
            "model": "modelo o variante del bien",
            "code": "código identificador del concepto",
            "technical_specification": "característica o especificación técnica",
            "certificate": "certificación o documento que acredita una condición",
        }
        return meanings.get(
            semantic_key,
            "concepto documental identificado a partir de evidencia y contexto; requiere validación contextual adicional",
        )

    def _build_entity_mentions(self, observations: list[UniversalSemanticObservation]) -> list[dict[str, Any]]:
        result = []
        for obs in observations:
            for match in self._LEGAL_ENTITY.finditer(obs.text):
                name = self._extract_legal_entity_name(match.group(1))
                local = obs.text[max(0, match.start() - 90):match.end() + 120]
                ruc = self._extract_ruc(local)
                result.append({
                    "mention_id": f"mention:{self._digest(obs.observation_id + name)}",
                    "name": name,
                    "normalized_name": self._normalize(name),
                    "identifier": ruc,
                    "page_number": obs.page_number,
                    "source_id": obs.source_id,
                    "observation_id": obs.observation_id,
                    "context": local,
                    "confidence": min(0.99, obs.confidence + (0.08 if ruc else 0.0)),
                })
        return self._dedupe_dicts(result, ("normalized_name", "identifier", "page_number", "source_id"))

    def _build_role_candidates(self, observations: list[UniversalSemanticObservation], entities: Iterable[Any], mentions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        states: dict[tuple[str, str, str], dict[str, Any]] = {}
        def get(role: str, name: str, identifier: str = ""):
            key = (role, self._normalize(name), identifier)
            return states.setdefault(key, {
                "candidate_id": f"role:{role}:{self._digest(self._normalize(name) + '|' + identifier)}",
                "role": role, "name": name, "identifier": identifier,
                "score": 0.0, "confidence": 0.0, "evidence": [], "source_ids": [],
            })
        for mention in mentions:
            context = self._normalize(mention.get("context"))
            for role, markers in self._ROLE_MARKERS.items():
                hits = [m for m in markers if self._normalize(m) in context]
                if hits:
                    state = get(role, mention["name"], mention.get("identifier", ""))
                    weights = {
                        "proveedor": 92.0, "proveedora": 92.0,
                        "supplier": 92.0, "vendor": 88.0, "seller": 84.0,
                        "emisor": 94.0, "emitter": 94.0,
                        "vendedor": 84.0, "cotizado por": 96.0,
                        "cotiza por": 94.0, "titular": 86.0,
                        "depositar a nombre": 98.0, "cuentas bancarias": 94.0,
                        "cuentas a nombre": 98.0, "atentamente": 78.0,
                        "quedamos de ustedes": 78.0, "nuestra empresa": 82.0,
                        "cliente": 92.0, "comprador": 92.0, "buyer": 92.0,
                        "customer": 92.0, "destinatario": 92.0,
                        "señor": 88.0, "señores": 94.0,
                        "cotizado a": 96.0, "facturar a": 94.0,
                        "datos del cliente": 98.0,
                    }
                    weights = {
                        self._normalize(key): value
                        for key, value in weights.items()
                    }
                    state["score"] += min(
                        100.0,
                        sum(weights.get(self._normalize(item), 16.0) for item in hits),
                    )
                    state["evidence"].extend(f"marker:{item}" for item in hits)
                    state["source_ids"].append(mention["source_id"])
        for entity in entities:
            role = str(getattr(entity, "role", "") or "").strip().lower()
            name = str(getattr(entity, "name", "") or "").strip()
            if not role or not name:
                continue
            state = get(role, name, str(getattr(entity, "identifier", "") or ""))
            entity_confidence = self._confidence(getattr(entity, "confidence", 0.0))
            state["score"] += 60.0 * entity_confidence
            if getattr(entity, "identifier", ""):
                state["score"] += 8.0
                state["evidence"].append("resolved_entity_with_identifier")
            else:
                state["evidence"].append("resolved_entity")
            state["source_ids"].extend(getattr(entity, "evidence_ids", ()) or ())
        ranked = list(states.values())
        for state in ranked:
            state["score"] = round(min(100.0, float(state["score"])), 3)
            state["confidence"] = round(min(0.999, state["score"] / 100.0), 4)
            state["evidence"] = list(dict.fromkeys(state["evidence"]))
            state["source_ids"] = list(dict.fromkeys(state["source_ids"]))
        ranked.sort(key=lambda item: (item["confidence"], item["score"]), reverse=True)
        return ranked

    @staticmethod
    def _build_visuals(knowledge: DocumentKnowledge) -> list[dict[str, Any]]:
        result = []
        for image in knowledge.images:
            visual = image.get("visual_understanding") or {}
            result.append({
                "image_id": str(image.get("image_id") or ""),
                "page_number": image.get("page_number"),
                "bbox": image.get("bbox"),
                "image_type": str(visual.get("object_type") or "image"),
                "description": str(visual.get("description") or ""),
                "detected_text": str(visual.get("detected_text") or image.get("ocr_text") or ""),
                "semantic_hints": list(visual.get("semantic_hints") or ()),
                "detected_features": list(visual.get("detected_features") or ()),
                "qr_codes": list(visual.get("qr_codes") or ()),
                "confidence": UniversalDocumentSemanticReasoner._confidence(visual.get("visual_confidence")),
                "analysis_status": str(visual.get("analysis_status") or "unknown"),
            })
        return result

    def _build_entity_profiles(self, *, knowledge, mentions, roles, resolved_roles, fields, visuals):
        """Consolida toda la evidencia conocida sobre cada entidad."""
        profiles: dict[str, dict[str, Any]] = {}

        def profile(name: str, identifier: str = "") -> dict[str, Any]:
            key = self._normalize(identifier or name)
            return profiles.setdefault(key, {
                "profile_id": f"entity-profile:{self._digest(key)}",
                "name": name,
                "normalized_name": self._normalize(name),
                "identifiers": [],
                "roles": [],
                "resolved_roles": {},
                "fields": [],
                "visual_evidence": [],
                "source_ids": [],
                "evidence_count": 0,
                "confidence": 0.0,
            })

        for mention in mentions:
            p = profile(mention.get("name", ""), mention.get("identifier", ""))
            identifier = str(mention.get("identifier") or "").strip()
            if identifier and identifier not in p["identifiers"]:
                p["identifiers"].append(identifier)
            p["source_ids"].append(mention.get("source_id"))
            p["evidence_count"] += 1
            p["confidence"] = max(p["confidence"], float(mention.get("confidence", 0.0) or 0.0))

        for candidate in roles:
            p = profile(candidate.get("name", ""), candidate.get("identifier", ""))
            role = str(candidate.get("role") or "unknown")
            if role not in p["roles"]:
                p["roles"].append(role)
            p["source_ids"].extend(candidate.get("source_ids", ()) or ())
            p["evidence_count"] += len(candidate.get("evidence", ()) or ())
            p["confidence"] = max(p["confidence"], float(candidate.get("confidence", 0.0) or 0.0))

        for decision in resolved_roles:
            p = profile(decision.get("name", ""), decision.get("identifier", ""))
            p["resolved_roles"][str(decision.get("role") or "unknown")] = {
                "decision": decision.get("decision"),
                "confidence": decision.get("confidence", 0.0),
                "margin": decision.get("decision_margin", 0.0),
                "evidence": list(decision.get("evidence", ()) or ()),
            }

        mentions_by_name = {
            self._normalize(m.get("name", "")): m
            for m in mentions
            if m.get("name")
        }
        for field in fields:
            value_norm = self._normalize(field.get("value", ""))
            if not value_norm:
                continue
            for name_norm, mention in mentions_by_name.items():
                if name_norm in value_norm or value_norm in name_norm:
                    p = profile(mention.get("name", ""), mention.get("identifier", ""))
                    p["fields"].append({
                        "semantic_key": field.get("semantic_key"),
                        "raw_label": field.get("raw_label"),
                        "value": field.get("value"),
                        "source_id": field.get("source_id"),
                    })

        for visual in visuals:
            visual_norm = self._normalize(
                " ".join([
                    visual.get("detected_text", ""),
                    visual.get("description", ""),
                    " ".join(visual.get("semantic_hints", ())),
                ])
            )
            if not visual_norm:
                continue
            for mention in mentions:
                name_norm = mention.get("normalized_name", "")
                if name_norm and name_norm in visual_norm:
                    p = profile(mention.get("name", ""), mention.get("identifier", ""))
                    p["visual_evidence"].append({
                        "image_id": visual.get("image_id"),
                        "image_type": visual.get("image_type"),
                        "detected_text": visual.get("detected_text", ""),
                        "confidence": visual.get("confidence", 0.0),
                    })

        result = []
        for p in profiles.values():
            p["source_ids"] = list(dict.fromkeys(x for x in p["source_ids"] if x))
            p["roles"] = list(dict.fromkeys(p["roles"]))
            p["fields"] = self._dedupe_dicts(p["fields"], ("semantic_key", "raw_label", "value", "source_id"))
            p["confidence"] = round(min(0.999, p["confidence"]), 4)
            p["semantic_summary"] = {
                "role_count": len(p["roles"]),
                "resolved_role_count": sum(1 for item in p["resolved_roles"].values() if item.get("decision") == "resolved"),
                "field_count": len(p["fields"]),
                "visual_evidence_count": len(p["visual_evidence"]),
            }
            result.append(p)
        result.sort(key=lambda item: (-item["confidence"], -item["evidence_count"], item["normalized_name"]))
        return result

    @staticmethod
    def _build_semantic_graph(*, entity_profiles, relations, multimodal, numeric):
        nodes = [
            {
                "node_id": p["profile_id"],
                "node_type": "entity",
                "label": p["name"],
                "roles": list(p.get("roles", ())),
                "confidence": p.get("confidence", 0.0),
            }
            for p in entity_profiles
        ]
        edges = []
        for relation in list(relations) + list(multimodal.get("evidence_links", ()) or ()):
            edges.append({
                "source_id": relation.get("source_id"),
                "target_id": relation.get("target_id"),
                "relationship_type": relation.get("relationship_type"),
                "confidence": relation.get("confidence", 0.0),
                "evidence_ids": list(relation.get("evidence_ids", ()) or ()),
            })
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "numeric_reasoning": numeric,
            "reasoning_policy": "evidence_first_entity_field_relation_graph",
        }

    def _build_relations(self, observations, mentions, roles):
        relations = []
        for mention in mentions:
            for role in roles:
                if self._normalize(role.get("name")) != mention["normalized_name"]:
                    continue
                relations.append({
                    "relationship_id": f"rel:{self._digest(mention['mention_id'] + role['candidate_id'])}",
                    "source_id": mention["mention_id"],
                    "relationship_type": "supports_role",
                    "target_id": role["candidate_id"],
                    "confidence": role["confidence"],
                    "evidence_ids": [mention["source_id"]],
                })
        return self._dedupe_dicts(relations, ("source_id", "relationship_type", "target_id"))

    def _build_multimodal_reasoning(self, knowledge, observations, mentions, fields, visuals, roles):
        """Cruza texto, tablas, geometría y visión sin inventar objetos."""
        links = []
        visual_entity_links = []
        field_entity_links = []
        page_by_source = {obs.source_id: obs.page_number for obs in observations}

        for visual in visuals:
            visual_text = self._normalize(
                " ".join(
                    [
                        visual.get("detected_text", ""),
                        visual.get("description", ""),
                        " ".join(visual.get("semantic_hints", ())),
                    ]
                )
            )
            if not visual_text:
                continue
            visual_tokens = {token for token in visual_text.split() if len(token) >= 3}
            for mention in mentions:
                mention_tokens = {
                    token for token in self._normalize(mention.get("name", "")).split()
                    if len(token) >= 3
                }
                overlap = len(visual_tokens & mention_tokens)
                if overlap == 0:
                    continue
                confidence = min(
                    0.98,
                    0.55
                    + 0.10 * overlap
                    + 0.15 * float(visual.get("confidence", 0.0) or 0.0),
                )
                visual_entity_links.append({
                    "relationship_id": f"visual-entity:{self._digest(visual['image_id'] + mention['mention_id'])}",
                    "image_id": visual["image_id"],
                    "mention_id": mention["mention_id"],
                    "relationship_type": "visual_supports_entity_identity",
                    "confidence": round(confidence, 4),
                    "evidence": ["visual_text_token_overlap"],
                })

        for field in fields:
            value_norm = self._normalize(field.get("value", ""))
            if not value_norm:
                continue
            for mention in mentions:
                name_norm = mention.get("normalized_name", "")
                if not name_norm:
                    continue
                if name_norm in value_norm or value_norm in name_norm:
                    field_entity_links.append({
                        "relationship_id": f"field-entity:{self._digest(field['field_id'] + mention['mention_id'])}",
                        "field_id": field["field_id"],
                        "mention_id": mention["mention_id"],
                        "relationship_type": "field_belongs_to_entity",
                        "confidence": round(min(field["confidence"], mention["confidence"]), 4),
                    })

        for mention in mentions:
            for field in fields:
                if field.get("semantic_key") != "tax_id":
                    continue
                ruc = self._extract_ruc(mention.get("context", ""))
                if ruc and self._normalize_numeric(field.get("value")) == self._normalize_numeric(ruc):
                    links.append({
                        "relationship_id": f"tax:{self._digest(mention['mention_id'] + field['field_id'])}",
                        "source_id": mention["mention_id"],
                        "relationship_type": "entity_has_tax_id",
                        "target_id": field["field_id"],
                        "confidence": round(min(mention["confidence"], field["confidence"]), 4),
                    })

        links.extend(visual_entity_links)
        links.extend(field_entity_links)
        return {
            "visual_entity_links": self._dedupe_dicts(
                visual_entity_links,
                ("image_id", "mention_id", "relationship_type"),
            ),
            "field_entity_links": self._dedupe_dicts(
                field_entity_links,
                ("field_id", "mention_id", "relationship_type"),
            ),
            "evidence_links": self._dedupe_dicts(
                links,
                ("relationship_id",),
            ),
            "multimodal_link_count": len(links),
        }

    @staticmethod
    def _resolve_role_conclusions(roles, conflicts=None):
        conflicts = conflicts or []
        by_role = defaultdict(list)
        for role in roles:
            by_role[str(role.get("role") or "unknown")].append(role)
        conclusions = []
        for role_name, candidates in by_role.items():
            candidates = sorted(
                candidates,
                key=lambda item: (float(item.get("confidence", 0.0)), float(item.get("score", 0.0))),
                reverse=True,
            )
            if not candidates:
                continue
            top = candidates[0]
            second = candidates[1] if len(candidates) > 1 else None
            margin = float(top.get("confidence", 0.0)) - float(second.get("confidence", 0.0)) if second else float(top.get("confidence", 0.0))
            conflict = any(
                str(conflict_item.get("name", "")).casefold() == str(top.get("name", "")).casefold()
                for conflict_item in conflicts
            )
            conclusions.append({
                "role": role_name,
                "name": top.get("name", ""),
                "identifier": top.get("identifier", ""),
                "candidate_id": top.get("candidate_id", ""),
                "confidence": round(float(top.get("confidence", 0.0)), 4),
                "decision_margin": round(margin, 4),
                "decision": (
                    "resolved"
                    if (
                        float(top.get("confidence", 0.0)) >= 0.80
                        and not conflict
                        and (
                            margin >= 0.08
                            or any("marker:señores" == item for item in top.get("evidence", ()))
                            or any("marker:proveedor" == item for item in top.get("evidence", ()))
                            or any("marker:emisor" == item for item in top.get("evidence", ()))
                            or any("marker:cuentas bancarias" == item for item in top.get("evidence", ()))
                        )
                    )
                    else "ambiguous"
                ),
                "competing_candidates": [
                    {
                        "name": item.get("name", ""),
                        "identifier": item.get("identifier", ""),
                        "confidence": item.get("confidence", 0.0),
                    }
                    for item in candidates[1:5]
                ],
            })
        return conclusions

    def _build_document_understanding(
        self,
        *,
        knowledge,
        mentions,
        fields,
        roles,
        resolved_roles,
        visuals,
        relations,
        multimodal,
        numeric,
        conflicts,
    ):
        role_map = {
            item["role"]: item
            for item in resolved_roles
            if item.get("decision") == "resolved"
        }
        return {
            "document_id": knowledge.document_id,
            "document_kind": self._infer_document_kind(knowledge, fields),
            "entities": mentions,
            "resolved_roles": role_map,
            "semantic_fields": fields,
            "visual_entities": visuals,
            "relations": relations + multimodal.get("evidence_links", []),
            "numeric_reasoning": numeric,
            "conflicts": conflicts,
            "answer_ready": bool(mentions or fields or visuals or knowledge.text.strip()),
            "reasoning_policy": "evidence_first_conservative_resolution",
        }

    def _build_typed_values(self, observations, fields):
        result = []
        for obs in observations:
            for value_type, pattern in (("money", self._MONEY), ("measurement", self._MEASUREMENT)):
                for match in pattern.finditer(obs.text):
                    raw = match.group(0).strip()
                    result.append({
                        "value_id": f"value:{value_type}:{self._digest(obs.observation_id + raw)}",
                        "value_type": value_type,
                        "raw_value": raw,
                        "normalized_value": self._normalize_numeric(raw),
                        "page_number": obs.page_number,
                        "source_id": obs.source_id,
                        "confidence": obs.confidence,
                    })
        for field in fields:
            if field["semantic_key"] not in {"price", "unit_price", "total", "subtotal", "tax", "amount", "cost", "quantity"}:
                continue
            numeric = self._normalize_numeric(field["value"])
            if numeric:
                result.append({
                    "value_id": f"field-value:{field['field_id']}",
                    "value_type": field["semantic_key"],
                    "raw_value": field["value"],
                    "normalized_value": numeric,
                    "page_number": field["page_number"],
                    "source_id": field["source_id"],
                    "confidence": field["confidence"],
                })
        return self._dedupe_dicts(result, ("value_type", "normalized_value", "page_number", "source_id"))

    def _build_numeric_reasoning(self, knowledge: DocumentKnowledge) -> dict[str, Any]:
        checks = []
        for table in knowledge.tables:
            semantic = table.get("semantic") if isinstance(table, dict) else None
            if not isinstance(semantic, dict):
                continue
            for index, row in enumerate(semantic.get("rows") or []):
                if not isinstance(row, dict):
                    continue
                q = self._decimal(row.get("quantity"))
                p = self._decimal(row.get("unit_price") or row.get("price"))
                t = self._decimal(row.get("total") or row.get("amount"))
                if q is None or p is None or t is None:
                    continue
                expected = q * p
                delta = abs(expected - t)
                tolerance = max(Decimal("0.01"), abs(t) * Decimal("0.005"))
                checks.append({
                    "table_id": semantic.get("table_id") or table.get("table_id"),
                    "row_index": index,
                    "quantity": str(q), "unit_price": str(p), "reported_total": str(t),
                    "expected_total": str(expected), "delta": str(delta),
                    "status": "consistent" if delta <= tolerance else "inconsistent",
                })
        return {"row_math_checks": checks,
                "consistent_count": sum(x["status"] == "consistent" for x in checks),
                "inconsistent_count": sum(x["status"] == "inconsistent" for x in checks)}

    def _build_conflicts(self, roles, fields):
        conflicts = []
        names = defaultdict(list)
        for role in roles:
            names[self._normalize(role["name"])].append(role)
        for name, items in names.items():
            role_set = {item["role"] for item in items}
            if len(role_set) > 1:
                conflicts.append({"type": "entity_role_competition", "name": name, "roles": sorted(role_set), "candidates": [x["candidate_id"] for x in items]})
        return conflicts

    def _build_page_summary(self, knowledge, observations):
        grouped = defaultdict(list)
        for obs in observations:
            if obs.page_number is not None:
                grouped[obs.page_number].append(obs)
        return [{
            "page_number": page,
            "observation_count": len(grouped.get(page, [])),
            "text_observation_count": sum(x.source_type in {"text", "text_line", "ocr_block"} for x in grouped.get(page, [])),
            "table_observation_count": sum(x.source_type in {"table", "semantic_table"} for x in grouped.get(page, [])),
            "image_observation_count": sum(x.source_type == "image" for x in grouped.get(page, [])),
            "has_evidence": bool(grouped.get(page)),
        } for page in range(1, knowledge.page_count + 1)]

    def _build_coverage(self, knowledge, observations, visuals):
        pages = set(range(1, knowledge.page_count + 1))
        observed = {x.page_number for x in observations if x.page_number in pages}
        image_total = len(visuals)
        image_done = sum(x["analysis_status"] == "completed" for x in visuals)
        layers = {
            "ordered_reading": bool(knowledge.reading_order),
            "native_text": bool(knowledge.text.strip()),
            "ocr": bool(knowledge.ocr_blocks),
            "images": bool(knowledge.images) or image_total == 0,
            "tables": bool(knowledge.tables) or not knowledge.tables,
            "structure": bool(knowledge.structural_objects) or not knowledge.structural_objects,
            "visual_analysis": image_total == image_done,
        }
        return {
            "status": "complete" if observed == pages and all(layers.values()) else "partial",
            "page_count": len(pages),
            "pages_with_evidence": len(observed),
            "page_coverage": round(len(observed) / len(pages), 4) if pages else 0.0,
            "image_count": image_total,
            "image_analysis_count": image_done,
            "image_analysis_coverage": round(image_done / image_total, 4) if image_total else 1.0,
            "source_layers": layers,
        }

    def _infer_document_kind(self, knowledge, fields):
        text = self._normalize(" ".join([knowledge.file_name, knowledge.text, knowledge.visual_text]))
        if any(x in text for x in ("cotizacion", "cotización", "quotation", "quote")):
            return "quotation"
        if any(x in text for x in ("factura", "invoice", "comprobante")):
            return "invoice"
        if any(x in text for x in ("contrato", "contract", "agreement")):
            return "contract"
        if any(f["semantic_key"] in {"model", "material", "serial_number"} for f in fields):
            return "technical_document"
        return "general_document"

    @staticmethod
    def _canonical_label(value: str) -> str:
        norm = UniversalDocumentSemanticReasoner._normalize(value)
        return UniversalDocumentSemanticReasoner._SEMANTIC_LABELS.get(norm, norm.replace(" ", "_")) if norm else ""

    @staticmethod
    def _clean_entity_name(value: str) -> str:
        return " ".join(str(value).strip(" :,-\t").split())

    @classmethod
    def _extract_legal_entity_name(cls, value: str) -> str:
        """Extrae la razón social sin etiquetas OCR como 'Señores' o 'Cuentas bancarias'."""
        clean = cls._clean_entity_name(value)
        match = re.search(
            r"(?i)(?:S\.?\s*A\.?\s*C?\.?|S\.?\s*R\.?\s*L\.?|"
            r"E\.?\s*I\.?\s*R\.?\s*L\.?|S\.?\s*A\.?|"
            r"LLC|INC\.?|LTD\.?|LIMITED|CORP\.?|CORPORATION|PLC|"
            r"GMBH|SAC|SRL|EIRL|LTDA\.?|LIMITADA)\s*$",
            clean,
        )
        if not match:
            return clean
        prefix = clean[:match.start()].strip(" :,-")
        legal_suffix = match.group(0).strip()
        tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&'()./-]+", prefix)
        noise = {
            "señores", "señor", "sr", "sres", "proveedor", "emisor", "empresa",
            "cuentas", "cuentas bancarias", "bancarias", "titular", "a", "nombre",
            "razon", "social", "cliente", "comprador", "cotizado", "por", "de",
            "datos", "del", "la", "los", "las",
        }
        while tokens and tokens[0].casefold() in noise:
            tokens.pop(0)
        # Si 'cuentas bancarias' quedó en medio, cortar desde ahí.
        filtered = []
        for token in tokens:
            if token.casefold() in noise and filtered:
                continue
            filtered.append(token)
        if not filtered:
            return clean
        return " ".join(filtered + [legal_suffix])

    @classmethod
    def _extract_ruc(cls, text: str) -> str:
        m = cls._RUC.search(text)
        return m.group(1) if m else ""

    @staticmethod
    def _normalize(value: Any) -> str:
        value = " ".join(str(value or "").split()).strip().casefold()
        return value.translate(str.maketrans("áéíóúüñ", "aeiouun"))

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            return round(max(0.0, min(1.0, float(value))), 4)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _as_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _digest(value: Any) -> str:
        return hashlib.sha256(str(value).encode("utf-8", "ignore")).hexdigest()[:20]

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        text = re.sub(r"[^0-9,.-]", "", str(value).replace(" ", ""))
        if not text:
            return None
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
        elif "," in text:
            parts = text.split(",")
            text = text.replace(",", ".") if len(parts[-1]) <= 2 else text.replace(",", "")
        try:
            return Decimal(text)
        except Exception:
            return None

    @classmethod
    def _normalize_numeric(cls, value: Any) -> str:
        d = cls._decimal(value)
        return format(d, "f") if d is not None else ""

    @staticmethod
    def _dedupe_dicts(records: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
        seen = set(); result = []
        for record in records:
            key = tuple(str(record.get(k, "")) for k in keys)
            if key in seen:
                continue
            seen.add(key); result.append(record)
        return result


__all__ = ["UniversalDocumentSemanticReasoner", "UniversalSemanticObservation"]
