"""Léxico semántico local y extensible para comprensión documental universal.

No intenta ser un diccionario general del idioma. Su función es transformar
etiquetas y términos observados en el documento en conceptos documentales
normalizados, conservando siempre el término fuente y una puntuación de
semejanza. No utiliza modelos remotos.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable


@dataclass(frozen=True)
class SemanticLexicalMatch:
    raw_term: str
    semantic_key: str
    category: str
    confidence: float
    matched_alias: str


class DocumentSemanticLexicon:
    VERSION = "1.0"

    # Alias transversales: no dependen de un dominio concreto.
    ALIASES: dict[str, tuple[str, ...]] = {
        "provider": ("proveedor", "proveedora", "supplier", "vendor", "seller", "emisor", "issuer", "vendedor", "cotizado por", "cotiza por", "titular"),
        "customer": ("cliente", "comprador", "buyer", "customer", "destinatario", "recipient", "cotizado a", "facturar a", "señores", "señor"),
        "manufacturer": ("fabricante", "manufacturer", "maker"),
        "representative": ("representante", "asesor", "ejecutivo comercial", "sales representative"),
        "beneficiary": ("beneficiario", "beneficiary", "beneficiary name"),
        "bank": ("banco", "bank", "cuenta bancaria", "bank account", "cci", "iban", "swift"),
        "product": ("producto", "productos", "product", "item", "articulo", "artículo", "bien", "material"),
        "service": ("servicio", "servicios", "service", "services"),
        "description": ("descripcion", "descripción", "detalle", "concepto", "concept", "description", "details", "products", "producto", "productos"),
        "code": ("codigo", "código", "code", "item code", "part number", "part no", "numero de parte", "número de parte"),
        "sku": ("sku", "stock keeping unit"),
        "brand": ("marca", "brand"),
        "model": ("modelo", "model"),
        "serial_number": ("serie", "serial", "serial number", "numero de serie", "número de serie"),
        "quantity": ("cantidad", "cant", "qty", "quantidade", "quantity", "volumen", "volume"),
        "unit": ("unidad", "und", "unid", "u.m.", "um", "u medida", "medida", "unit", "unidade", "measure", "presentation", "presentación", "presentacao"),
        "price": ("precio", "price", "preço", "valor", "value", "tarifa", "rate", "precio de lista", "list price"),
        "unit_price": ("precio unitario", "p/unit", "p/unit.", "p. unit", "unit price", "unit value", "preço unitário"),
        "amount": ("importe", "monto", "amount", "valor", "net amount", "importe neto"),
        "total": ("total", "grand total", "total general", "importe total", "monto total"),
        "subtotal": ("subtotal", "sub total", "subtotal neto", "base imponible", "taxable base"),
        "tax": ("igv", "iva", "tax", "impuesto", "vat", "sales tax"),
        "discount": ("descuento", "descto", "dscto", "discount", "bonificacion", "bonificación", "rebate"),
        "currency": ("moneda", "currency", "moeda", "divisa"),
        "cost": ("costo", "coste", "cost", "custo", "coste unitario"),
        "payment_method": ("forma de pago", "medio de pago", "payment method", "forma de pagamento"),
        "payment_terms": ("condiciones de pago", "plazo de pago", "payment terms", "terms of payment", "condiciones comerciales"),
        "delivery_time": ("tiempo de entrega", "plazo de entrega", "entrega", "delivery time", "lead time", "delivery"),
        "delivery_location": ("lugar de entrega", "direccion de entrega", "dirección de entrega", "delivery location", "ship to", "deliver to"),
        "warranty": ("garantia", "garantía", "warranty", "garantia del producto", "product warranty"),
        "validity": ("validez", "vigencia", "validity", "quotation validity", "offer validity"),
        "legal_name": ("razon social", "razón social", "legal name", "company name", "nombre legal"),
        "tax_id": ("ruc", "vat", "tin", "tax id", "tax number", "nit", "rif", "cuit", "rfc"),
        "email": ("correo", "email", "e-mail", "correo electronico", "correo electrónico"),
        "phone": ("telefono", "teléfono", "phone", "telephone", "mobile", "celular"),
        "address": ("direccion", "dirección", "address", "domicilio"),
        "date": ("fecha", "date", "data"),
        "reference": ("referencia", "reference", "ref", "project", "proyecto", "obra"),
        "bank_account": ("cuenta", "account", "cuenta corriente", "cta cte", "current account"),
        "technical_specification": ("especificacion", "especificación", "specification", "spec", "caracteristica", "característica", "technical data", "ficha tecnica", "ficha técnica"),
        "certificate": ("certificado", "certificate", "certification", "certificación", "constancia"),
        "document_number": ("numero", "número", "nro", "no.", "number", "document number", "quotation number", "invoice number"),
    }

    _TOKEN_NOISE = {
        "de", "del", "la", "el", "los", "las", "the", "of", "and", "y", "a", "to", "por", "for",
    }

    @classmethod
    def normalize(cls, value: str) -> str:
        value = unicodedata.normalize("NFKD", str(value or ""))
        value = "".join(c for c in value if not unicodedata.combining(c))
        value = re.sub(r"[^a-zA-Z0-9%./_-]+", " ", value).strip().casefold()
        return re.sub(r"\s+", " ", value)

    @classmethod
    def tokens(cls, value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9%]+", cls.normalize(value))
            if token not in cls._TOKEN_NOISE and len(token) >= 2
        }

    @classmethod
    def match(cls, term: str, *, threshold: float = 0.72) -> SemanticLexicalMatch | None:
        normalized = cls.normalize(term)
        if not normalized:
            return None

        # Primero exactitud sobre la cadena completa. Esto evita que un alias
        # compuesto como ``P/Unit.`` caiga por tokenización en ``unit``.
        for semantic_key, aliases in cls.ALIASES.items():
            for alias in aliases:
                if normalized == cls.normalize(alias):
                    return SemanticLexicalMatch(
                        raw_term=term,
                        semantic_key=semantic_key,
                        category=semantic_key,
                        confidence=1.0,
                        matched_alias=alias,
                    )

        best: SemanticLexicalMatch | None = None
        term_tokens = cls.tokens(normalized)
        for semantic_key, aliases in cls.ALIASES.items():
            for alias in aliases:
                alias_norm = cls.normalize(alias)
                if not alias_norm:
                    continue
                if normalized == alias_norm:
                    confidence = 1.0
                else:
                    alias_tokens = cls.tokens(alias_norm)
                    jaccard = (
                        len(term_tokens & alias_tokens) / len(term_tokens | alias_tokens)
                        if term_tokens | alias_tokens
                        else 0.0
                    )
                    similarity = SequenceMatcher(None, normalized, alias_norm).ratio()
                    confidence = max(jaccard, similarity * 0.92)
                if confidence < threshold:
                    continue
                candidate = SemanticLexicalMatch(
                    raw_term=term,
                    semantic_key=semantic_key,
                    category=semantic_key,
                    confidence=round(min(0.999, confidence), 4),
                    matched_alias=alias,
                )
                if best is None or candidate.confidence > best.confidence:
                    best = candidate
        return best

    @classmethod
    def explain(cls, terms: Iterable[str]) -> list[dict[str, object]]:
        result = []
        for term in terms:
            match = cls.match(term)
            if match:
                result.append({
                    "raw_term": match.raw_term,
                    "semantic_key": match.semantic_key,
                    "meaning_category": match.category,
                    "confidence": match.confidence,
                    "matched_alias": match.matched_alias,
                })
            else:
                result.append({
                    "raw_term": str(term),
                    "semantic_key": "unknown",
                    "meaning_category": "unknown_document_term",
                    "confidence": 0.0,
                    "matched_alias": "",
                })
        return result


__all__ = ["DocumentSemanticLexicon", "SemanticLexicalMatch"]
