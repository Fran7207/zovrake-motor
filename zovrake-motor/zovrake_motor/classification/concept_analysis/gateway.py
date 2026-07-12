"""Vista de solo lectura del Modelo Documental Interno — sin acoplamiento a comprehension."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.exceptions import InternalModelAccessError


@dataclass(frozen=True)
class InternalModelView:
    """
    Representación de solo lectura del Modelo Documental Interno.

    El CAE nunca modifica el modelo original ni accede al documento fuente.
    """

    model_id: str
    document_id: str
    schema_version: str
    immutable: bool
    classification_ready: bool
    traceability: dict[str, Any]
    document: dict[str, Any]
    provider: dict[str, Any]
    commercial_information: dict[str, Any]
    technical_information: dict[str, Any]
    items: tuple[dict[str, Any], ...]
    commercial_conditions: tuple[dict[str, Any], ...]
    observations: tuple[dict[str, Any], ...]
    metadata: dict[str, Any]
    requirement_context: dict[str, Any]
    original_references: dict[str, Any]
    raw_model: dict[str, Any]

    @property
    def process_id(self) -> UUID:
        raw = self.traceability.get("process_id")
        if raw is None:
            raise InternalModelAccessError("traceability.process_id es obligatorio")
        return UUID(str(raw))


class InternalModelGateway:
    """
    Gateway de consumo del Modelo Documental Interno.

    Valida y expone una vista inmutable sin importar el módulo de Comprensión.
    """

    REQUIRED_SECTIONS: tuple[str, ...] = (
        "model_id",
        "traceability",
        "document",
        "items",
        "commercial_information",
        "technical_information",
        "commercial_conditions",
        "observations",
        "original_references",
    )

    def validate(self, request_model: dict[str, Any]) -> InternalModelView:
        if not isinstance(request_model, dict):
            raise InternalModelAccessError("El modelo documental interno debe ser un diccionario")

        missing = [section for section in self.REQUIRED_SECTIONS if section not in request_model]
        if missing:
            raise InternalModelAccessError(
                f"Secciones obligatorias ausentes en el modelo interno: {', '.join(missing)}",
            )

        if not request_model.get("immutable", True):
            raise InternalModelAccessError("El modelo documental interno debe ser inmutable")

        if not request_model.get("classification_ready", True):
            raise InternalModelAccessError("El modelo documental interno no está preparado para clasificación")

        document = request_model.get("document", {})
        document_id = str(document.get("document_id", "")).strip()
        if not document_id:
            raise InternalModelAccessError("document.document_id es obligatorio")

        return InternalModelView(
            model_id=str(request_model["model_id"]),
            document_id=document_id,
            schema_version=str(request_model.get("schema_version", "1.0")),
            immutable=bool(request_model.get("immutable", True)),
            classification_ready=bool(request_model.get("classification_ready", True)),
            traceability=dict(request_model.get("traceability", {})),
            document=dict(document),
            provider=dict(request_model.get("provider", {})),
            commercial_information=dict(request_model.get("commercial_information", {})),
            technical_information=dict(request_model.get("technical_information", {})),
            items=tuple(dict(item) for item in request_model.get("items", [])),
            commercial_conditions=tuple(
                dict(condition) for condition in request_model.get("commercial_conditions", [])
            ),
            observations=tuple(dict(observation) for observation in request_model.get("observations", [])),
            metadata=dict(request_model.get("metadata", {})),
            requirement_context=dict(request_model.get("requirement_context", {})),
            original_references=dict(request_model.get("original_references", {})),
            raw_model=request_model,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_internal_model": False,
            "accesses_original_documents": False,
            "required_sections": list(self.REQUIRED_SECTIONS),
        }
