"""Política de prompt y esquema estructurado de ZOVRAKE."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_INSTRUCTIONS = """
Eres la capa de comprensión semántica multimodal dentro del motor ZOVRAKE.

Tu función NO es decidir un ganador, NO es construir la tabla comparativa final y
NO es reemplazar la lógica de negocio de ZOVRAKE. Tu función es interpretar
evidencia documental difícil y devolver conocimiento estructurado para que ZOVRAKE
lo valide y lo fusione con su comprensión local.

Reglas obligatorias:
1. Analiza cualquier tipo de documento sin asumir una plantilla fija.
2. Usa solamente la evidencia suministrada.
3. Nunca inventes nombres, precios, cantidades, fechas, códigos, entidades,
   métodos de pago, condiciones, productos, servicios o relaciones.
4. Conserva la redacción fuente cuando la normalización pueda perder significado.
5. Distingue claramente entre texto visible, interpretación semántica y dato
   normalizado.
6. No determines que una empresa es proveedor solo porque aparece en un bloque
   bancario, firma o cuenta de depósito.
7. No conviertas un número cercano a una etiqueta en método de pago sin evidencia.
8. Resuelve referencias considerando todo el documento y sus relaciones espaciales.
9. Cuando exista conflicto o evidencia insuficiente, registra una incertidumbre.
10. Cada dato importante debe indicar sus evidence_refs.
11. Para imágenes, separa texto detectado de interpretación visual.
12. Las cantidades, precios y totales no deben promoverse a hechos confiables
    cuando la evidencia sea dudosa.
13. Devuelve únicamente el objeto JSON del esquema indicado.
""".strip()


SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "document_type": {"type": "string"},
        "summary": {"type": "string"},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "entity_type": {"type": "string"},
                    "identifier": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "name", "role", "entity_type", "identifier",
                    "confidence", "evidence_refs"
                ],
            },
        },
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "subject": {"type": "string"},
                    "attribute": {"type": "string"},
                    "value": {"type": "string"},
                    "normalized_value": {"type": "string"},
                    "value_type": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "subject", "attribute", "value", "normalized_value",
                    "value_type", "confidence", "evidence_refs"
                ],
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "source": {"type": "string"},
                    "relationship": {"type": "string"},
                    "target": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "source", "relationship", "target",
                    "confidence", "evidence_refs"
                ],
            },
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                },
                "required": ["name", "role", "evidence_refs", "confidence"],
            },
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "description": {"type": "string"},
                    "code": {"type": "string"},
                    "quantity": {"type": "string"},
                    "unit": {"type": "string"},
                    "unit_price": {"type": "string"},
                    "total": {"type": "string"},
                    "currency": {"type": "string"},
                    "attributes": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "description", "code", "quantity", "unit", "unit_price",
                    "total", "currency", "attributes", "confidence",
                    "evidence_refs"
                ],
            },
        },
        "visual_observations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "image_ref": {"type": "string"},
                    "image_type": {"type": "string"},
                    "description": {"type": "string"},
                    "detected_text": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "image_ref", "image_type", "description",
                    "detected_text", "confidence", "evidence_refs"
                ],
            },
        },
        "numeric_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "expression": {"type": "string"},
                    "declared_value": {"type": "string"},
                    "calculated_value": {"type": "string"},
                    "status": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "expression", "declared_value", "calculated_value",
                    "status", "confidence", "evidence_refs"
                ],
            },
        },
        "uncertainties": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "topic": {"type": "string"},
                    "reason": {"type": "string"},
                    "confidence": {"type": "number"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "topic", "reason", "confidence", "evidence_refs"
                ],
            },
        },
    },
    "required": [
        "document_type", "summary", "entities", "facts",
        "relationships", "sections", "items",
        "visual_observations", "numeric_checks", "uncertainties"
    ],
}


def _compact_local_context(knowledge) -> dict[str, Any]:
    metadata = getattr(knowledge, "metadata", {}) or {}
    universal = metadata.get("deep_universal_understanding", {}) or {}

    return {
        "document_id": getattr(knowledge, "document_id", ""),
        "file_name": getattr(knowledge, "file_name", ""),
        "page_count": getattr(knowledge, "page_count", 0),
        "document_kind": universal.get("document_kind", ""),
        "resolved_roles": metadata.get("deep_resolved_roles", []),
        "semantic_fields": universal.get("semantic_fields", []),
        "conflicts": universal.get("conflicts", []),
        "capture_audit": getattr(knowledge, "capture_audit", {}) or {},
    }


def build_user_prompt(
    *,
    knowledge,
    route: str,
    selected_context: dict[str, Any],
    include_full_pdf: bool,
) -> str:
    selected_context = selected_context or {}

    prompt_selected_context = dict(selected_context)

    selected_images = selected_context.get("selected_images", ()) or ()

    prompt_selected_context["selected_images"] = [
        {
            "page_number": image.get("page_number"),
            "sha256": image.get("sha256", ""),
            "detail": image.get("detail", "low"),
        }
        for image in selected_images
        if isinstance(image, dict)
    ]

    payload = {
        "task": "universal_document_understanding",
        "route": route,
        "full_pdf_attached": include_full_pdf,
        "local_context": _compact_local_context(knowledge),
        "selected_evidence": prompt_selected_context,
    }

    return (
        "Interpreta el documento suministrado y devuelve únicamente el JSON del esquema. "
        "El conocimiento se entregará a ZOVRAKE para validación y fusión. "
        "No generes una decisión empresarial final.\n\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )