"""Interpretación semántica universal de DocumentKnowledge, local y trazable."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import re
from typing import Any, Iterable

from zovrake_motor.comprehension.models import DocumentKnowledge


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

    MODEL_VERSION = "1.0-universal-evidence-graph"

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
        mentions = self._build_entity_mentions(observations)
        roles = self._build_role_candidates(observations, knowledge.entities, mentions)
        visuals = self._build_visuals(knowledge)
        relations = self._build_relations(observations, mentions, roles)
        typed = self._build_typed_values(observations, fields)
        numeric = self._build_numeric_reasoning(knowledge)
        conflicts = self._build_conflicts(roles, fields)
        coverage = self._build_coverage(knowledge, observations, visuals)
        page_summary = self._build_page_summary(knowledge, observations)

        return {
            "model_version": self.MODEL_VERSION,
            "schema_version": "universal-semantic-understanding-v1",
            "stage": "evidence_graph_reasoning",
            "document_id": knowledge.document_id,
            "document_kind": self._infer_document_kind(knowledge, fields),
            "observations": [item.to_dict() for item in observations],
            "semantic_fields": fields,
            "entity_mentions": mentions,
            "role_candidates": roles,
            "visual_understanding": visuals,
            "relations": relations,
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
                "visual": visuals,
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
                "confidence": obs.confidence,
            })
        return self._dedupe_dicts(result, ("semantic_key", "raw_label", "value", "page_number", "source_id"))

    def _build_entity_mentions(self, observations: list[UniversalSemanticObservation]) -> list[dict[str, Any]]:
        result = []
        for obs in observations:
            for match in self._LEGAL_ENTITY.finditer(obs.text):
                name = self._clean_entity_name(match.group(1))
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
                    state["score"] += min(58.0, 18.0 + 8.0 * len(hits))
                    state["evidence"].extend(f"marker:{item}" for item in hits)
                    state["source_ids"].append(mention["source_id"])
        for entity in entities:
            role = str(getattr(entity, "role", "") or "").strip().lower()
            name = str(getattr(entity, "name", "") or "").strip()
            if not role or not name:
                continue
            state = get(role, name, str(getattr(entity, "identifier", "") or ""))
            state["score"] += 60.0 * self._confidence(getattr(entity, "confidence", 0.0))
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
