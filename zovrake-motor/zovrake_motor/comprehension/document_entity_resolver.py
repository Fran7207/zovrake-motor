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

    MODEL_VERSION = "1.1-deterministic-evidence-entity"

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
        r"(?i)\bR\.?\s*U\.?\s*C\.?\s*[:\-]?\s*"
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

    _PAYEE_LABEL = re.compile(
        r"(?i)\b(?:depositar|dep[oó]sito)\s+a\s+nombre\s*[:\-]\s*"
        r"(?P<value>.+?)\s*$"
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
        self._collect_text_candidates(
            lines=lines,
            role_context=role_context,
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
                self._add_candidate(
                    role="provider",
                    name=self._clean_name(
                        payee_match.group(
                            "value"
                        )
                    ),
                    region=region,
                    source="explicit_payee",
                    score=32.0,
                    candidates=candidates,
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
                self._add_candidate(
                    role="provider",
                    name=self._clean_name(
                        payee_match.group(
                            "value"
                        )
                    ),
                    region=None,
                    source="full_text_payee",
                    score=34.0,
                    candidates=candidates,
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

        if role in {
            "provider",
            "customer",
            "manufacturer",
        } and not self._looks_like_legal_entity(
            cleaned
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
                " \t\r\n:;,.()"
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