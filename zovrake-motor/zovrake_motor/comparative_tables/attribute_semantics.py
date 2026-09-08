"""Normalización semántica conservadora de atributos comparables."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AttributeSemantic:
    """Identidad semántica de un atributo sin perder su etiqueta original."""

    semantic_key: str
    display_name: str
    matched_alias: bool


_ALIAS_GROUPS: dict[str, tuple[str, ...]] = {
    "DESCRIPTION": (
        "description",
        "descripcion",
        "descripción",
        "producto",
        "item",
        "detalle",
        "productos",
        "producto(s)",
    ),
    "QUANTITY": (
        "quantity",
        "cantidad",
        "cant",
        "cant.",
        "qty",
    ),
    "UNIT": (
        "unit",
        "unidad",
        "unid",
        "unid.",
        "und",
        "und.",
        "u.m.",
        "u medida",
        "u. medida",
        "u.medida",
        "unidad de medida",
        "um",
        "um.",
        "medida",
        "medida.",
    ),
    "UNIT_PRICE": (
        "unit price",
        "precio unitario",
        "precio unit",
        "precio u",
        "precio u.",
        "p unit",
        "p. unit",
        "p. unit.",
        "p/u",
        "p/u.",
        "p u",
        "p. u.",
        "p.u.",
        "pu",
        "p/unit",
        "p/unit.",
        "s/p.u.",
        "s/p.u",
    ),
    "LINE_TOTAL": (
        "line total",
        "total línea",
        "total linea",
        "importe",
        "importe total",
        "precio total",
        "total por línea",
        "total por linea",
        "s/.total",
        "s/. total",
    ),
    "CODE": (
        "code",
        "codigo",
        "código",
        "cod",
        "cod.",
        "sku",
        "part number",
        "nro item",
    ),
    "BRAND": (
        "brand",
        "marca",
    ),
    "CURRENCY": (
        "currency",
        "moneda",
    ),
    "PAYMENT_TERMS": (
        "payment terms",
        "forma de pago",
        "condiciones de pago",
        "condiciones comerciales",
        "pago",
        "condiciones",
    ),
    "DOCUMENT_TOTAL": (
        "document total",
        "total a pagar",
        "total pagar",
        "total cotización",
        "total cotizacion",
        "total general",
        "grand total",
    ),
    "DOCUMENT": (
        "document",
        "documento",
        "file name",
        "archivo",
    ),
    "PROVIDER": (
        "provider",
        "proveedor",
        "provider name",
        "nombre del proveedor",
        "razon social",
        "razón social",
    ),
}

_DISPLAY_NAMES = {
    "DESCRIPTION": "Descripción",
    "QUANTITY": "Cantidad",
    "UNIT": "Unidad",
    "UNIT_PRICE": "Precio Unitario",
    "LINE_TOTAL": "Total",
    "CODE": "Código",
    "BRAND": "Marca",
    "CURRENCY": "Moneda",
    "PAYMENT_TERMS": "Condiciones de Pago",
    "DOCUMENT_TOTAL": "Total del Documento",
    "DOCUMENT": "Documento",
    "PROVIDER": "Proveedor",
}


def normalize_attribute_text(value: Any) -> str:
    """Normaliza texto para comparar etiquetas sin borrar su significado."""
    text = str(value or "").strip().casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("/", " / ")
    text = re.sub(r"[^a-z0-9.]+", " ", text)
    return " ".join(text.split())


def _compact_normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text)


_ALIAS_INDEX: dict[str, str] = {}
for _semantic_key, _aliases in _ALIAS_GROUPS.items():
    for _alias in _aliases:
        _normalized = normalize_attribute_text(_alias)
        if _normalized:
            _ALIAS_INDEX[_normalized] = _semantic_key
            _ALIAS_INDEX.setdefault(_compact_normalized(_normalized), _semantic_key)


def canonicalize_attribute_name(
    name: Any,
    *,
    scope: str = "unknown",
) -> AttributeSemantic:
    """
    Resuelve una etiqueta a una identidad semántica conocida.

    ``scope='item'`` interpreta ``TOTAL`` como total de línea porque el valor
    procede de un ítem comercial. Fuera de ese alcance, ``TOTAL`` se conserva
    como total documental solo cuando la etiqueta expresa explícitamente ese
    significado; de lo contrario queda como atributo libre.
    """
    raw = str(name or "").strip()
    normalized = normalize_attribute_text(raw)
    compact = _compact_normalized(normalized)

    if scope == "item" and normalized in {"total", "total s", "s total"}:
        return AttributeSemantic("LINE_TOTAL", _DISPLAY_NAMES["LINE_TOTAL"], True)

    semantic_key = _ALIAS_INDEX.get(normalized) or _ALIAS_INDEX.get(compact)
    if semantic_key is None:
        return AttributeSemantic(
            semantic_key=f"ATTRIBUTE:{compact or 'UNNAMED'}",
            display_name=raw,
            matched_alias=False,
        )

    return AttributeSemantic(
        semantic_key=semantic_key,
        display_name=_DISPLAY_NAMES.get(semantic_key, raw),
        matched_alias=True,
    )
