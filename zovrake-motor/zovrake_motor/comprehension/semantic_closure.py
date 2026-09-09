from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import unicodedata
from typing import Any, Iterable

from zovrake_motor.comprehension.document_semantic_lexicon import DocumentSemanticLexicon


@dataclass(frozen=True)
class SemanticTerm:
    term: str
    normalized: str
    semantic_key: str
    meaning: str
    confidence: float
    source: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "term": self.term,
            "normalized": self.normalized,
            "semantic_key": self.semantic_key,
            "meaning": self.meaning,
            "confidence": self.confidence,
            "source": self.source,
            "evidence": list(self.evidence),
        }


class UniversalSemanticClosure:
    """Capa semántica local que diferencia significado conocido de desconocido."""

    VERSION = "1.1"

    MEANINGS = {
        "provider": "entidad que emite, ofrece o suministra el bien o servicio",
        "customer": "entidad que recibe, compra, solicita o contrata",
        "manufacturer": "entidad que fabrica el bien",
        "product": "bien o artículo ofrecido o descrito",
        "service": "prestación o actividad ofrecida",
        "description": "texto que describe o identifica un bien, servicio o concepto",
        "code": "identificador de un elemento",
        "quantity": "magnitud numérica de unidades, volumen o cantidad",
        "unit": "unidad o presentación de una cantidad",
        "price": "valor económico asociado a un bien, servicio o tarifa",
        "unit_price": "valor económico por unidad",
        "amount": "importe monetario asociado a un concepto",
        "total": "importe final o agregado declarado",
        "subtotal": "importe parcial antes de impuestos u otros ajustes",
        "tax": "tributo aplicado a una operación",
        "discount": "reducción aplicada a un precio o importe",
        "currency": "moneda en la que se expresa un importe",
        "cost": "costo económico asociado a adquisición, producción o prestación",
        "payment_method": "medio utilizado para realizar un pago",
        "payment_terms": "condiciones, plazos o reglas de pago",
        "delivery_time": "plazo o tiempo requerido para entregar",
        "delivery_location": "lugar de entrega o recepción",
        "warranty": "compromiso de garantía",
        "validity": "periodo durante el cual una oferta permanece vigente",
        "legal_name": "razón o denominación legal",
        "tax_id": "identificador fiscal",
        "email": "dirección electrónica",
        "phone": "número telefónico",
        "address": "dirección física o postal",
        "date": "fecha documentada",
        "reference": "referencia contextual del documento, proyecto u obra",
        "bank_account": "cuenta utilizada para operaciones bancarias",
        "technical_specification": "característica o especificación técnica",
        "certificate": "evidencia que acredita una condición o cumplimiento",
        "document_number": "identificador del documento",
    }

    _DIRECT = {
        "nombre": "name", "titular": "owner", "cuenta": "bank_account", "banco": "bank",
        "marca": "brand", "modelo": "model", "serie": "serial_number", "medida": "unit",
        "presentacion": "unit", "cantidad": "quantity", "valor": "amount", "importe": "amount",
        "monto": "amount", "precio": "price", "producto": "product", "productos": "product",
        "servicio": "service", "servicios": "service", "fecha": "date", "direccion": "address",
        "telefono": "phone", "correo": "email", "garantia": "warranty", "garantía": "warranty",
        "vigencia": "validity", "validez": "validity",
    }

    @staticmethod
    def normalize(value: str) -> str:
        value = unicodedata.normalize("NFKD", str(value or ""))
        value = "".join(c for c in value if not unicodedata.combining(c))
        value = re.sub(r"[^a-zA-Z0-9%./_-]+", " ", value).strip().casefold()
        return re.sub(r"\s+", " ", value)

    @classmethod
    def resolve_term(cls, term: str, *, context: str = "") -> SemanticTerm:
        match = DocumentSemanticLexicon.match(term, threshold=0.72)
        if match:
            return SemanticTerm(
                term=term,
                normalized=cls.normalize(term),
                semantic_key=match.semantic_key,
                meaning=cls.MEANINGS.get(match.semantic_key, "concepto documental normalizado"),
                confidence=match.confidence,
                source="document_semantic_lexicon",
                evidence=(f"alias:{match.matched_alias}",),
            )

        normalized = cls.normalize(term)
        direct = cls._DIRECT.get(normalized)
        if direct:
            return SemanticTerm(
                term=term,
                normalized=normalized,
                semantic_key=direct,
                meaning=cls.MEANINGS.get(direct, "concepto documental"),
                confidence=0.88,
                source="contextual_document_noun",
                evidence=("generic_document_noun",),
            )

        candidates: list[tuple[str, float]] = []
        for key, aliases in DocumentSemanticLexicon.ALIASES.items():
            for alias in aliases:
                similarity = SequenceMatcher(None, normalized, cls.normalize(alias)).ratio()
                if similarity >= 0.62:
                    candidates.append((key, similarity))
        if candidates:
            key, similarity = max(candidates, key=lambda item: item[1])
            if similarity >= 0.78:
                return SemanticTerm(
                    term=term,
                    normalized=normalized,
                    semantic_key=key,
                    meaning=cls.MEANINGS.get(key, "concepto documental"),
                    confidence=round(similarity * 0.90, 4),
                    source="contextual_fuzzy_lexicon",
                    evidence=(f"closest:{key}", f"similarity:{similarity:.3f}"),
                )

        if re.fullmatch(r"[A-Z0-9][A-Z0-9._/-]{2,30}", term.strip()):
            return SemanticTerm(
                term=term,
                normalized=normalized,
                semantic_key="identifier_like",
                meaning="token con forma de identificador",
                confidence=0.62,
                source="shape_inference",
                evidence=("alphanumeric_identifier_shape",),
            )

        return SemanticTerm(
            term=term,
            normalized=normalized,
            semantic_key="unknown",
            meaning="término presente cuyo significado no puede determinarse con seguridad mediante la ontología local",
            confidence=0.0,
            source="unresolved_semantic_term",
            evidence=("term_not_in_local_semantic_registry", "context_available" if context else "no_context"),
        )

    @classmethod
    def build_dictionary(cls, observations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: dict[tuple[str, str], dict[str, Any]] = {}
        pattern = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9./_-]{1,50}")
        for observation in observations:
            text = str(observation.get("text") or "")
            if not text:
                continue
            for raw_term in pattern.findall(text):
                resolved = cls.resolve_term(raw_term, context=text)
                record = resolved.to_dict()
                record["source_id"] = observation.get("source_id")
                record["page_number"] = observation.get("page_number")
                key = (record["normalized"], record["semantic_key"])
                previous = unique.get(key)
                if previous is None or record["confidence"] > previous["confidence"]:
                    unique[key] = record
        return sorted(unique.values(), key=lambda item: (-float(item["confidence"]), item["normalized"]))
