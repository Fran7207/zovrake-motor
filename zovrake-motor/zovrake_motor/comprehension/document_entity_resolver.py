"""Resolución determinista de entidades dentro de DocumentKnowledge."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import re
from typing import Any, Iterable

from zovrake_motor.comprehension.models import (
    DocumentEntity,
    DocumentKnowledge,
    DocumentRelationship,
)


class DocumentEntityResolver:
    """
    Descubre entidades documentales a partir de evidencia ya extraída.

    La resolución es independiente del tipo de PDF. Se apoya en:

    - etiquetas explícitas;
    - secciones documentales;
    - identificadores;
    - razón social;
    - contexto lingüístico;
    - referencias del emisor;
    - referencias del cliente;
    - información ya detectada por las tablas.

    No elimina información y no utiliza modelos externos.

    Las hipótesis que no alcanzan evidencia suficiente permanecen en
    ``metadata["entity_candidates"]`` y no se publican como entidades
    resueltas.
    """

    MODEL_VERSION = "1.2-deterministic-multimodal-issuer-entity"

    _LEGAL_SUFFIX = re.compile(
        r"(?i)(?<![A-ZÁÉÍÓÚÜÑ])"
        r"(?:S\.?\s*A\.?\s*C\.?|"
        r"S\.?\s*R\.?\s*L\.?|"
        r"S\.?\s*A\.?|"
        r"E\.?\s*I\.?\s*R\.?\s*L\.?|"
        r"LTDA\.?|LIMITADA)"
        r"(?![A-ZÁÉÍÓÚÜÑ])"
    )

    _RUC = re.compile(
        r"(?i)\bR\.?\s*U\.?\s*C\.?(?:\s*[:\-]\s*)+"
        r"(?P<value>\d{11})\b"
    )

    _ROLE_HEADERS: dict[str, tuple[str, ...]] = {
        "provider": (
            "datos del proveedor",
            "datos del emisor",
            "informacion del proveedor",
            "información del proveedor",
            "informacion del emisor",
            "información del emisor",
            "empresa proveedora",
        ),
        "customer": (
            "datos del cliente",
            "datos del comprador",
            "datos del destinatario",
            "informacion del cliente",
            "información del cliente",
            "informacion del comprador",
            "información del comprador",
        ),
        "manufacturer": (
            "datos del fabricante",
            "informacion del fabricante",
            "información del fabricante",
        ),
        "representative": (
            "representante comercial",
            "asesor comercial",
            "ejecutivo comercial",
        ),
    }

    _ROLE_LABEL = re.compile(
        r"(?i)^\s*(?P<label>"
        r"proveedor|emisor|vendedor|cliente|comprador|destinatario|"
        r"fabricante|representante|"
        r"raz[oó]n\s+social|razon\s+social"
        r")\s*[:\-]\s*(?P<value>.+?)\s*$"
    )

    _RECIPIENT_HEADER = re.compile(
        r"(?i)^\s*(?:señor(?:es)?|sres?\.?|señora(?:s)?)\s*"
        r"[:\-]?\s*(?P<value>.+?)\s*$"
    )

    _RECIPIENT_INLINE = re.compile(
        r"(?i)\b(?:señor(?:es)?|sres?\.?|señora(?:s)?)\s*"
        r"[:\-]\s*(?P<value>.*?)(?=\s+soles\b|\s+fecha\b|\s+\d{1,2}/\d{1,2}/\d{2,4}\b|$)"
    )

    _BANK_IDENTITY_HEADER = re.compile(
        r"(?i)^\s*(?:cuentas?\s+bancarias|datos\s+bancarios|"
        r"informaci[oó]n\s+bancaria|bank\s+accounts?)\s+"
        r"(?:de\s+|del\s+|de\s+la\s+)?(?P<value>.+?)\s*$"
    )

    _PAYEE_LABEL = re.compile(
        r"(?i)\b(?:depositar|dep[oó]sito)\s+a\s+nombre\s*[:\-]\s*"
        r"(?P<value>.+?)(?=\s+R\.?\s*U\.?\s*C\.?\s*[:\-]|\s+Cuentas?\s+Recaudadoras\b|\s*$)"
    )

    _HEADER_CUSTOMER_MARKER = re.compile(
        r"(?i)\b(?:ref|referencia|obra|proyecto|atencion|atención)\s*[:\-]?"
    )

    _ISSUER_TRANSITION = re.compile(
        r"(?i)\b(?:de\s+nuestra\s+consideraci[oó]n|"
        r"nos\s+dirigimos|cotizaci[oó]n\s+de\s+nuestros|"
        r"cotizamos\s+nuestros|ofrecemos\s+nuestros)\b"
    )

    _ISSUER_PHRASES = (
        "nuestra empresa",
        "nuestros productos",
        "nuestros servicios",
        "cotizamos",
        "ofrecemos",
        "de nuestra consideración",
        "atentamente",
        "quedamos de uds",
        "quedamos de ustedes",
    )

    _CUSTOMER_PHRASES = (
        "datos del cliente",
        "datos del comprador",
        "cliente:",
        "comprador:",
        "destinatario:",
        "facturar a",
    )

    _NON_ENTITY_PREFIXES = (
        "cta cte",
        "cuenta",
        "banco de credito",
        "banco de crédito",
        "nos dirigimos",
        "sobre el precio",
    )

    def resolve(
        self,
        knowledge: DocumentKnowledge,
    ) -> DocumentKnowledge:
        """
        Resuelve entidades y relaciones y devuelve una copia del conocimiento.

        El objeto de entrada nunca se modifica.
        """
        if not isinstance(
            knowledge,
            DocumentKnowledge,
        ):
            raise TypeError(
                "knowledge debe ser una instancia de DocumentKnowledge"
            )

        lines = [
            line.strip()
            for line in knowledge.text.splitlines()
            if line.strip()
        ]

        role_context = self._build_role_context(
            lines
        )

        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

        # ---------------------------------------------------------
        # Primera pasada:
        # las regiones mantienen la procedencia física del documento.
        # ---------------------------------------------------------
        for region in knowledge.regions:
            self._collect_region_candidates(
                region=region,
                role_context=role_context,
                candidates=candidates,
            )

        # ---------------------------------------------------------
        # Segunda pasada:
        # el texto completo permite recuperar entidades que fueron
        # separadas por el layout o por tablas distintas.
        # ---------------------------------------------------------
        self._collect_explicit_recipient_candidates(
            lines=lines,
            candidates=candidates,
        )

        self._collect_header_customer_candidates(
            lines=lines,
            candidates=candidates,
        )

        self._collect_text_candidates(
            lines=lines,
            role_context=role_context,
            candidates=candidates,
        )

        # Tercera pasada: utiliza evidencia visual y de identidad de contacto
        # que ya existe en DocumentKnowledge. No vuelve a abrir el PDF.
        self._collect_visual_identity_candidates(
            knowledge=knowledge,
            text_lines=lines,
            candidates=candidates,
        )

        ranked = self._rank(
            candidates
        )

        resolved_candidates = (
            self._select_resolved_candidates(
                ranked
            )
        )

        resolved_candidates = (
            self._remove_cross_role_duplicates(
                resolved_candidates
            )
        )

        entities = tuple(
            self._to_entity(
                candidate,
                document_id=knowledge.document_id,
            )
            for candidate in resolved_candidates
        )

        relationships = tuple(
            self._build_relationships(
                document_id=knowledge.document_id,
                entities=entities,
            )
        )

        metadata = dict(
            knowledge.metadata
        )

        metadata.update(
            {
                "entity_resolution_model_version": (
                    self.MODEL_VERSION
                ),
                "entity_resolution_stage": (
                    "candidate_and_role_resolution"
                ),
                "entity_count": len(
                    entities
                ),
                "relationship_count": len(
                    relationships
                ),
                "resolved_roles": sorted(
                    {
                        entity.role
                        for entity in entities
                    }
                ),
                "entity_candidates": [
                    self._candidate_dict(
                        candidate
                    )
                    for candidate in ranked
                ],
            }
        )

        return replace(
            knowledge,
            entities=entities,
            relationships=relationships,
            metadata=metadata,
        )

    def _build_role_context(
        self,
        lines: list[str],
    ) -> list[tuple[str, int, int]]:
        """
        Construye intervalos de contexto alrededor de encabezados explícitos.

        Un nuevo encabezado cierra el contexto anterior. Cada contexto tiene
        una ventana máxima para evitar arrastrar un rol por todo el documento.
        """
        markers: list[tuple[int, str]] = []

        for index, line in enumerate(lines):
            normalized = self._normalize(line)

            for role, phrases in self._ROLE_HEADERS.items():
                if any(
                    self._normalize(
                        phrase
                    ) in normalized
                    for phrase in phrases
                ):
                    markers.append(
                        (
                            index,
                            role,
                        )
                    )
                    break

        contexts: list[
            tuple[str, int, int]
        ] = []

        for marker_index, (
            start_index,
            role,
        ) in enumerate(markers):
            next_start = (
                markers[marker_index + 1][0]
                if marker_index + 1 < len(markers)
                else len(lines)
            )

            contexts.append(
                (
                    role,
                    start_index,
                    min(
                        next_start,
                        start_index + 14,
                    ),
                )
            )

        return contexts

    @staticmethod
    def _role_at(
        line_index: int,
        contexts: list[tuple[str, int, int]],
    ) -> str:
        matches = [
            role
            for role, start, end in contexts
            if start <= line_index < end
        ]

        unique = tuple(
            dict.fromkeys(
                matches
            )
        )

        if len(unique) == 1:
            return unique[0]

        if len(unique) > 1:
            return "ambiguous"

        return "unknown"

    def _collect_region_candidates(
        self,
        *,
        region: Any,
        role_context: list[tuple[str, int, int]],
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        """
        Obtiene candidatos directamente desde regiones preservadas.

        Esta ruta es la preferida para trazabilidad porque puede asociar
        la entidad con ``evidence_id`` y página.
        """
        content = region.content or ""

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        metadata_role = self._metadata_role(
            region
        )

        local_role = (
            metadata_role
            if metadata_role != "unknown"
            else self._infer_role_from_content(
                content
            )
        )

        for line in lines:
            role_match = self._ROLE_LABEL.match(
                line
            )

            if role_match:
                label = self._normalize(
                    role_match.group(
                        "label"
                    )
                )

                role = self._label_role(
                    label
                )

                if role == "unknown":
                    role = local_role

                value = self._clean_name(
                    role_match.group(
                        "value"
                    )
                )

                if role in {
                    "provider",
                    "customer",
                    "manufacturer",
                    "representative",
                }:
                    self._add_candidate(
                        role=role,
                        name=value,
                        region=region,
                        source="explicit_role_label",
                        score=28.0,
                        candidates=candidates,
                    )

            payee_match = self._PAYEE_LABEL.search(
                line
            )

            if payee_match:
                provider_name = self._clean_name(
                    payee_match.group(
                        "value"
                    )
                )

                self._add_candidate(
                    role="provider",
                    name=provider_name,
                    region=region,
                    source="explicit_payee",
                    score=52.0,
                    candidates=candidates,
                )

                region_ruc = self._find_nearby_identifier(
                    lines=lines,
                    start=max(0, lines.index(line) - 1),
                    end=min(
                        len(lines),
                        lines.index(line) + 3,
                    ),
                )

                if provider_name and region_ruc:
                    state = candidates.get(
                        (
                            "provider",
                            self._entity_key(
                                provider_name
                            ),
                        )
                    )

                    if state is not None:
                        state["identifier"] = region_ruc
                        state["score"] += 10.0
                        state["evidence"].append(
                            f"payee_tax_id:{region_ruc}"
                        )

            ruc_match = self._RUC.search(
                line
            )

            if ruc_match:
                self._attach_identifier_to_region(
                    role=local_role,
                    identifier=ruc_match.group(
                        "value"
                    ),
                    region=region,
                    candidates=candidates,
                )

    def _collect_explicit_recipient_candidates(
        self,
        *,
        lines: list[str],
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        """Recupera destinatarios marcados explícitamente en el encabezado."""
        for index, line in enumerate(lines[:24]):
            match = self._RECIPIENT_HEADER.match(line)
            if not match:
                match = self._RECIPIENT_INLINE.search(line)
            if not match:
                continue

            value = self._clean_name(match.group("value"))
            value_index = index

            if not self._looks_like_legal_entity(value):
                for next_index in range(index + 1, min(index + 3, len(lines))):
                    possible = self._clean_name(lines[next_index])
                    if self._looks_like_legal_entity(possible):
                        value = possible
                        value_index = next_index
                        break

            if not self._looks_like_legal_entity(value):
                continue

            ruc = self._find_recipient_identifier(
                lines=lines,
                line_index=index,
                inline_match=match if value_index == index else None,
            )

            self._add_candidate(
                role="customer",
                name=value,
                region=None,
                source="explicit_recipient_header",
                score=48.0,
                candidates=candidates,
            )

            state = candidates.get(("customer", self._entity_key(value)))
            if state is None:
                continue

            state["attributes"]["source_line_index"] = value_index
            state["attributes"]["recipient_marker"] = "señores"
            state["score"] += 12.0
            state["evidence"].append("explicit_recipient_header")

            if ruc:
                state["identifier"] = ruc
                state["score"] += 12.0
                state["evidence"].append(f"recipient_tax_id:{ruc}")

    def _collect_header_customer_candidates(
        self,
        *,
        lines: list[str],
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        """
        Recupera el destinatario empresarial de documentos donde el cliente
        aparece en el encabezado sin la etiqueta literal ``CLIENTE``.

        Patrón observado y generalizable:
            razón social / empresa + RUC
            ...
            referencia / obra
            ...
            de nuestra consideración / nos dirigimos / cotización de nuestros

        La evidencia temprana se considera contexto de destinatario porque
        aparece antes de la transición explícita al discurso del emisor.
        """
        if not lines:
            return

        if any(
            self._RECIPIENT_HEADER.match(line)
            or self._RECIPIENT_INLINE.search(line)
            for line in lines[:16]
        ):
            return

        search_limit = min(
            len(lines),
            14,
        )

        issuer_transition_index = next(
            (
                index
                for index, line in enumerate(
                    lines[:search_limit]
                )
                if self._ISSUER_TRANSITION.search(
                    line
                )
            ),
            search_limit,
        )

        if issuer_transition_index <= 0:
            return

        for index in range(
            issuer_transition_index
        ):
            line = lines[index]

            # Debe existir una entidad legal en una ventana temprana.
            matches = list(
                self._LEGAL_SUFFIX.finditer(
                    line
                )
            )

            if not matches:
                continue

            ruc = self._find_nearby_identifier(
                lines=lines,
                start=max(0, index - 1),
                end=min(
                    issuer_transition_index,
                    index + 3,
                ),
            )

            if not ruc:
                continue

            for match in matches:
                candidate = line[
                    :match.end()
                ]

                candidate = re.sub(
                    r"(?i)^\s*(?:raz[oó]n\s+social|"
                    r"nombre|empresa)\s*[:\-]\s*",
                    "",
                    candidate,
                )

                candidate = self._clean_name(
                    candidate
                )

                if not self._looks_like_legal_entity(
                    candidate
                ):
                    continue

                self._add_candidate(
                    role="customer",
                    name=candidate,
                    region=None,
                    source="header_recipient_block",
                    score=28.0,
                    candidates=candidates,
                )

                resolved_key = (
                    "customer",
                    self._entity_key(
                        candidate
                    ),
                )

                candidate_state = candidates.get(
                    resolved_key
                )

                if candidate_state is not None:
                    candidate_state["identifier"] = ruc
                    candidate_state["score"] += 12.0
                    candidate_state["evidence"].append(
                        f"header_tax_id:{ruc}"
                    )

                    candidate_state["attributes"][
                        "source_line_index"
                    ] = index

                    candidate_state["attributes"][
                        "document_recipient_evidence"
                    ] = (
                        "entity_and_tax_id_before_"
                        "issuer_transition"
                    )

    @staticmethod
    def _find_nearby_identifier(
        *,
        lines: list[str],
        start: int,
        end: int,
    ) -> str:
        for index in range(
            max(0, start),
            min(len(lines), end),
        ):
            match = DocumentEntityResolver._RUC.search(
                lines[index]
            )

            if match:
                return match.group(
                    "value"
                )

        return ""

    @classmethod
    def _find_recipient_identifier(
        cls,
        *,
        lines: list[str],
        line_index: int,
        inline_match: re.Match[str] | None,
    ) -> str:
        """Obtiene el identificador posterior al marcador de destinatario."""
        if inline_match is not None:
            line = lines[line_index]
            matches = list(cls._RUC.finditer(line))
            for ruc_match in matches:
                if ruc_match.start() >= inline_match.start():
                    return ruc_match.group("value")

        for index in range(line_index + 1, min(len(lines), line_index + 4)):
            match = cls._RUC.search(lines[index])
            if match:
                return match.group("value")
        return ""

    @classmethod
    def _find_identifier_after_position(
        cls,
        *,
        lines: list[str],
        line_index: int,
        position: int,
    ) -> str:
        """Busca un RUC después de una etiqueta de identidad en la misma línea."""
        line = lines[line_index]
        match = cls._RUC.search(line, position)
        if match:
            return match.group("value")

        for index in range(line_index + 1, min(len(lines), line_index + 3)):
            match = cls._RUC.search(lines[index])
            if match:
                return match.group("value")
        return ""

    def _collect_text_candidates(
        self,
        *,
        lines: list[str],
        role_context: list[tuple[str, int, int]],
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        """
        Segunda pasada sobre el texto completo.

        Permite recuperar entidades que fueron fragmentadas por el layout.
        """
        for index, line in enumerate(lines):
            role = self._role_at(
                index,
                role_context,
            )

            role_match = self._ROLE_LABEL.match(
                line
            )

            if role_match:
                label = self._normalize(
                    role_match.group(
                        "label"
                    )
                )

                candidate_role = self._label_role(
                    label
                )

                if candidate_role == "unknown":
                    candidate_role = role

                value = self._clean_name(
                    role_match.group(
                        "value"
                    )
                )

                if candidate_role in {
                    "provider",
                    "customer",
                    "manufacturer",
                    "representative",
                }:
                    self._add_candidate(
                        role=candidate_role,
                        name=value,
                        region=None,
                        source="full_text_role_label",
                        score=30.0,
                        candidates=candidates,
                    )

            payee_match = self._PAYEE_LABEL.search(
                line
            )

            if payee_match:
                provider_name = self._clean_name(
                    payee_match.group(
                        "value"
                    )
                )

                self._add_candidate(
                    role="provider",
                    name=provider_name,
                    region=None,
                    source="full_text_payee",
                    score=40.0,
                    candidates=candidates,
                )

                provider_ruc = self._find_identifier_after_position(
                    lines=lines,
                    line_index=index,
                    position=payee_match.end(),
                )

                if provider_name and provider_ruc:
                    state = candidates.get(
                        (
                            "provider",
                            self._entity_key(
                                provider_name
                            ),
                        )
                    )

                    if state is not None:
                        state["identifier"] = provider_ruc
                        state["score"] += 10.0
                        state["evidence"].append(
                            f"payee_tax_id:{provider_ruc}"
                        )

            issuer_context = self._nearby_contains(
                lines,
                index,
                self._ISSUER_PHRASES,
                radius=4,
            )

            customer_context = self._nearby_contains(
                lines,
                index,
                self._CUSTOMER_PHRASES,
                radius=4,
            )

            effective_role = role

            if effective_role in {
                "ambiguous",
                "unknown",
            }:
                if (
                    customer_context
                    and not issuer_context
                ):
                    effective_role = "customer"
                elif (
                    issuer_context
                    and not customer_context
                ):
                    effective_role = "provider"

            if effective_role in {
                "provider",
                "customer",
                "manufacturer",
            }:
                candidate_name = (
                    self._extract_entity_from_line(
                        line
                    )
                )

                if candidate_name:
                    context_score = (
                        22.0
                        if issuer_context
                        else 14.0
                    )

                    self._add_candidate(
                        role=effective_role,
                        name=candidate_name,
                        region=None,
                        source="full_text_context",
                        score=context_score,
                        candidates=candidates,
                    )

            # Un RUC solo se vincula automáticamente cuando hay un único
            # candidato del rol. Con varios candidatos evitamos adivinar.
            ruc_match = self._RUC.search(
                line
            )

            if ruc_match:
                ruc = ruc_match.group(
                    "value"
                )

                ruc_role = (
                    role
                    if role
                    in {
                        "provider",
                        "customer",
                    }
                    else "unknown"
                )

                if ruc_role == "unknown":
                    if self._nearby_contains(
                        lines,
                        index,
                        self._ISSUER_PHRASES,
                        radius=3,
                    ):
                        ruc_role = "provider"

                if ruc_role in {
                    "provider",
                    "customer",
                }:
                    self._attach_identifier_by_role(
                        role=ruc_role,
                        identifier=ruc,
                        candidates=candidates,
                    )

    def _collect_visual_identity_candidates(
        self,
        *,
        knowledge: DocumentKnowledge,
        text_lines: list[str],
        candidates: dict[tuple[str, str], dict[str, Any]],
    ) -> None:
        """Vincula identidad comercial ubicada en OCR visual/encabezados."""
        commercial_context = self._normalize(" ".join(text_lines[:24]))
        commercial_terms = (
            "cotizacion", "cotización", "factura", "proforma", "oferta",
            "precio", "venta", "pedido", "orden de compra", "proveedor",
            "cliente", "productos", "servicios",
        )
        if not any(term in commercial_context for term in commercial_terms):
            return

        header_text = "\n".join(text_lines[:24])
        recipient_marker = self._RECIPIENT_INLINE.search(header_text)
        header_search_text = (
            header_text[:recipient_marker.start()]
            if recipient_marker
            else ""
        )
        ruc_matches = list(self._RUC.finditer(header_search_text))
        header_ruc = ruc_matches[-1].group("value") if ruc_matches else ""

        visual_candidates: list[tuple[str, str, float]] = []
        images = getattr(knowledge, "images", ()) or ()
        max_y = max(
            [
                float((image.get("bbox") or [0, 0, 0, 0])[3])
                for image in images
                if isinstance(image, dict) and image.get("bbox")
            ]
            or [0.0]
        )
        header_limit = max_y * 0.28 if max_y else 180.0

        for image in images:
            if not isinstance(image, dict):
                continue
            bbox = image.get("bbox") or ()
            if len(bbox) < 4:
                continue
            try:
                top_y = float(bbox[1])
            except (TypeError, ValueError):
                continue
            if top_y > header_limit:
                continue

            visual_text = str(image.get("ocr_text") or "").strip()
            if not visual_text:
                visual_data = image.get("visual_understanding") or {}
                visual_text = str(visual_data.get("detected_text") or "").strip()
            visual_name = self._extract_brand_like_name(visual_text)
            if visual_name:
                visual_candidates.append((visual_name, str(image.get("image_id", "")), 12.0))

        aggregated_visual = str(getattr(knowledge, "visual_text", "") or "").strip()
        aggregated_name = self._extract_brand_like_name(aggregated_visual)
        if aggregated_name:
            visual_candidates.append((aggregated_name, "visual_text", 9.0))

        for line in text_lines[:80]:
            bank_match = self._BANK_IDENTITY_HEADER.match(line)
            if not bank_match:
                continue
            bank_name = self._clean_name(bank_match.group("value"))
            if not self._looks_like_legal_entity(bank_name):
                continue
            self._add_candidate(
                role="provider",
                name=bank_name,
                region=None,
                source="bank_account_holder_identity",
                score=26.0,
                candidates=candidates,
                require_legal_entity=False,
            )

        for visual_name, source_id, visual_score in visual_candidates:
            self._add_candidate(
                role="provider",
                name=visual_name,
                region=None,
                source=f"visual_header:{source_id}",
                score=18.0 + visual_score,
                candidates=candidates,
                require_legal_entity=False,
            )

        for email in self._extract_emails("\n".join(text_lines)):
            email_name = self._name_from_business_email(email)
            if not email_name:
                continue

            best_name = email_name
            source = "business_email_identity"
            score = 14.0

            for visual_name, source_id, visual_score in visual_candidates:
                if self._identity_tokens_overlap(email_name, visual_name):
                    best_name = self._merge_identity_names(email_name, visual_name)
                    source = f"visual_header:{source_id}"
                    score += visual_score + 8.0
                    break

            self._add_candidate(
                role="provider",
                name=best_name,
                region=None,
                source=source,
                score=score,
                candidates=candidates,
                require_legal_entity=False,
            )

            state = candidates.get(("provider", self._entity_key(best_name)))
            if state is None:
                continue

            if header_ruc:
                state["identifier"] = header_ruc
                state["score"] += 14.0
                state["evidence"].append(f"header_first_ruc:{header_ruc}")
                state["attributes"]["identity_cross_source"] = (
                    "business_email_plus_visual_header_plus_header_ruc"
                )

            if visual_candidates:
                state["score"] += 4.0
                state["evidence"].append("visual_header_identity_support")

        for provider_candidate in list(candidates.values()):
            if provider_candidate.get("role") != "provider":
                continue
            candidate_name = str(provider_candidate.get("name") or "").strip()
            if not candidate_name:
                continue
            if header_ruc:
                provider_candidate["identifier"] = header_ruc
                provider_candidate["score"] += 14.0
                provider_candidate["evidence"].append(f"header_first_ruc:{header_ruc}")
                provider_candidate["attributes"]["identity_cross_source"] = (
                    "header_ruc_plus_visual_or_bank_identity"
                )
            if visual_candidates:
                provider_candidate["score"] += 4.0
                provider_candidate["evidence"].append("visual_header_identity_support")

    @staticmethod
    def _extract_emails(text: str) -> tuple[str, ...]:
        matches = re.findall(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text or "",
            flags=re.IGNORECASE,
        )
        return tuple(dict.fromkeys(matches))

    @staticmethod
    def _name_from_business_email(email: str) -> str:
        local = email.split("@", 1)[0].casefold()
        local = re.sub(r"[0-9]+$", "", local)
        local = re.sub(r"[._-]+", " ", local).strip()
        if not local:
            return ""

        prefixes = (
            "corporacion", "corporación", "empresa", "grupo",
            "comercial", "industrial", "inversiones", "constructora",
            "servicios", "sociedad", "distribuciones", "importaciones",
            "exportaciones", "ferreteria", "ferretería", "multiservicios",
            "proyectos", "transportes", "logistica", "logística",
        )
        for prefix in prefixes:
            if local.startswith(prefix) and len(local) > len(prefix) + 2:
                remainder = local[len(prefix):].strip(" _-.")
                if remainder:
                    return f"{prefix} {remainder}".strip().upper()

        parts = local.split()
        if len(parts) >= 2:
            return " ".join(parts).upper()
        return ""

    @staticmethod
    def _extract_brand_like_name(text: str) -> str:
        cleaned = " ".join(str(text or "").split())
        if not cleaned:
            return ""

        legal_match = re.search(
            r"(?i)(?P<body>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.-]+(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.-]+){0,7})"
            r"\s+(?P<legal>S\.?A\.?C?\.?|S\.?R\.?L\.?|E\.?I\.?R\.?L\.?)\b",
            cleaned,
        )
        if legal_match:
            body_tokens = re.findall(
                r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9&.-]{3,}",
                legal_match.group("body"),
            )
            ignored = {
                "ruc", "cotizacion", "cotización", "fecha", "empresa",
                "cliente", "proveedor", "productos", "servicios",
                "aa", "aro", "www",
            }
            filtered = [
                token for token in body_tokens
                if token.casefold() not in ignored
            ]
            if filtered:
                business_prefixes = {
                    "grupo", "corporacion", "corporación", "industrial",
                    "comercial", "inversiones", "constructora",
                }
                prefix = [t for t in filtered if t.casefold() in business_prefixes]
                corporate = [t for t in filtered if t.casefold() == "corporativo"]
                middle = [
                    t for t in filtered
                    if t.casefold() not in business_prefixes
                    and t.casefold() != "corporativo"
                ]
                ordered = prefix + corporate + middle
                return " ".join(ordered[:5] + [legal_match.group("legal")]).upper()

        tokens = re.findall(
            r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,}",
            cleaned,
        )
        ignored = {
            "ruc", "cotizacion", "cotización", "fecha", "empresa",
            "cliente", "proveedor", "productos", "servicios",
            "ladrillos", "cemento", "tuberias", "tuberías", "aa",
            "aro", "y", "o", "vo", "ae", "na", "f",
        }
        useful = [token for token in tokens if token.casefold() not in ignored]
        if not useful:
            return ""

        business_tokens = {
            "corporacion", "corporación", "grupo", "empresa", "industrial",
            "comercial", "inversiones", "constructora", "servicios",
            "corporativo",
        }
        prefix = [t for t in useful if t.casefold() in business_tokens]
        distinct = [t for t in useful if t.casefold() not in business_tokens]
        ordered = prefix[:2] + distinct[:3]
        return " ".join(ordered).upper() if ordered else ""

    @staticmethod
    def _identity_tokens_overlap(left: str, right: str) -> bool:
        a = {token for token in re.split(r"\W+", left.casefold()) if len(token) >= 3}
        b = {token for token in re.split(r"\W+", right.casefold()) if len(token) >= 3}
        if a.intersection(b):
            return True
        for token_a in a:
            for token_b in b:
                if len(token_a) >= 4 and len(token_b) >= 4:
                    if token_a.startswith(token_b) or token_b.startswith(token_a):
                        return True
        return False

    @staticmethod
    def _merge_identity_names(left: str, right: str) -> str:
        left_tokens = left.strip().upper().split()
        right_tokens = right.strip().upper().split()
        if not left_tokens:
            return right.strip().upper()
        if not right_tokens:
            return left.strip().upper()

        corporate_prefixes = {
            "CORPORACION", "CORPORACIÓN", "EMPRESA", "GRUPO",
            "COMERCIAL", "INDUSTRIAL", "INVERSIONES", "CONSTRUCTORA",
            "SERVICIOS", "SOCIEDAD", "DISTRIBUCIONES", "IMPORTACIONES",
            "EXPORTACIONES", "FERRETERIA", "FERRETERÍA", "MULTISERVICIOS",
            "PROYECTOS", "TRANSPORTES", "LOGISTICA", "LOGÍSTICA",
        }
        if left_tokens[0] in corporate_prefixes:
            right_core = next(
                (token for token in right_tokens if token not in corporate_prefixes),
                right_tokens[-1],
            )
            for left_core in left_tokens[1:]:
                if (
                    len(left_core) >= 4
                    and len(right_core) >= 4
                    and (left_core.startswith(right_core) or right_core.startswith(left_core))
                ):
                    return f"{left_tokens[0]} {right_core}"
            return f"{left_tokens[0]} {right_core}"

        if len(right_tokens) >= len(left_tokens):
            return right.strip().upper()
        return left.strip().upper()

    def _metadata_role(
        self,
        region: Any,
    ) -> str:
        section = self._normalize(
            str(
                region.metadata.get(
                    "document_section",
                    "",
                )
            )
        )

        return {
            "provider_identity": "provider",
            "customer_identity": "customer",
        }.get(
            section,
            section
            if section
            in {
                "provider",
                "customer",
                "manufacturer",
            }
            else "unknown",
        )

    def _infer_role_from_content(
        self,
        content: str,
    ) -> str:
        normalized = self._normalize(
            content
        )

        provider_hits = sum(
            self._normalize(marker)
            in normalized
            for marker in self._ISSUER_PHRASES
        )

        customer_hits = sum(
            self._normalize(marker)
            in normalized
            for marker in self._CUSTOMER_PHRASES
        )

        if provider_hits > customer_hits:
            return "provider"

        if customer_hits > provider_hits:
            return "customer"

        return "unknown"

    def _attach_identifier_to_region(
        self,
        *,
        role: str,
        identifier: str,
        region: Any,
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        if role not in {
            "provider",
            "customer",
            "manufacturer",
        }:
            return

        names: list[str] = []

        for line in (
            region.content or ""
        ).splitlines():
            candidate = (
                self._extract_entity_from_line(
                    line
                )
            )

            if candidate:
                names.append(
                    candidate
                )

        for name in dict.fromkeys(
            names
        ):
            self._add_candidate(
                role=role,
                name=name,
                region=region,
                source="regional_tax_id",
                score=10.0,
                candidates=candidates,
            )

            candidate = candidates.get(
                (
                    role,
                    self._entity_key(name),
                )
            )

            if candidate is not None:
                candidate["identifier"] = (
                    identifier
                )
                candidate["score"] += 10.0
                candidate["evidence"].append(
                    f"tax_id:{identifier}"
                )

    def _attach_identifier_by_role(
        self,
        *,
        role: str,
        identifier: str,
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> None:
        role_candidates = [
            candidate
            for candidate in candidates.values()
            if candidate["role"] == role
            and candidate["name"]
        ]

        if len(role_candidates) == 1:
            candidate = role_candidates[0]

            candidate["identifier"] = (
                identifier
            )
            candidate["score"] += 9.0
            candidate["evidence"].append(
                f"text_tax_id:{identifier}"
            )

    def _add_candidate(
        self,
        *,
        role: str,
        name: str,
        region: Any | None,
        source: str,
        score: float,
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
        require_legal_entity: bool = True,
    ) -> None:
        allowed_roles = {
            "provider",
            "customer",
            "manufacturer",
            "representative",
        }

        if role not in allowed_roles:
            return

        cleaned = self._clean_name(
            name
        )

        if (
            require_legal_entity
            and role in {
                "provider",
                "customer",
                "manufacturer",
            }
            and not self._looks_like_legal_entity(cleaned)
        ):
            return

        if not cleaned:
            return

        key = (
            role,
            self._entity_key(cleaned),
        )

        candidate = candidates.setdefault(
            key,
            {
                "role": role,
                "name": cleaned,
                "identifier": "",
                "score": 0.0,
                "evidence_ids": [],
                "evidence": [],
                "attributes": {},
            },
        )

        candidate["score"] += score
        candidate["evidence"].append(
            source
        )

        if region is not None:
            evidence_id = str(
                region.metadata.get(
                    "evidence_id",
                    f"evidence-{region.region_id}",
                )
            )

            if (
                evidence_id
                not in candidate[
                    "evidence_ids"
                ]
            ):
                candidate[
                    "evidence_ids"
                ].append(
                    evidence_id
                )

            candidate[
                "attributes"
            ].setdefault(
                "source_page_number",
                region.page_number,
            )

    @staticmethod
    def _nearby_contains(
        lines: list[str],
        index: int,
        phrases: Iterable[str],
        *,
        radius: int,
    ) -> bool:
        start = max(
            0,
            index - radius,
        )

        end = min(
            len(lines),
            index + radius + 1,
        )

        context = " ".join(
            lines[start:end]
        ).casefold()

        return any(
            str(phrase).casefold()
            in context
            for phrase in phrases
        )

    @classmethod
    def _select_resolved_candidates(
        cls,
        ranked: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Publica como resuelto solo el candidato dominante por rol.

        Esta separación impide que dos posibles proveedores terminen
        apareciendo simultáneamente como proveedor definitivo.
        """
        selected: list[dict[str, Any]] = []

        by_role: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for candidate in ranked:
            by_role.setdefault(
                candidate["role"],
                [],
            ).append(
                candidate
            )

        for role, role_candidates in by_role.items():
            if not role_candidates:
                continue

            best = role_candidates[0]

            if not cls._resolved(
                best
            ):
                continue

            if len(role_candidates) == 1:
                selected.append(
                    best
                )
                continue

            second = role_candidates[1]

            margin = (
                best["score"]
                - second["score"]
            )

            required_margin = (
                5.0
                if role in {
                    "provider",
                    "customer",
                    "manufacturer",
                }
                else 3.0
            )

            if margin >= required_margin:
                selected.append(
                    best
                )

        return selected

    @classmethod
    def _remove_cross_role_duplicates(
        cls,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Evita publicar la misma identidad con roles incompatibles.

        Cuando dos candidatos comparten RUC, o comparten nombre normalizado
        si no existe RUC, se consideran la misma identidad documental y solo
        se conserva el rol mejor respaldado.
        """
        grouped: dict[str, list[dict[str, Any]]] = {}

        for candidate in candidates:
            identifier = str(
                candidate.get(
                    "identifier",
                    "",
                )
            ).strip()

            identity_key = (
                f"id:{identifier}"
                if identifier
                else (
                    "name:"
                    + cls._entity_key(
                        candidate.get(
                            "name",
                            "",
                        )
                    )
                )
            )

            grouped.setdefault(
                identity_key,
                [],
            ).append(
                candidate
            )

        selected: list[dict[str, Any]] = []

        for group in grouped.values():
            ranked_group = sorted(
                group,
                key=lambda candidate: (
                    candidate.get(
                        "score",
                        0.0,
                    ),
                    cls._explicit_role_evidence_strength(
                        candidate
                    ),
                    len(
                        candidate.get(
                            "evidence",
                            (),
                        )
                    ),
                ),
                reverse=True,
            )

            selected.append(
                ranked_group[0]
            )

        return selected

    @staticmethod
    def _explicit_role_evidence_strength(
        candidate: dict[str, Any],
    ) -> float:
        role = candidate.get(
            "role",
            "",
        )

        evidence = set(
            candidate.get(
                "evidence",
                (),
            )
        )

        score = 0.0

        if "explicit_role_label" in evidence:
            score += 20.0

        if (
            role == "provider"
            and (
                "explicit_payee" in evidence
                or "full_text_payee" in evidence
            )
        ):
            score += 30.0

        if (
            role == "customer"
            and "header_recipient_block" in evidence
        ):
            score += 30.0

        return score

    @staticmethod
    def _label_role(
        label: str,
    ) -> str:
        return {
            "proveedor": "provider",
            "emisor": "provider",
            "vendedor": "provider",
            "cliente": "customer",
            "comprador": "customer",
            "destinatario": "recipient",
            "fabricante": "manufacturer",
            "representante": "representative",
            "razon social": "unknown",
        }.get(
            label,
            "unknown",
        )

    @classmethod
    def _rank(
        cls,
        candidates: dict[
            tuple[str, str],
            dict[str, Any],
        ],
    ) -> list[dict[str, Any]]:
        return sorted(
            candidates.values(),
            key=lambda candidate: (
                candidate["score"],
                bool(
                    candidate["identifier"]
                ),
                len(
                    candidate["evidence_ids"]
                ),
            ),
            reverse=True,
        )

    @classmethod
    def _resolved(
        cls,
        candidate: dict[str, Any],
    ) -> bool:
        threshold = {
            "provider": 20.0,
            "customer": 20.0,
            "manufacturer": 20.0,
            "representative": 18.0,
        }.get(
            candidate["role"],
            20.0,
        )

        return bool(
            candidate["name"]
            and candidate["score"] >= threshold
        )

    @classmethod
    def _to_entity(
        cls,
        candidate: dict[str, Any],
        *,
        document_id: str,
    ) -> DocumentEntity:
        raw_key = (
            f"{document_id}|"
            f"{candidate['role']}|"
            f"{candidate['identifier']}|"
            f"{candidate['name']}"
        )

        entity_id = (
            "entity-"
            + sha256(
                raw_key.encode(
                    "utf-8"
                )
            ).hexdigest()[:24]
        )

        confidence = min(
            1.0,
            round(
                candidate["score"]
                / 55.0,
                4,
            ),
        )

        attributes = dict(
            candidate["attributes"]
        )

        attributes.update(
            {
                "document_id": document_id,
                "resolution_method": (
                    "deterministic_evidence"
                ),
                "resolution_evidence": list(
                    dict.fromkeys(
                        candidate["evidence"]
                    )
                ),
            }
        )

        return DocumentEntity(
            entity_id=entity_id,
            entity_type="organization",
            role=candidate["role"],
            name=candidate["name"],
            identifier=candidate["identifier"],
            confidence=confidence,
            evidence_ids=tuple(
                candidate["evidence_ids"]
            ),
            attributes=attributes,
        )

    @staticmethod
    def _build_relationships(
        *,
        document_id: str,
        entities: Iterable[
            DocumentEntity
        ],
    ) -> list[
        DocumentRelationship
    ]:
        relationships: list[
            DocumentRelationship
        ] = []

        for entity in entities:
            raw_key = (
                f"{document_id}|"
                f"{entity.entity_id}|"
                f"{entity.role}"
            )

            relationship_id = (
                "relationship-"
                + sha256(
                    raw_key.encode(
                        "utf-8"
                    )
                ).hexdigest()[:24]
            )

            relationships.append(
                DocumentRelationship(
                    relationship_id=relationship_id,
                    source_id=document_id,
                    relationship_type=(
                        f"has_{entity.role}"
                    ),
                    target_id=entity.entity_id,
                    confidence=entity.confidence,
                    evidence_ids=entity.evidence_ids,
                    metadata={
                        "resolution_method": (
                            "deterministic_evidence"
                        ),
                    },
                )
            )

        return relationships

    @classmethod
    def _candidate_dict(
        cls,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "role": candidate["role"],
            "name": candidate["name"],
            "identifier": candidate["identifier"],
            "score": round(
                candidate["score"],
                4,
            ),
            "resolved": cls._resolved(
                candidate
            ),
            "evidence_ids": list(
                candidate["evidence_ids"]
            ),
            "evidence": list(
                dict.fromkeys(
                    candidate["evidence"]
                )
            ),
            "attributes": dict(
                candidate["attributes"]
            ),
        }

    @staticmethod
    def _clean_name(
        value: str,
    ) -> str:
        cleaned = " ".join(
            str(value)
            .strip(
                " \t\r\n:;,"
            )
            .split()
        )

        rejected = {
            "",
            "nuestros productos",
            "nuestros servicios",
            "nuestra empresa",
            "productos",
            "servicios",
            "cliente",
            "proveedor",
            "emisor",
            "comprador",
            "vendedor",
        }

        if cleaned.casefold() in rejected:
            return ""

        return cleaned

    @classmethod
    def _looks_like_legal_entity(
        cls,
        value: str,
    ) -> bool:
        return bool(
            cls._LEGAL_SUFFIX.search(
                value
            )
        )

    @staticmethod
    def _entity_key(
        value: str,
    ) -> str:
        return re.sub(
            r"[^a-z0-9]",
            "",
            value.casefold(),
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        return " ".join(
            str(value)
            .casefold()
            .split()
        )

    @staticmethod
    def _extract_entity_from_line(
        line: str,
    ) -> str:
        """
        Extrae una entidad jurídica de una línea cuando el contexto ya indica
        que la línea puede contener una organización.

        Se limita a la parte que termina en una forma jurídica reconocible,
        evitando capturar teléfonos, cuentas o frases posteriores.
        """
        cleaned = " ".join(
            line.strip().split()
        )

        if not cleaned:
            return ""

        lowered = cleaned.casefold()

        if any(
            lowered.startswith(prefix)
            for prefix in (
                "cta cte",
                "cuenta",
                "banco de credito",
                "banco de crédito",
            )
        ):
            return ""

        match = (
            DocumentEntityResolver
            ._LEGAL_SUFFIX
            .search(cleaned)
        )

        if not match:
            return ""

        candidate = cleaned[
            : match.end()
        ].strip(
            " \t\r\n:;,"
        )

        remainder = cleaned[
            match.end():
        ].lstrip()

        # Conservamos un alias legal inmediatamente posterior:
        # S.A. (ITICSA)
        if remainder.startswith("("):
            closing = remainder.find(
                ")"
            )

            if closing >= 0:
                candidate = (
                    f"{candidate} "
                    f"{remainder[:closing + 1]}"
                )

        return candidate