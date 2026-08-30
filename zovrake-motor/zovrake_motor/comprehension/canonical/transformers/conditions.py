"""Transformador de la sección Condiciones."""

from __future__ import annotations

from typing import Any, Iterable

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalCondition,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import ConditionsTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ConditionsTransformer(ConditionsTransformerPort):
    """
    Transforma condiciones documentales a la representación canónica.

    La entrada puede proceder de tres fuentes complementarias:

    1. elementos estructurales ya clasificados por la extracción;
    2. condiciones existentes en metadata;
    3. tablas semánticas clasificadas explícitamente como ``conditions``.

    La tercera fuente es especialmente importante para PDF: una condición
    puede venir representada como una tabla de pares etiqueta/valor y no como
    un bloque de texto libre. La información original de cada fila se conserva
    en ``fields`` para que PM5/PM6/PM7 pueda utilizarla posteriormente.

    El transformador no intenta reinterpretar todo el PDF ni elimina datos.
    Su responsabilidad es proyectar a ``CanonicalCondition`` aquello que ya
    cuenta con evidencia suficiente de pertenecer a la sección de condiciones.
    """

    _STRUCTURAL_CONDITION_TYPES = frozenset(
        {
            "condition",
            "footer",
            "terms",
        }
    )

    _CONDITION_TYPE_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "validity",
            (
                "validez",
                "vigencia",
                "vigencia de la oferta",
                "valida hasta",
                "válida hasta",
            ),
        ),
        (
            "delivery",
            (
                "plazo de entrega",
                "tiempo de entrega",
                "entrega",
                "plazo",
            ),
        ),
        (
            "payment",
            (
                "forma de pago",
                "condiciones de pago",
                "pago",
                "pagos",
                "crédito",
                "credito",
            ),
        ),
        (
            "warranty",
            (
                "garantía",
                "garantia",
                "garantías",
                "garantias",
            ),
        ),
        (
            "taxes",
            (
                "igv",
                "iva",
                "impuesto",
                "impuestos",
            ),
        ),
        (
            "additional_cost",
            (
                "costo adicional",
                "costos adicionales",
                "flete",
                "transporte",
                "instalación",
                "instalacion",
            ),
        ),
        (
            "commercial",
            (
                "condiciones comerciales",
                "terminos comerciales",
                "términos comerciales",
                "condiciones",
                "terminos",
                "términos",
            ),
        ),
    )

    def __init__(self) -> None:
        """Inicializa el transformador sin estado mutable por documento."""

    @property
    def transformer_name(self) -> str:
        return "conditions_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Condiciones"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.CONDITIONS

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_conditions(
            extraction_result,
            traceability=traceability,
        )

        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation=(
                "Condiciones transformadas desde elementos estructurales, "
                "metadata y tablas semánticas clasificadas"
            ),
        )

    def build_conditions(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalCondition, ...]:
        """
        Construye condiciones canónicas sin descartar evidencia previa.

        El orden de precedencia es estable:
        1. elementos estructurales;
        2. metadata de condiciones;
        3. tablas semánticas con ``table_role == conditions``.

        Antes de devolver el resultado se eliminan duplicados exactos por una
        clave estable derivada del tipo, contenido y referencia de origen.
        """
        section_ref = source_reference(
            traceability.extraction_reference_id,
            self.section_type,
        )

        conditions: list[CanonicalCondition] = []
        seen: set[tuple[str, str, str]] = set()

        # -------------------------------------------------------------
        # 1. Elementos estructurales ya identificados como condiciones.
        # -------------------------------------------------------------
        for index, element in enumerate(
            extraction_result.structural_elements
        ):
            if element.element_type not in self._STRUCTURAL_CONDITION_TYPES:
                continue

            content = self._normalize_text(element.content)
            if not content:
                continue

            condition_type = (
                self._normalize_text(element.element_type)
                or self._infer_condition_type(content)
            )

            fields = dict(element.metadata or {})
            fields.setdefault(
                "document_semantic_role",
                "conditions",
            )
            fields.setdefault(
                "source_kind",
                "structural_element",
            )

            self._append_condition(
                conditions=conditions,
                seen=seen,
                condition=CanonicalCondition(
                    condition_id=f"condition-element-{index}",
                    content=content,
                    source_reference=(
                        f"{section_ref}/element/{index}"
                    ),
                    condition_type=condition_type,
                    fields=fields,
                ),
            )

        # -------------------------------------------------------------
        # 2. Metadata producida por extractores anteriores.
        # -------------------------------------------------------------
        raw_conditions = metadata_value(
            extraction_result,
            "conditions",
            (),
        )

        if isinstance(raw_conditions, (list, tuple)):
            for index, condition_data in enumerate(raw_conditions):
                if not isinstance(condition_data, dict):
                    continue

                content = self._condition_content_from_mapping(
                    condition_data,
                )
                if not content:
                    continue

                condition_type = (
                    self._normalize_text(
                        condition_data.get("condition_type", "")
                    )
                    or self._infer_condition_type(content)
                )

                fields = dict(condition_data)
                fields.setdefault(
                    "document_semantic_role",
                    "conditions",
                )
                fields.setdefault(
                    "source_kind",
                    "metadata",
                )

                condition_id = self._normalize_text(
                    condition_data.get(
                        "condition_id",
                        f"meta-condition-{index}",
                    )
                )

                self._append_condition(
                    conditions=conditions,
                    seen=seen,
                    condition=CanonicalCondition(
                        condition_id=(
                            condition_id
                            or f"meta-condition-{index}"
                        ),
                        content=content,
                        source_reference=(
                            f"{section_ref}/metadata/{index}"
                        ),
                        condition_type=condition_type,
                        fields=fields,
                    ),
                )

        # -------------------------------------------------------------
        # 3. Tablas semánticas explícitamente clasificadas como conditions.
        # -------------------------------------------------------------
        semantic_tables = metadata_value(
            extraction_result,
            "semantic_tables",
            (),
        )

        if isinstance(semantic_tables, (list, tuple)):
            for table_index, table in enumerate(semantic_tables):
                if not isinstance(table, dict):
                    continue

                table_role = self._normalize_text(
                    table.get("table_role", "")
                ).lower()

                if table_role != "conditions":
                    continue

                rows = table.get("rows", ())
                if not isinstance(rows, (list, tuple)):
                    continue

                table_id = self._normalize_text(
                    table.get(
                        "table_id",
                        f"semantic-table-{table_index + 1}",
                    )
                ) or f"semantic-table-{table_index + 1}"

                source_table_id = self._normalize_text(
                    table.get("source_table_id", "")
                )

                source_page_number = table.get(
                    "source_page_number"
                )

                table_confidence = table.get(
                    "confidence",
                    0.0,
                )

                role_confidence = table.get(
                    "table_role_confidence",
                    0.0,
                )

                role_evidence = table.get(
                    "table_role_evidence",
                    (),
                )

                if not isinstance(
                    role_evidence,
                    (list, tuple),
                ):
                    role_evidence = (str(role_evidence),)

                table_evidence = table.get(
                    "evidence",
                    (),
                )

                if not isinstance(
                    table_evidence,
                    (list, tuple),
                ):
                    table_evidence = (str(table_evidence),)

                for row_index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        continue

                    content = self._condition_content_from_mapping(row)
                    if not content:
                        continue

                    condition_type = self._infer_condition_type(content)

                    fields: dict[str, Any] = {
                        "semantic_table_id": table_id,
                        "source_table_id": source_table_id,
                        "semantic_table_confidence": table_confidence,
                        "semantic_table_role": table_role,
                        "semantic_table_role_confidence": role_confidence,
                        "semantic_table_role_evidence": list(
                            role_evidence
                        ),
                        "semantic_table_source_page_number": (
                            source_page_number
                        ),
                        "semantic_table_evidence": list(
                            table_evidence
                        ),
                        "values": dict(row),
                        "document_semantic_role": "conditions",
                        "source_kind": "semantic_table",
                    }

                    source_id = source_table_id or table_id

                    self._append_condition(
                        conditions=conditions,
                        seen=seen,
                        condition=CanonicalCondition(
                            condition_id=(
                                f"{table_id}-condition-{row_index}"
                            ),
                            content=content,
                            source_reference=(
                                f"{section_ref}/"
                                f"{source_id}/"
                                f"{row_index}"
                            ),
                            condition_type=condition_type,
                            fields=fields,
                        ),
                    )

        return tuple(conditions)

    @classmethod
    def _append_condition(
        cls,
        *,
        conditions: list[CanonicalCondition],
        seen: set[tuple[str, str, str]],
        condition: CanonicalCondition,
    ) -> None:
        """Agrega una condición si no existe el mismo dato y origen."""
        content_key = cls._normalize_text(condition.content).casefold()
        type_key = cls._normalize_text(condition.condition_type).casefold()
        source_key = cls._normalize_text(condition.source_reference)

        identity = (
            type_key,
            content_key,
            source_key,
        )

        if identity in seen:
            return

        seen.add(identity)
        conditions.append(condition)

    @staticmethod
    def _normalize_text(value: Any) -> str:
        """Convierte de forma segura un valor documental en texto limpio."""
        if value is None:
            return ""

        text = str(value).replace("\x00", " ").strip()
        if not text:
            return ""

        return " ".join(text.split())

    @classmethod
    def _condition_content_from_mapping(
        cls,
        mapping: dict[str, Any],
    ) -> str:
        """
        Reconstruye el contenido legible de una condición desde una fila.

        No presupone nombres de columnas fijos. Primero intenta encontrar
        pares etiqueta/valor y, si no existen, conserva todos los valores
        disponibles en el orden original del mapping.
        """
        if not mapping:
            return ""

        preferred_label_keys = (
            "label",
            "name",
            "key",
            "concept",
            "description",
            "detail",
            "attribute",
            "field",
            "condition",
            "condition_type",
            "unit_price",
            "quantity",
            "unit",
            "total",
        )

        label_key = next(
            (
                key
                for key in preferred_label_keys
                if key in mapping
                and cls._normalize_text(mapping.get(key))
            ),
            None,
        )

        if label_key is not None:
            label = cls._normalize_text(mapping.get(label_key))
            value_parts = []

            for key, value in mapping.items():
                if key == label_key:
                    continue

                normalized = cls._normalize_text(value)
                if normalized:
                    value_parts.append(normalized)

            if value_parts:
                return f"{label}: {' | '.join(value_parts)}"

            return label

        values = []
        for value in mapping.values():
            normalized = cls._normalize_text(value)
            if normalized:
                values.append(normalized)

        return " | ".join(values)

    @classmethod
    def _infer_condition_type(cls, content: str) -> str:
        """Infiere un tipo de condición a partir de su contenido textual."""
        normalized = cls._normalize_text(content).casefold()
        if not normalized:
            return "condition"

        for condition_type, markers in cls._CONDITION_TYPE_MARKERS:
            for marker in markers:
                normalized_marker = cls._normalize_text(marker).casefold()
                if (
                    normalized_marker
                    and normalized_marker in normalized
                ):
                    return condition_type

        return "condition"
