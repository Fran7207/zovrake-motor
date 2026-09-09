"""Compositor semántico del layout del Cuadro Comparativo.

No genera HTML ni usa una plantilla visual fija. Produce un plan de composición
que indica qué información debe ocupar las zonas primaria, secundaria y
terciaria del cuadro, además de la matriz, resúmenes y criterios encontrados.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable
import re
import unicodedata


_PAYMENT_KEYS = {
    "payment_method", "payment_terms", "forma_de_pago", "forma pago",
    "medio_de_pago", "condiciones_de_pago", "condiciones comerciales", "pago",
}

_PRIMARY_ORDER = (
    "comparison_identity",
    "buyer_identity",
    "purpose_or_reference",
)
_SECONDARY_ORDER = (
    "provider_identity",
    "commercial_terms",
    "technical_context",
    "logistics_terms",
)
_TERTIARY_ORDER = (
    "supporting_information",
    "evidence_and_traceability",
)


def _normalize(value: Any) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9%]+", " ", value).strip().casefold()
    return re.sub(r"\s+", " ", value)


def _key(value: Any) -> str:
    return _normalize(value).replace(" ", "_")


def _is_payment_key(value: Any) -> bool:
    normalized = _normalize(value)
    compact = _key(value)
    return normalized in {"forma de pago", "medio de pago", "condiciones de pago", "condiciones comerciales", "pago"} or compact in _PAYMENT_KEYS


def _provider_name(provider: dict[str, Any]) -> str:
    for key in ("provider_name", "provider_display_name", "name", "legal_name"):
        value = str(provider.get(key, "")).strip()
        if value:
            return value
    org = provider.get("organization", {})
    if isinstance(org, dict):
        for key in ("name", "legal_name", "display_name"):
            value = str(org.get(key, "")).strip()
            if value:
                return value
    return str(provider.get("provider_id", "")).strip()


def _flatten_provider_fields(provider: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for container_key in ("commercial_information", "technical_information", "fields"):
        container = provider.get(container_key, {})
        if isinstance(container, dict):
            raw = container.get("fields", container)
            if isinstance(raw, dict):
                for key, value in raw.items():
                    if value not in (None, "", [], (), {}):
                        fields[str(key)] = value
    return fields


def _build_field_descriptor(section_id: str, label: str, value: Any, *, provider_id: str = "") -> dict[str, Any]:
    return {
        "field_id": f"field:{_key(section_id)}:{_key(label)}:{_key(provider_id)}",
        "semantic_key": _key(label),
        "display_name": str(label),
        "value": value,
        "provider_id": provider_id,
        "source": "comparative_knowledge",
        "required": False,
        "section_id": section_id,
    }


def compose_comparative_layout(
    *,
    enriched_context: dict[str, Any],
    structure: dict[str, Any],
    columns: Iterable[dict[str, Any]],
    rows: Iterable[dict[str, Any]],
    providers: Iterable[dict[str, Any]],
    document_ids: Iterable[str],
) -> dict[str, Any]:
    """Construye un plan de presentación adaptado a la evidencia disponible."""
    providers = [dict(item) for item in providers if isinstance(item, dict)]
    columns = [dict(item) for item in columns if isinstance(item, dict)]
    rows = [dict(item) for item in rows if isinstance(item, dict)]
    enriched_context = dict(enriched_context or {})
    structure = dict(structure or {})

    sections: list[dict[str, Any]] = []
    seen_section: set[str] = set()

    def add_section(section_id: str, title: str, hierarchy: str, *, priority: int, fields: list[dict[str, Any]] | None = None, visible_if_nonempty: bool = True) -> None:
        if section_id in seen_section:
            return
        fields = fields or []
        if visible_if_nonempty and not fields:
            return
        sections.append({
            "section_id": section_id,
            "title": title,
            "hierarchy": hierarchy,
            "priority": priority,
            "fields": fields,
            "layout_role": "data_section",
        })
        seen_section.add(section_id)

    # Contexto principal: sólo lo que existe realmente.
    primary_fields: list[dict[str, Any]] = []
    for key, value in enriched_context.items():
        if value not in (None, "", [], (), {}) and key not in {"confidence_level_available"}:
            primary_fields.append(_build_field_descriptor("comparison_identity", str(key), value))
    for key, value in structure.items():
        if value not in (None, "", [], (), {}) and key in {"group_type", "table_role", "primary_item"}:
            primary_fields.append(_build_field_descriptor("comparison_identity", key, value))
    add_section("comparison_identity", "Identificación del análisis", "primary", priority=10, fields=primary_fields)

    # Proveedores: identidad + campos comerciales/administrativos. Se preservan
    # proveedores aunque tengan atributos distintos.
    provider_fields: list[dict[str, Any]] = []
    payment_fields: list[dict[str, Any]] = []
    provider_field_keys: set[str] = set()
    payment_by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for provider in providers:
        provider_id = str(provider.get("provider_id") or provider.get("organization_id") or "").strip()
        name = _provider_name(provider)
        if name:
            provider_fields.append(_build_field_descriptor("provider_identity", "Proveedor", name, provider_id=provider_id))
        trace = provider.get("traceability", {})
        if isinstance(trace, dict):
            for key in ("source_document_reference", "document_id"):
                value = trace.get(key)
                if value:
                    provider_fields.append(_build_field_descriptor("provider_identity", key, value, provider_id=provider_id))
        for key, value in _flatten_provider_fields(provider).items():
            if value in (None, "", [], (), {}):
                continue
            if _is_payment_key(key):
                item = _build_field_descriptor("commercial_terms", key, value, provider_id=provider_id)
                payment_fields.append(item)
                payment_by_provider[provider_id or name].append(item)
            normalized = _key(key)
            if normalized not in provider_field_keys:
                provider_field_keys.add(normalized)
                provider_fields.append(_build_field_descriptor("commercial_terms", key, value, provider_id=provider_id))

    provider_sections: list[dict[str, Any]] = []
    for provider in providers:
        provider_id = str(provider.get("provider_id") or provider.get("organization_id") or "").strip()
        name = _provider_name(provider)
        provider_specific_fields = [
            field for field in provider_fields
            if str(field.get("provider_id", "")) == provider_id
        ]
        provider_payment = payment_by_provider.get(provider_id or name, [])
        provider_sections.append({
            "provider_id": provider_id,
            "display_name": name,
            "hierarchy": "secondary",
            "identity_fields": [
                field for field in provider_specific_fields
                if field.get("section_id") != ""
            ],
            "commercial_fields": provider_specific_fields,
            "payment_fields": provider_payment,
            "has_payment_evidence": bool(provider_payment),
        })

    # Garantía de composición: si existe método/condición de pago, debe formar
    # parte de la salida visible del modelo, incluso aunque sea el único campo
    # comercial detectado.
    add_section("provider_identity", "Proveedores", "secondary", priority=20, fields=provider_fields)
    add_section("payment_terms", "Método y condiciones de pago", "secondary", priority=21, fields=payment_fields)

    # Contexto comercial/técnico/logístico dinámico.
    commercial = structure.get("commercial_information", structure.get("available_attributes", {}))
    if isinstance(commercial, dict):
        commercial_fields = commercial.get("fields", commercial.get("commercial", commercial))
    else:
        commercial_fields = {}
    if isinstance(commercial_fields, dict):
        fields = [
            _build_field_descriptor("commercial_terms", str(k), v)
            for k, v in commercial_fields.items()
            if v not in (None, "", [], (), {}) and not _is_payment_key(k)
        ]
        add_section("commercial_terms", "Condiciones comerciales", "secondary", priority=22, fields=fields)

    technical = structure.get("technical_information", structure.get("available_attributes", {}).get("technical", {}))
    if isinstance(technical, dict):
        add_section(
            "technical_context",
            "Información técnica",
            "secondary",
            priority=23,
            fields=[_build_field_descriptor("technical_context", str(k), v) for k, v in technical.items() if v not in (None, "", [], (), {})],
        )

    # Matriz: jamás impone columnas fijas; describe las detectadas.
    matrix_columns = []
    for column in sorted(columns, key=lambda c: (int(c.get("logical_position", 0)), str(c.get("column_id", "")))):
        matrix_columns.append({
            "column_id": str(column.get("column_id", "")),
            "attribute_name": str(column.get("attribute_name", "")),
            "display_name": str(column.get("metadata", {}).get("display_name", column.get("attribute_name", ""))) if isinstance(column.get("metadata", {}), dict) else str(column.get("attribute_name", "")),
            "logical_position": column.get("logical_position"),
            "data_type": str(column.get("data_type", "")),
            "traceability": dict(column.get("traceability", {})) if isinstance(column.get("traceability", {}), dict) else {},
        })

    matrix_rows = []
    for row in sorted(rows, key=lambda r: (int(r.get("logical_position", 0)), str(r.get("row_id", "")))):
        provider_id = str(row.get("provider_id", ""))
        matrix_rows.append({
            "row_id": str(row.get("row_id", "")),
            "provider_id": provider_id,
            "logical_position": row.get("logical_position"),
            "column_references": list(row.get("column_references", [])),
            "source_table_id": str(row.get("table_id", "")),
            "traceability": dict(row.get("traceability", {})) if isinstance(row.get("traceability", {}), dict) else {},
        })

    # Jerarquía de atributos observados; no se inventan etiquetas.
    dynamic_attribute_ids = [str(c.get("column_id", "")) for c in matrix_columns if c.get("column_id")]
    matrix = {
        "matrix_type": "dynamic_provider_item_matrix",
        "orientation": "items_by_provider" if providers else "rows_by_source",
        "columns": matrix_columns,
        "rows": matrix_rows,
        "providers": [
            {"provider_id": str(p.get("provider_id", "")), "display_name": _provider_name(p)}
            for p in providers
        ],
        "dynamic_attribute_ids": dynamic_attribute_ids,
        "comparison_basis": "document_evidence",
        "fixed_schema": False,
    }

    # Resumen inferior: crea bloques sólo si hay evidencia.
    summary_fields: list[dict[str, Any]] = []
    for key, value in commercial_fields.items() if isinstance(commercial_fields, dict) else ():
        normalized = _key(key)
        if normalized in {"subtotal", "igv", "iva", "tax", "total", "document_total", "total_a_pagar", "monto_total", "importe_total"}:
            summary_fields.append(_build_field_descriptor("financial_summary", key, value))
    add_section("financial_summary", "Resumen económico", "secondary", priority=30, fields=summary_fields)

    # Logística / condiciones detectadas entre campos de proveedor.
    logistical_fields: list[dict[str, Any]] = []
    for provider in providers:
        provider_id = str(provider.get("provider_id") or "")
        for key, value in _flatten_provider_fields(provider).items():
            norm = _normalize(key)
            if any(token in norm for token in ("entrega", "plazo", "stock", "disponibilidad", "flete", "transporte")):
                logistical_fields.append(_build_field_descriptor("logistics_terms", key, value, provider_id=provider_id))
    add_section("logistics_terms", "Condiciones logísticas", "secondary", priority=24, fields=logistical_fields)

    # Criterios explícitos provenientes del proceso/contexto.
    criteria = structure.get("evaluation_criteria", enriched_context.get("evaluation_criteria", []))
    if isinstance(criteria, (list, tuple)):
        criteria_items = [dict(c) if isinstance(c, dict) else {"name": str(c)} for c in criteria]
    else:
        criteria_items = []
    criteria_items = [item for item in criteria_items if item]
    if criteria_items:
        add_section(
            "evaluation_criteria",
            "Criterios de evaluación",
            "secondary",
            priority=31,
            fields=[_build_field_descriptor("evaluation_criteria", str(item.get("name") or item.get("criterion") or "Criterio"), item) for item in criteria_items],
        )

    # Información terciaria y trazabilidad: siempre útil para auditoría, pero no
    # compite visualmente con las decisiones principales.
    trace_fields = []
    for doc_id in document_ids:
        if str(doc_id).strip():
            trace_fields.append(_build_field_descriptor("evidence_and_traceability", "Documento origen", str(doc_id)))
    add_section("evidence_and_traceability", "Evidencia y trazabilidad", "tertiary", priority=90, fields=trace_fields)

    sections.sort(key=lambda item: (item["priority"], item["section_id"]))
    primary = [item["section_id"] for item in sections if item["hierarchy"] == "primary"]
    secondary = [item["section_id"] for item in sections if item["hierarchy"] == "secondary"]
    tertiary = [item["section_id"] for item in sections if item["hierarchy"] == "tertiary"]

    return {
        "layout_version": "1.0-dynamic-semantic-composition",
        "template_fixed": False,
        "composition_basis": "available_evidence_and_comparative_relevance",
        "hierarchy": {
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
        },
        "sections": sections,
        "provider_sections": provider_sections,
        "matrix": matrix,
        "decision_area": {
            "section_id": "decision_area",
            "title": "Resultado del análisis",
            "hierarchy": "post_reasoning",
            "owner": "MP7",
            "render_when_available": True,
            "source": "pm7_reasoning_output",
            "fixed_content": False,
        },
        "mandatory_present_when_available": {
            "payment_method_or_terms": bool(payment_fields),
        },
        "rendering_instructions": {
            "keep_source_values": True,
            "do_not_invent_missing_fields": True,
            "preserve_provider_boundaries": True,
            "preserve_item_boundaries": True,
            "show_payment_per_provider": bool(payment_fields),
            "show_only_sections_with_evidence": True,
        },
    }
