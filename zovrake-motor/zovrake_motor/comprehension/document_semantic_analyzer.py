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
    Analizador semántico inicial del conocimiento documental.

    Esta capa no utiliza modelos externos de IA y no elimina información.

    Su responsabilidad es:
    - identificar encabezados/secciones;
    - utilizar la semántica de tablas ya descubierta;
    - evitar falsos positivos por palabras genéricas;
    - propagar contexto de sección a regiones posteriores de la misma página;
    - conservar el contenido físico original;
    - registrar las señales que justifican una clasificación.

    Esta clase NO intenta resolver todavía entidades, relaciones ni hechos
    complejos. Es una capa de contexto previa a esas operaciones.
    """

    MODEL_VERSION = "1.1-context-aware-semantic"

    # Frases fuertes que por sí solas pueden identificar una sección.
    # No usamos términos débiles como "unidad", "producto" o "total"
    # como identificadores de sección aislados.
    _EXPLICIT_SECTION_RULES: tuple[
        tuple[str, tuple[str, ...]],
        ...,
    ] = (
        (
            "provider_identity",
            (
                "datos del proveedor",
                "informacion del proveedor",
                "información del proveedor",
                "datos del emisor",
                "informacion del emisor",
                "información del emisor",
                "informacion de la empresa proveedora",
                "información de la empresa proveedora",
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
                "datos del destinatario",
                "informacion del destinatario",
                "información del destinatario",
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
                "cuentas bancarias",
                "cci",
                "swift",
                "iban",
                "datos de la cuenta",
                "cuentas recaudadoras",
            ),
        ),
        (
            "conditions",
            (
                "condiciones comerciales",
                "condiciones de pago",
                "forma de pago",
                "plazo de pago",
                "condiciones de venta",
                "condiciones de entrega",
                "tiempo de entrega",
                "plazo de entrega",
                "validez de la oferta",
                "validez de la cotización",
                "validez de la cotizacion",
                "garantia",
                "garantía",
                "vigencia de la oferta",
                "vigencia de la cotización",
            ),
        ),
        (
            "financial",
            (
                "resumen financiero",
                "resumen de costos",
                "resumen de costes",
                "subtotal",
                "igv",
                "iva",
                "impuestos",
                "tipo de cambio",
                "descuento",
                "precio total",
                "importe total",
                "monto total",
                "total a pagar",
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
                "especificaciones del producto",
                "datos tecnicos",
                "datos técnicos",
                "norma tecnica",
                "norma técnica",
                "requisitos tecnicos",
                "requisitos técnicos",
            ),
        ),
        (
            "commercial_items",
            (
                "detalle de productos",
                "detalle de servicios",
                "detalle de productos y servicios",
                "lista de productos",
                "lista de servicios",
                "detalle de cotizacion",
                "detalle de cotización",
                "detalle de la cotizacion",
                "detalle de la cotización",
            ),
        ),
        (
            "observation",
            (
                "observaciones",
                "observaciones generales",
                "observación",
                "observacion",
                "notas",
                "nota",
                "comentarios",
                "consideraciones",
            ),
        ),
    )

    # Señales de contenido que se evalúan solamente en combinación.
    _FINANCIAL_VALUE_RULES: tuple[str, ...] = (
        "subtotal",
        "igv",
        "iva",
        "impuesto",
        "descuento",
        "total a pagar",
        "importe total",
        "monto total",
        "tipo de cambio",
    )

    _COMMERCIAL_STRUCTURE_RULES: tuple[str, ...] = (
        "descripcion",
        "descripción",
        "cantidad",
        "precio unitario",
        "importe",
        "codigo",
        "código",
        "producto",
        "servicio",
        "unidad",
    )

    _BANKING_VALUE_RULES: tuple[str, ...] = (
        "banco",
        "cuenta",
        "cuenta corriente",
        "cuenta bancaria",
        "cci",
        "swift",
        "iban",
        "recaudadora",
        "soles",
        "dolares",
        "dólares",
    )

    _CONDITION_VALUE_RULES: tuple[str, ...] = (
        "validez",
        "vigencia",
        "plazo",
        "entrega",
        "forma de pago",
        "condiciones de pago",
        "garantia",
        "garantía",
    )

    _IDENTITY_VALUE_RULES: tuple[str, ...] = (
        "ruc",
        "razon social",
        "razón social",
        "direccion",
        "dirección",
        "telefono",
        "teléfono",
        "correo",
        "email",
    )

    _TECHNICAL_VALUE_RULES: tuple[str, ...] = (
        "especificacion",
        "especificación",
        "modelo",
        "marca",
        "material",
        "norma",
        "capacidad",
        "dimensiones",
        "caracteristica",
        "característica",
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
        "identity": "customer_identity",
    }

    _PAGE_CONTEXT_MAX_GAP = 4

    def analyze(
        self,
        knowledge: DocumentKnowledge,
    ) -> DocumentKnowledge:
        """
        Analiza todas las regiones sin eliminarlas ni modificar su contenido.

        El contexto se resuelve en orden documental dentro de cada página.
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

        current_page: int | None = None
        current_context = "unknown"
        current_context_confidence = 0.0
        current_context_hints: tuple[str, ...] = ()
        context_region_index = -10_000

        for index, region in enumerate(
            knowledge.regions,
        ):
            if current_page != region.page_number:
                current_page = region.page_number
                current_context = "unknown"
                current_context_confidence = 0.0
                current_context_hints = ()
                context_region_index = -10_000

            (
                direct_section,
                direct_confidence,
                direct_hints,
            ) = self._classify_region(
                region
            )

            if direct_section != "unknown":
                section = direct_section
                confidence = direct_confidence
                hints = direct_hints

                # Un encabezado/señal explícita actualiza el contexto de la
                # página para regiones posteriores.
                if self._is_context_anchor(
                    region,
                    section,
                    direct_hints,
                ):
                    current_context = section
                    current_context_confidence = confidence
                    current_context_hints = direct_hints
                    context_region_index = index
            elif (
                current_context != "unknown"
                and index - context_region_index
                <= self._PAGE_CONTEXT_MAX_GAP
                and self._can_inherit_context(region)
            ):
                section = current_context
                confidence = round(
                    current_context_confidence * 0.88,
                    4,
                )
                hints = tuple(
                    dict.fromkeys(
                        (
                            "context:inherited",
                            *current_context_hints,
                        )
                    )
                )
            else:
                # ``unknown`` no significa ausencia de evidencia. Cuando
                # ``_classify_region`` detecta una ambigüedad, debe conservar
                # su confianza y sus señales para que las capas superiores
                # conozcan exactamente por qué la región no fue resuelta.
                section = "unknown"
                confidence = direct_confidence
                hints = direct_hints

            metadata = dict(region.metadata)

            metadata.update(
                {
                    "document_section": section,
                    "semantic_context_confidence": confidence,
                    "semantic_model_version": self.MODEL_VERSION,
                    "semantic_hints": hints,
                }
            )

            analyzed_region = replace(
                region,
                metadata=metadata,
            )

            analyzed_regions.append(
                analyzed_region
            )

            if section != "unknown":
                sections.append(
                    self._section_record(
                        analyzed_region,
                        section=section,
                        confidence=confidence,
                        hints=hints,
                    )
                )

        metadata = dict(
            knowledge.metadata
        )

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
                "semantic_unknown_regions": (
                    sum(
                        1
                        for region in analyzed_regions
                        if region.metadata.get(
                            "document_section"
                        )
                        == "unknown"
                    )
                ),
            }
        )

        return replace(
            knowledge,
            regions=tuple(
                analyzed_regions
            ),
            sections=tuple(
                sections
            ),
            metadata=metadata,
        )

    def _classify_region(
        self,
        region: DocumentRegion,
    ) -> tuple[
        str,
        float,
        tuple[str, ...],
    ]:
        """
        Clasifica una región usando señales fuertes y combinaciones.

        Palabras genéricas como ``unidad`` o ``total`` no determinan por sí
        solas una sección; esto evita los falsos positivos observados en PDFs
        reales.
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

        # Encabezados explícitos e incompatibles dentro de la misma región
        # son una ambigüedad estructural. Se resuelve antes de cualquier
        # scoring secundario para impedir que el orden de las reglas haga
        # ganar arbitrariamente a uno de los roles.
        explicit_heading_hits: dict[str, tuple[str, ...]] = {}

        for section, phrases in self._EXPLICIT_SECTION_RULES:
            matched_phrases = tuple(
                phrase
                for phrase in phrases
                if self._normalize(phrase) in combined
            )

            if matched_phrases:
                explicit_heading_hits[section] = matched_phrases

        explicit_heading_sections = tuple(
            explicit_heading_hits.keys()
        )

        if len(explicit_heading_sections) > 1:
            competing_hints = tuple(
                hint
                for section in explicit_heading_sections
                for phrase in explicit_heading_hits[section]
                for hint in (f"{section}:{phrase}",)
            )

            return (
                "unknown",
                0.49,
                tuple(
                    dict.fromkeys(
                        (*competing_hints, "ambiguous_semantic_context")
                    )
                ),
            )

        explicit_scores: dict[str, float] = {}
        hints_by_section: dict[str, list[str]] = {}

        # ---------------------------------------------------------
        # 1. Encabezados/secciones explícitos.
        # ---------------------------------------------------------
        for section, phrases in (
            self._EXPLICIT_SECTION_RULES
        ):
            matches = [
                phrase
                for phrase in phrases
                if self._normalize(
                    phrase
                ) in combined
            ]

            if matches:
                explicit_scores[section] = min(
                    1.0,
                    0.65
                    + (
                        0.12
                        * (
                            len(matches) - 1
                        )
                    ),
                )

                hints_by_section[section] = [
                    f"{section}:{phrase}"
                    for phrase in matches
                ]

        # ---------------------------------------------------------
        # 2. Semántica declarada por la tabla.
        # ---------------------------------------------------------
        table_roles = self._extract_table_roles(
            region
        )

        for role in table_roles:
            explicit_scores[role] = max(
                explicit_scores.get(
                    role,
                    0.0,
                ),
                0.85,
            )

            hints_by_section.setdefault(
                role,
                [],
            ).append(
                f"table_role:{role}"
            )

        # ---------------------------------------------------------
        # 3. Señales combinadas para regiones de contenido.
        # ---------------------------------------------------------
        self._add_combined_signal(
            text=combined,
            section="financial",
            markers=self._FINANCIAL_VALUE_RULES,
            target_scores=explicit_scores,
            target_hints=hints_by_section,
            minimum_matches=2,
            score=0.72,
        )

        self._add_combined_signal(
            text=combined,
            section="banking",
            markers=self._BANKING_VALUE_RULES,
            target_scores=explicit_scores,
            target_hints=hints_by_section,
            minimum_matches=2,
            score=0.74,
        )

        self._add_combined_signal(
            text=combined,
            section="conditions",
            markers=self._CONDITION_VALUE_RULES,
            target_scores=explicit_scores,
            target_hints=hints_by_section,
            minimum_matches=2,
            score=0.70,
        )

        self._add_combined_signal(
            text=combined,
            section="provider_identity",
            markers=self._IDENTITY_VALUE_RULES,
            target_scores=explicit_scores,
            target_hints=hints_by_section,
            minimum_matches=2,
            score=0.68,
        )

        self._add_combined_signal(
            text=combined,
            section="technical",
            markers=self._TECHNICAL_VALUE_RULES,
            target_scores=explicit_scores,
            target_hints=hints_by_section,
            minimum_matches=2,
            score=0.68,
        )

        # ---------------------------------------------------------
        # 4. Estructura comercial.
        #
        # Solo aceptamos una clasificación comercial por contenido si:
        # - hay al menos 2 señales estructurales;
        # - la región es tabla/semantic_table; o
        # - existe un encabezado explícito de detalle.
        #
        # No se clasifica un bloque de texto solo porque mencione "unidad".
        # ---------------------------------------------------------
        commercial_matches = [
            marker
            for marker in self._COMMERCIAL_STRUCTURE_RULES
            if self._normalize(marker)
            in combined
        ]

        if (
            len(commercial_matches) >= 2
            and region.region_type
            in {
                "table",
                "semantic_table",
            }
        ):
            explicit_scores["commercial_items"] = max(
                explicit_scores.get(
                    "commercial_items",
                    0.0,
                ),
                0.70,
            )

            hints_by_section.setdefault(
                "commercial_items",
                [],
            ).extend(
                f"commercial_structure:{marker}"
                for marker in commercial_matches
            )

        if not explicit_scores:
            return (
                "unknown",
                0.0,
                (),
            )

        ranked = sorted(
            explicit_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        best_section, best_score = ranked[0]

        # Si dos interpretaciones fuertes compiten por contenido, devolvemos
        # unknown en vez de fingir una certeza inexistente.
        if len(ranked) > 1:
            second_section, second_score = ranked[1]

            if (
                best_score - second_score
                < 0.08
                and (
                    best_score >= 0.60
                    and second_score >= 0.60
                )
            ):
                hints = tuple(
                    dict.fromkeys(
                        (
                            *hints_by_section.get(
                                best_section,
                                [],
                            ),
                            *hints_by_section.get(
                                second_section,
                                [],
                            ),
                            "ambiguous_semantic_context",
                        )
                    )
                )

                return (
                    "unknown",
                    round(
                        min(
                            best_score,
                            0.49,
                        ),
                        4,
                    ),
                    hints,
                )

        hints = tuple(
            dict.fromkeys(
                hints_by_section.get(
                    best_section,
                    [],
                )
            )
        )

        return (
            best_section,
            round(
                best_score,
                4,
            ),
            hints,
        )

    @classmethod
    def _extract_table_roles(
        cls,
        region: DocumentRegion,
    ) -> tuple[str, ...]:
        roles: list[str] = []

        table_role = cls._normalize(
            str(
                region.metadata.get(
                    "table_role",
                    "",
                )
            )
        )

        if table_role:
            mapped = cls._TABLE_ROLE_MAP.get(
                table_role
            )

            if mapped:
                roles.append(mapped)

        table_roles = region.metadata.get(
            "table_roles",
            (),
        )

        if isinstance(
            table_roles,
            str,
        ):
            values = (
                role.strip()
                for role in table_roles.split(",")
            )
        elif isinstance(
            table_roles,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        ):
            values = (
                str(role)
                for role in table_roles
            )
        else:
            values = ()

        for role in values:
            mapped = cls._TABLE_ROLE_MAP.get(
                cls._normalize(role)
            )

            if mapped:
                roles.append(mapped)

        return tuple(
            dict.fromkeys(roles)
        )

    @staticmethod
    def _add_combined_signal(
        *,
        text: str,
        section: str,
        markers: Iterable[str],
        target_scores: dict[str, float],
        target_hints: dict[str, list[str]],
        minimum_matches: int,
        score: float,
    ) -> None:
        matches = [
            marker
            for marker in markers
            if DocumentSemanticAnalyzer._normalize(
                marker
            ) in text
        ]

        if len(matches) < minimum_matches:
            return

        target_scores[section] = max(
            target_scores.get(
                section,
                0.0,
            ),
            score,
        )

        target_hints.setdefault(
            section,
            [],
        ).extend(
            f"{section}:{marker}"
            for marker in matches
        )

    @staticmethod
    def _is_context_anchor(
        region: DocumentRegion,
        section: str,
        hints: tuple[str, ...],
    ) -> bool:
        """
        Determina si una región tiene fuerza suficiente para abrir contexto
        para los bloques posteriores.
        """
        if section == "unknown":
            return False

        if region.region_type in {
            "table",
            "semantic_table",
        }:
            return any(
                hint.startswith(
                    "table_role:"
                )
                or hint.startswith(
                    "table_roles:"
                )
                for hint in hints
            )

        return any(
            ":" in hint
            and not hint.startswith(
                "context:"
            )
            for hint in hints
        )

    @staticmethod
    def _can_inherit_context(
        region: DocumentRegion,
    ) -> bool:
        """
        Solo permite heredar contexto a regiones que no sean una entidad
        estructural fuerte incompatible.

        Las tablas semánticas ya clasificadas siempre se clasifican por su
        propia información y no dependen del contexto anterior.
        """
        if region.region_type in {
            "semantic_table",
        }:
            return False

        return True

    @staticmethod
    def _section_record(
        region: DocumentRegion,
        *,
        section: str,
        confidence: float,
        hints: Iterable[str],
    ) -> dict[str, Any]:
        """
        Crea un registro trazable de la sección detectada.
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
        Normaliza únicamente para comparar.

        Nunca modifica el contenido almacenado en DocumentKnowledge.
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
                frozenset,
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
