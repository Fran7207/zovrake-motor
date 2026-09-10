"""Validador defensivo de la respuesta de comprensión."""

from __future__ import annotations

from typing import Any


_REQUIRED = (
    "document_type",
    "summary",
    "entities",
    "facts",
    "relationships",
    "sections",
    "items",
    "visual_observations",
    "numeric_checks",
    "uncertainties",
)


def _require_confidence(item: dict[str, Any], section: str) -> None:
    value = item.get("confidence", 0.0)
    if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"Confianza inválida en {section}.")
    refs = item.get("evidence_refs", [])
    if not isinstance(refs, list):
        raise ValueError(f"evidence_refs inválido en {section}.")


def validate_understanding(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("La respuesta de comprensión no es un objeto JSON.")

    for key in _REQUIRED:
        if key not in payload:
            raise ValueError(f"Falta el campo requerido: {key}")

    if not isinstance(payload["document_type"], str):
        raise ValueError("document_type inválido.")
    if not isinstance(payload["summary"], str):
        raise ValueError("summary inválido.")

    for key in _REQUIRED[2:]:
        if not isinstance(payload[key], list):
            raise ValueError(f"Campo requerido inválido: {key}")

    for section, required_text_field in (
        ("entities", "name"),
        ("facts", "attribute"),
        ("relationships", "relationship"),
        ("sections", "name"),
        ("items", "description"),
        ("visual_observations", "image_type"),
        ("numeric_checks", "status"),
        ("uncertainties", "topic"),
    ):
        for item in payload[section]:
            if not isinstance(item, dict):
                raise ValueError(f"Elemento inválido en {section}.")
            if not str(item.get(required_text_field, "")).strip():
                raise ValueError(
                    f"Falta {required_text_field} en {section}."
                )
            _require_confidence(item, section)

    return payload
