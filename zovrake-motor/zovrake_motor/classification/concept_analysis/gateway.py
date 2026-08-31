"""Vista de solo lectura del Modelo Documental Interno — sin acoplamiento a comprehension."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.exceptions import (
    InternalModelAccessError,
)


@dataclass(frozen=True)
class InternalModelView:
    """
    Representación de solo lectura del Modelo Documental Interno.

    El CAE nunca modifica el modelo original ni accede al documento fuente.

    Además de las entidades tradicionales del IDMB, expone una vista
    controlada del ``document_knowledge`` que ya fue transportado dentro
    de ``metadata`` por Comprensión Documental.

    El gateway no importa ``DocumentKnowledge`` ni ninguna clase del módulo
    de comprensión. Esto mantiene el límite arquitectónico entre módulos.
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
            raise InternalModelAccessError(
                "traceability.process_id es obligatorio"
            )

        try:
            return UUID(str(raw))
        except ValueError as exc:
            raise InternalModelAccessError(
                "traceability.process_id no contiene un UUID válido"
            ) from exc

    @property
    def document_knowledge(self) -> dict[str, Any]:
        """
        Devuelve el conocimiento documental transportado.

        Contrato aceptado:

            metadata["extraction_metadata"]["document_knowledge"]

        También se soporta directamente:

            metadata["document_knowledge"]

        La vista devuelve siempre un diccionario nuevo para impedir que un
        consumidor del CAE modifique accidentalmente el modelo original.
        """
        candidate = self.metadata.get(
            "document_knowledge"
        )

        if isinstance(
            candidate,
            dict,
        ):
            return dict(candidate)

        extraction_metadata = self.metadata.get(
            "extraction_metadata"
        )

        if isinstance(
            extraction_metadata,
            dict,
        ):
            nested = extraction_metadata.get(
                "document_knowledge"
            )

            if isinstance(
                nested,
                dict,
            ):
                return dict(nested)

        return {}

    @property
    def knowledge_regions(self) -> tuple[dict[str, Any], ...]:
        """Regiones documentales conservadas y analizadas."""
        return self._knowledge_sequence(
            "regions"
        )

    @property
    def knowledge_entities(self) -> tuple[dict[str, Any], ...]:
        """Entidades documentales resueltas."""
        return self._knowledge_sequence(
            "entities"
        )

    @property
    def knowledge_facts(self) -> tuple[dict[str, Any], ...]:
        """Hechos observables extraídos del documento."""
        return self._knowledge_sequence(
            "facts"
        )

    @property
    def knowledge_attributes(self) -> tuple[dict[str, Any], ...]:
        """Atributos derivados de hechos etiquetados."""
        return self._knowledge_sequence(
            "attributes"
        )

    @property
    def knowledge_relationships(self) -> tuple[dict[str, Any], ...]:
        """Relaciones documentales resueltas."""
        return self._knowledge_sequence(
            "relationships"
        )

    @property
    def knowledge_evidence(self) -> tuple[dict[str, Any], ...]:
        """Evidencias preservadas del documento."""
        return self._knowledge_sequence(
            "evidence"
        )

    @property
    def knowledge_tables(self) -> tuple[dict[str, Any], ...]:
        """Tablas documentales conservadas."""
        return self._knowledge_sequence(
            "tables"
        )

    @property
    def has_document_knowledge(self) -> bool:
        """Indica si existe conocimiento documental transportado."""
        return bool(
            self.document_knowledge
        )

    @property
    def knowledge_metadata(self) -> dict[str, Any]:
        """Metadata propia de DocumentKnowledge."""
        raw = self.document_knowledge.get(
            "metadata",
            {},
        )

        if not isinstance(
            raw,
            dict,
        ):
            return {}

        return dict(raw)

    def _knowledge_sequence(
        self,
        key: str,
    ) -> tuple[dict[str, Any], ...]:
        raw = self.document_knowledge.get(
            key,
            (),
        )

        if not isinstance(
            raw,
            (list, tuple),
        ):
            return ()

        result: list[dict[str, Any]] = []

        for value in raw:
            if isinstance(
                value,
                dict,
            ):
                result.append(
                    dict(value)
                )

        return tuple(result)


class InternalModelGateway:
    """
    Gateway de consumo del Modelo Documental Interno.

    Valida y expone una vista inmutable sin importar el módulo de Comprensión.

    El conocimiento documental transportado se consume solamente a través
    de ``InternalModelView``. El CAE no accede al documento original.
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

    def validate(
        self,
        request_model: dict[str, Any],
    ) -> InternalModelView:
        if not isinstance(
            request_model,
            dict,
        ):
            raise InternalModelAccessError(
                "El modelo documental interno debe ser un diccionario"
            )

        missing = [
            section
            for section in self.REQUIRED_SECTIONS
            if section not in request_model
        ]

        if missing:
            raise InternalModelAccessError(
                "Secciones obligatorias ausentes en el modelo interno: "
                + ", ".join(missing)
            )

        if not request_model.get(
            "immutable",
            True,
        ):
            raise InternalModelAccessError(
                "El modelo documental interno debe ser inmutable"
            )

        if not request_model.get(
            "classification_ready",
            True,
        ):
            raise InternalModelAccessError(
                "El modelo documental interno no está preparado para clasificación"
            )

        document = request_model.get(
            "document",
            {},
        )

        if not isinstance(
            document,
            dict,
        ):
            raise InternalModelAccessError(
                "document debe ser un diccionario"
            )

        document_id = str(
            document.get(
                "document_id",
                "",
            )
        ).strip()

        if not document_id:
            raise InternalModelAccessError(
                "document.document_id es obligatorio"
            )

        traceability = request_model.get(
            "traceability",
            {},
        )

        if not isinstance(
            traceability,
            dict,
        ):
            raise InternalModelAccessError(
                "traceability debe ser un diccionario"
            )

        provider = request_model.get(
            "provider",
            {},
        )

        if not isinstance(
            provider,
            dict,
        ):
            raise InternalModelAccessError(
                "provider debe ser un diccionario"
            )

        commercial_information = request_model.get(
            "commercial_information",
            {},
        )

        if not isinstance(
            commercial_information,
            dict,
        ):
            raise InternalModelAccessError(
                "commercial_information debe ser un diccionario"
            )

        technical_information = request_model.get(
            "technical_information",
            {},
        )

        if not isinstance(
            technical_information,
            dict,
        ):
            raise InternalModelAccessError(
                "technical_information debe ser un diccionario"
            )

        metadata = request_model.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            raise InternalModelAccessError(
                "metadata debe ser un diccionario"
            )

        requirement_context = request_model.get(
            "requirement_context",
            {},
        )

        if not isinstance(
            requirement_context,
            dict,
        ):
            raise InternalModelAccessError(
                "requirement_context debe ser un diccionario"
            )

        original_references = request_model.get(
            "original_references",
            {},
        )

        if not isinstance(
            original_references,
            dict,
        ):
            raise InternalModelAccessError(
                "original_references debe ser un diccionario"
            )

        raw_items = request_model.get(
            "items",
            [],
        )

        if not isinstance(
            raw_items,
            (list, tuple),
        ):
            raise InternalModelAccessError(
                "items debe ser una lista o tupla"
            )

        raw_conditions = request_model.get(
            "commercial_conditions",
            [],
        )

        if not isinstance(
            raw_conditions,
            (list, tuple),
        ):
            raise InternalModelAccessError(
                "commercial_conditions debe ser una lista o tupla"
            )

        raw_observations = request_model.get(
            "observations",
            [],
        )

        if not isinstance(
            raw_observations,
            (list, tuple),
        ):
            raise InternalModelAccessError(
                "observations debe ser una lista o tupla"
            )

        return InternalModelView(
            model_id=str(
                request_model[
                    "model_id"
                ]
            ),
            document_id=document_id,
            schema_version=str(
                request_model.get(
                    "schema_version",
                    "1.0",
                )
            ),
            immutable=bool(
                request_model.get(
                    "immutable",
                    True,
                )
            ),
            classification_ready=bool(
                request_model.get(
                    "classification_ready",
                    True,
                )
            ),
            traceability=dict(
                traceability
            ),
            document=dict(
                document
            ),
            provider=dict(
                provider
            ),
            commercial_information=dict(
                commercial_information
            ),
            technical_information=dict(
                technical_information
            ),
            items=tuple(
                dict(item)
                for item in raw_items
                if isinstance(
                    item,
                    dict,
                )
            ),
            commercial_conditions=tuple(
                dict(condition)
                for condition in raw_conditions
                if isinstance(
                    condition,
                    dict,
                )
            ),
            observations=tuple(
                dict(observation)
                for observation in raw_observations
                if isinstance(
                    observation,
                    dict,
                )
            ),
            metadata=dict(
                metadata
            ),
            requirement_context=dict(
                requirement_context
            ),
            original_references=dict(
                original_references
            ),
            raw_model=request_model,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_internal_model": False,
            "accesses_original_documents": False,
            "document_knowledge_access": True,
            "document_knowledge_source": (
                "internal_model_metadata"
            ),
            "required_sections": list(
                self.REQUIRED_SECTIONS
            ),
        }
