"""Análisis semántico determinista de un conocimiento documental."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from zovrake_motor.comprehension.models import (
    DocumentKnowledge,
    DocumentRegion,
)


class DocumentSemanticAnalyzer:
    """
    Clasifica regiones de un ``DocumentKnowledge`` en contextos documentales.

    Esta capa no utiliza modelos externos de IA y no elimina información.
    Su función es convertir la representación física ya preservada por
    ``DocumentKnowledgeBuilder`` en contexto semántico inicial.

    La clasificación es deliberadamente conservadora: una región puede
    conservar varias señales semánticas en ``semantic_hints`` y recibe un
    único contexto principal para facilitar el consumo por las siguientes
    capas.
    """

    MODEL_VERSION = "1.0-deterministic-semantic"

    _SECTION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "provider_identity",
            (
                "datos del proveedor",
                "informacion del proveedor",
                "información del proveedor",
                "datos del emisor",
                "informacion del emisor",
                "información del emisor",
                "razon social del proveedor",
                "razón social del proveedor",
            ),
        ),
        (
            "customer_identity",
            (
                "datos del cliente",
                "informacion del cliente",
                "información del cliente",
                "datos del comprador",
                "informacion del comprador",
                "información del comprador",
                "razon social del cliente",
                "razón social del cliente",
            ),
        ),
        (
            "banking",
            (
                "datos bancarios",
                "informacion bancaria",
                "información bancaria",
                "cuenta bancaria",
                "cuenta corriente",
                "cci",
                "swift",
                "iban",
                "banco:",
            ),
        ),
        (
            "conditions",
            (
                "condiciones comerciales",
                "condiciones de pago",
                "forma de pago",
                "plazo de pago",
                "tiempo de entrega",
                "plazo de entrega",
                "validez de la oferta",
                "validez de la cotizacion",
                "validez de la cotización",
                "garantia",
                "garantía",
                "vigencia",
            ),
        ),
        (
            "financial",
            (
                "subtotal",
                "igv",
                "iva",
                "impuesto",
                "total",
                "moneda",
                "tipo de cambio",
                "descuento",
                "precio total",
                "monto total",
            ),
        ),
        (
            "technical",
            (
                "especificaciones tecnicas",
                "especificaciones técnicas",
                "ficha tecnica",
                "ficha técnica",
                "caracteristicas tecnicas",
                "características técnicas",
                "material",
                "norma tecnica",
                "norma técnica",
                "modelo",
                "marca",
            ),
        ),
        (
            "commercial_items",
            (
                "descripcion",
                "descripción",
                "cantidad",
                "unidad",
                "precio unitario",
                "importe",
                "producto",
                "servicio",
                "codigo",
                "código",
                "item",
            ),
        ),
        (
            "observation",
            (
                "observaciones",
                "observacion",
                "observación",
                "nota:",
                "notas:",
                "comentarios",
                "consideraciones",
                "importante:",
            ),
        ),
    )

    _TABLE_ROLE_MAP: dict[str, str] = {
        "commercial": "commercial_items",
        "commercial_items": "commercial_items",
        "items": "commercial_items",
        "conditions": "conditions",
        "condition": "conditions",
        "financial": "financial",
        "finance": "financial",
        "banking": "banking",
        "bank": "banking",
        "technical": "technical",
        "provider": "provider_identity",
        "provider_identity": "provider_identity",
        "customer": "customer_identity",
        "customer_identity": "customer_identity",
        "observation": "observation",
        "observations": "observation",
    }

    def analyze(
        self,
        knowledge: DocumentKnowledge,
    ) -> DocumentKnowledge:
        """
        Devuelve una nueva representación con contexto semántico inicial.

        No modifica el objeto recibido y no elimina regiones, tablas,
        imágenes, OCR ni evidencias.
        """
        if not isinstance(
            knowledge,
            DocumentKnowledge,
        ):
            raise TypeError(
                "knowledge debe ser una instancia de DocumentKnowledge"
            )

        sections: list[dict[str, Any]] = []
        analyzed_regions: list[DocumentRegion] = []

        for region in knowledge.regions:
            section, confidence, hints = (
                self._classify_region(region)
            )

            metadata = dict(region.metadata)

            metadata.update(
                {
                    "document_section": section,
                    "semantic_context_confidence": confidence,
                    "semantic_model_version": self.MODEL_VERSION,
                    "semantic_hints": hints,
                }
            )

            analyzed_regions.append(
                replace(
                    region,
                    metadata=metadata,
                )
            )

            if section != "unknown":
                sections.append(
                    self._section_record(
                        region,
                        section=section,
                        confidence=confidence,
                        hints=hints,
                    )
                )

        metadata = dict(knowledge.metadata)

        metadata.update(
            {
                "semantic_model_version": self.MODEL_VERSION,
                "semantic_stage": "region_context",
                "semantic_regions_analyzed": (
                    len(analyzed_regions)
                ),
                "semantic_sections_detected": (
                    len(sections)
                ),
            }
        )

        return replace(
            knowledge,
            regions=tuple(analyzed_regions),
            sections=tuple(sections),
            metadata=metadata,
        )

    def _classify_region(
        self,
        region: DocumentRegion,
    ) -> tuple[str, float, tuple[str, ...]]:
        """
        Clasifica una región utilizando el contenido y sus metadatos.

        No modifica el texto original.
        """
        text = self._normalize(
            region.content
        )

        metadata_text = self._normalize(
            " ".join(
                self._string_values(
                    region.metadata
                )
            )
        )

        combined = (
            f"{text} {metadata_text}"
        ).strip()

        scores: dict[str, float] = {}
        hints: list[str] = []

        for section, keywords in self._SECTION_RULES:
            matched = [
                keyword
                for keyword in keywords
                if self._normalize(keyword)
                in combined
            ]

            if matched:
                score = min(
                    1.0,
                    0.35 + 0.15 * len(matched),
                )

                scores[section] = score

                hints.extend(
                    f"{section}:{keyword}"
                    for keyword in matched
                )

        table_role = self._normalize(
            str(
                region.metadata.get(
                    "table_role",
                    "",
                )
            )
        )

        mapped_role = self._TABLE_ROLE_MAP.get(
            table_role
        )

        if mapped_role:
            scores[mapped_role] = max(
                scores.get(
                    mapped_role,
                    0.0,
                ),
                0.85,
            )

            hints.append(
                f"table_role:{table_role}"
            )

        table_roles = (
            region.metadata.get(
                "table_roles",
                (),
            )
            or ()
        )

        for role in table_roles:
            mapped = self._TABLE_ROLE_MAP.get(
                self._normalize(
                    str(role)
                )
            )

            if mapped:
                scores[mapped] = max(
                    scores.get(
                        mapped,
                        0.0,
                    ),
                    0.80,
                )

                hints.append(
                    f"table_roles:{role}"
                )

        region_type = self._normalize(
            region.region_type
        )

        if (
            region_type == "semantic_table"
            and not scores
        ):
            scores["commercial_items"] = 0.25
            hints.append(
                "semantic_table_without_role"
            )

        if (
            region_type == "table"
            and not scores
        ):
            scores["commercial_items"] = 0.20
            hints.append(
                "table_without_role"
            )

        if not scores:
            return (
                "unknown",
                0.0,
                (),
            )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        section, confidence = ranked[0]

        # Si dos contextos están prácticamente empatados,
        # no fingimos una certeza inexistente.
        if len(ranked) > 1:
            second_confidence = ranked[1][1]

            if (
                confidence
                - second_confidence
                < 0.08
            ):
                hints.append(
                    "ambiguous_semantic_context"
                )

                return (
                    "unknown",
                    round(
                        min(
                            confidence,
                            0.49,
                        ),
                        4,
                    ),
                    tuple(
                        dict.fromkeys(
                            hints
                        )
                    ),
                )

        return (
            section,
            round(
                confidence,
                4,
            ),
            tuple(
                dict.fromkeys(
                    hints
                )
            ),
        )

    @staticmethod
    def _section_record(
        region: DocumentRegion,
        *,
        section: str,
        confidence: float,
        hints: Iterable[str],
    ) -> dict[str, Any]:
        """
        Crea un registro de sección con trazabilidad hacia la región.
        """
        return {
            "section_id": (
                f"section-{region.region_id}"
            ),
            "section_type": section,
            "page_number": (
                region.page_number
            ),
            "region_id": (
                region.region_id
            ),
            "confidence": confidence,
            "source_kind": (
                region.source_kind
            ),
            "evidence_id": (
                f"evidence-{region.region_id}"
            ),
            "hints": list(hints),
        }

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """
        Normaliza espacios y mayúsculas sin alterar
        el contenido almacenado.
        """
        return " ".join(
            str(value)
            .casefold()
            .split()
        )

    @staticmethod
    def _string_values(
        value: Any,
    ) -> Iterable[str]:
        """
        Extrae valores textuales de metadatos anidados.
        """
        if isinstance(
            value,
            str,
        ):
            yield value
            return

        if isinstance(
            value,
            dict,
        ):
            for key, item in value.items():
                yield str(key)

                yield from (
                    DocumentSemanticAnalyzer
                    ._string_values(item)
                )

            return

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            for item in value:
                yield from (
                    DocumentSemanticAnalyzer
                    ._string_values(item)
                )

            return

        if value is not None:
            yield str(value)