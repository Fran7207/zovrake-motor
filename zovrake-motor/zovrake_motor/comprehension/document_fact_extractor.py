"""Extracción determinista de hechos y atributos desde DocumentKnowledge."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import re
from typing import Any, Iterable

from zovrake_motor.comprehension.models import (
    DocumentKnowledge,
)


class DocumentFactExtractor:
    """
    Extrae hechos observables desde DocumentKnowledge sin reducir el contenido.

    La extracción es deliberadamente conservadora. Una coincidencia textual
    no se convierte automáticamente en un hecho fuerte: cada hecho conserva
    su origen, región, página, evidencia y confianza.

    Soporta:
    - pares etiqueta: valor;
    - campos key=value procedentes de tablas;
    - identificadores;
    - importes monetarios;
    - porcentajes;
    - fechas;
    - correos;
    - URLs;
    - mediciones con unidad.

    No depende de un tipo de documento concreto.
    """

    MODEL_VERSION = "1.1-deterministic-fact-extraction"

    _LABEL_VALUE = re.compile(
        r"^\s*(?P<label>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]"
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _./()]{1,79}?)"
        r"\s*[:\-]\s*(?P<value>.+?)\s*$"
    )

    _KEY_VALUE = re.compile(
        r"(?P<label>[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _./()]{0,79}?)"
        r"\s*=\s*(?P<value>[^|]+)"
    )

    _MONEY = re.compile(
        r"(?P<prefix>US\$|U\$S|S\/\.?|€|£|¥|\$)?\s*"
        r"(?P<value>"
        r"(?:\d{1,3}(?:[.,]\d{3})+|\d+)"
        r"(?:[.,]\d+)?"
        r")\s*"
        r"(?P<currency>PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|"
        r"CAD|AUD|CHF|JPY|CNY|INR)?",
        re.IGNORECASE,
    )

    _PERCENT = re.compile(
        r"(?P<value>\d+(?:[.,]\d+)?)\s*%"
    )

    _DATE = re.compile(
        r"\b(?:"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|"
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}"
        r"|"
        r"\d{1,2}\s+de\s+"
        r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|"
        r"septiembre|octubre|noviembre|diciembre)"
        r"(?:\s+de\s+\d{4})?"
        r")\b",
        re.IGNORECASE,
    )

    _EMAIL = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    _URL = re.compile(
        r"\b(?:https?://|www\.)[^\s<>\"]+",
        re.IGNORECASE,
    )

    _IDENTIFIER = re.compile(
        r"(?P<label>\b(?:RUC|R\.U\.C\.|DNI|NIT|CUIT|"
        r"RIF|RFC|ID|CÓDIGO|CODIGO|SERIE|SKU)\b)"
        r"\s*[:#\-]?\s*(?P<value>[A-Z0-9][A-Z0-9./_-]{2,})",
        re.IGNORECASE,
    )

    _UNIT_VALUE = re.compile(
        r"(?P<value>"
        r"[-+]?\d+(?:[.,]\d+)?"
        r")\s*"
        r"(?P<unit>"
        r"%|kg|g|mg|t|m|cm|mm|km|"
        r"m2|m²|m3|m³|l|ml|"
        r"v|kv|w|kw|hz|"
        r"a|ma|°c|c|"
        r"und|unidad|unidades|"
        r"hrs?|horas?|dias?|días?|meses?|años?"
        r")\b",
        re.IGNORECASE,
    )

    _LABEL_ALIASES = {
        "razon social": "legal_name",
        "razón social": "legal_name",
        "nombre": "name",
        "descripcion": "description",
        "descripción": "description",
        "cantidad": "quantity",
        "unidad": "unit",
        "precio": "price",
        "precio unitario": "unit_price",
        "importe": "amount",
        "total": "total",
        "subtotal": "subtotal",
        "descuento": "discount",
        "igv": "tax",
        "iva": "tax",
        "garantia": "warranty",
        "garantía": "warranty",
        "vigencia": "validity",
        "validez": "validity",
        "plazo de entrega": "delivery_time",
        "forma de pago": "payment_method",
        "condiciones de pago": "payment_terms",
        "marca": "brand",
        "modelo": "model",
        "material": "material",
        "correo": "email",
        "email": "email",
        "telefono": "phone",
        "teléfono": "phone",
        "direccion": "address",
        "dirección": "address",
        "banco": "bank",
        "cuenta": "account",
        "cci": "bank_account_cci",
        "swift": "bank_account_swift",
        "iban": "bank_account_iban",
        "codigo": "code",
        "código": "code",
        "sku": "sku",
        "serie": "serial_number",
        "ruc": "tax_id",
        "dni": "identity_document",
    }

    _WEAK_LABELS = {
        "sub",
        "sub.",
        "fo",
        "son",
        "n",
        "no",
        "item",
        "ítem",
    }

    _NON_VALUE_TOKENS = {
        "",
        "-",
        "—",
        ":",
        "|",
    }

    def extract(
        self,
        knowledge: DocumentKnowledge,
    ) -> DocumentKnowledge:
        """Extrae hechos/atributos y devuelve una nueva representación."""
        if not isinstance(
            knowledge,
            DocumentKnowledge,
        ):
            raise TypeError(
                "knowledge debe ser una instancia de DocumentKnowledge"
            )

        facts: list[dict[str, Any]] = []
        attributes: list[dict[str, Any]] = []

        for region in knowledge.regions:
            region_facts = self._extract_from_region(
                region
            )

            facts.extend(region_facts)

            for fact in region_facts:
                if fact["fact_type"] in {
                    "labeled_value",
                    "table_field",
                }:
                    attributes.append(
                        {
                            "attribute_id": fact["fact_id"],
                            "name": fact["normalized_label"],
                            "raw_label": fact["label"],
                            "value": fact["raw_value"],
                            "normalized_value": fact[
                                "normalized_value"
                            ],
                            "page_number": fact["page_number"],
                            "region_id": fact["region_id"],
                            "evidence_id": fact["evidence_id"],
                            "confidence": fact["confidence"],
                        }
                    )

        facts = self._deduplicate(
            facts
        )
        attributes = self._deduplicate(
            attributes
        )

        unresolved = list(
            knowledge.unresolved
        )

        if not facts:
            unresolved.append(
                {
                    "type": "fact_extraction_empty",
                    "message": (
                        "No se encontraron hechos estructurables "
                        "con suficiente evidencia en las regiones procesadas."
                    ),
                }
            )

        metadata = dict(
            knowledge.metadata
        )

        metadata.update(
            {
                "fact_extraction_model_version": self.MODEL_VERSION,
                "fact_extraction_stage": (
                    "observable_fact_detection"
                ),
                "fact_count": len(facts),
                "attribute_count": len(attributes),
            }
        )

        return replace(
            knowledge,
            facts=tuple(facts),
            attributes=tuple(attributes),
            unresolved=tuple(unresolved),
            metadata=metadata,
        )

    def _extract_from_region(
        self,
        region: Any,
    ) -> list[dict[str, Any]]:
        content = region.content or ""

        if not content.strip():
            return []

        results: list[dict[str, Any]] = []

        for line_index, line in enumerate(
            content.splitlines(),
            start=1,
        ):
            clean_line = line.strip()

            if not clean_line:
                continue

            # -----------------------------------------------------
            # 1. Campos key=value típicos de tablas semánticas.
            # -----------------------------------------------------
            for match in self._KEY_VALUE.finditer(
                clean_line
            ):
                label = self._clean_text(
                    match.group("label")
                )
                raw_value = self._clean_text(
                    match.group("value")
                )

                if not self._is_valid_labeled_pair(
                    label,
                    raw_value,
                    table_field=True,
                ):
                    continue

                results.append(
                    self._fact(
                        region=region,
                        fact_type="table_field",
                        raw_value=raw_value,
                        label=label,
                        line_index=line_index,
                        confidence=self._table_field_confidence(
                            label,
                            raw_value,
                        ),
                    )
                )

            # -----------------------------------------------------
            # 2. Pares normales etiqueta: valor.
            #
            # No intentamos interpretar líneas que son claramente
            # representaciones serializadas de una tabla.
            # -----------------------------------------------------
            if "=" not in clean_line and "|" not in clean_line:
                labeled_match = self._LABEL_VALUE.match(
                    clean_line
                )

                if labeled_match:
                    label = self._clean_text(
                        labeled_match.group(
                            "label"
                        )
                    )
                    raw_value = self._clean_text(
                        labeled_match.group(
                            "value"
                        )
                    )

                    if self._is_valid_labeled_pair(
                        label,
                        raw_value,
                        table_field=False,
                    ):
                        results.append(
                            self._fact(
                                region=region,
                                fact_type="labeled_value",
                                raw_value=raw_value,
                                label=label,
                                line_index=line_index,
                                confidence=self._label_confidence(
                                    label,
                                    raw_value,
                                ),
                            )
                        )

            # -----------------------------------------------------
            # 3. Identificadores.
            # -----------------------------------------------------
            for match in self._IDENTIFIER.finditer(
                clean_line
            ):
                label = self._clean_text(
                    match.group(
                        "label"
                    )
                )

                raw_value = self._clean_text(
                    match.group(
                        "value"
                    )
                )

                results.append(
                    self._fact(
                        region=region,
                        fact_type="identifier",
                        raw_value=raw_value,
                        label=label,
                        line_index=line_index,
                        confidence=0.96,
                    )
                )

            # -----------------------------------------------------
            # 4. Moneda/importes.
            # -----------------------------------------------------
            for match in self._MONEY.finditer(
                clean_line
            ):
                value = match.group(
                    "value"
                )

                prefix = (
                    match.group(
                        "prefix"
                    )
                    or ""
                ).strip()

                currency = (
                    match.group(
                        "currency"
                    )
                    or ""
                ).upper()

                if not currency and prefix:
                    currency = self._symbol_currency(
                        prefix
                    )

                if not currency:
                    continue

                normalized_number = (
                    self._normalize_number(
                        value
                    )
                )

                if normalized_number is None:
                    continue

                results.append(
                    self._fact(
                        region=region,
                        fact_type="monetary_value",
                        raw_value=match.group(0).strip(),
                        label="monetary_value",
                        line_index=line_index,
                        confidence=0.92,
                        normalized_value={
                            "value": normalized_number,
                            "currency": currency,
                        },
                    )
                )

            # -----------------------------------------------------
            # 5. Porcentajes.
            # -----------------------------------------------------
            for match in self._PERCENT.finditer(
                clean_line
            ):
                normalized = self._normalize_number(
                    match.group(
                        "value"
                    )
                )

                if normalized is None:
                    continue

                results.append(
                    self._fact(
                        region=region,
                        fact_type="percentage",
                        raw_value=match.group(0),
                        label="percentage",
                        line_index=line_index,
                        confidence=0.96,
                        normalized_value=normalized,
                    )
                )

            # -----------------------------------------------------
            # 6. Fechas.
            # -----------------------------------------------------
            for match in self._DATE.finditer(
                clean_line
            ):
                results.append(
                    self._fact(
                        region=region,
                        fact_type="date",
                        raw_value=match.group(0),
                        label="date",
                        line_index=line_index,
                        confidence=0.92,
                    )
                )

            # -----------------------------------------------------
            # 7. Correos.
            # -----------------------------------------------------
            for match in self._EMAIL.finditer(
                clean_line
            ):
                results.append(
                    self._fact(
                        region=region,
                        fact_type="email",
                        raw_value=match.group(0),
                        label="email",
                        line_index=line_index,
                        confidence=0.98,
                    )
                )

            # -----------------------------------------------------
            # 8. URLs.
            # -----------------------------------------------------
            for match in self._URL.finditer(
                clean_line
            ):
                results.append(
                    self._fact(
                        region=region,
                        fact_type="url",
                        raw_value=match.group(0),
                        label="url",
                        line_index=line_index,
                        confidence=0.98,
                    )
                )

            # -----------------------------------------------------
            # 9. Mediciones.
            # -----------------------------------------------------
            for match in self._UNIT_VALUE.finditer(
                clean_line
            ):
                value = self._normalize_number(
                    match.group(
                        "value"
                    )
                )

                if value is None:
                    continue

                unit = self._clean_text(
                    match.group(
                        "unit"
                    )
                ).lower()

                results.append(
                    self._fact(
                        region=region,
                        fact_type="measurement",
                        raw_value=match.group(0),
                        label="measurement",
                        line_index=line_index,
                        confidence=0.86,
                        normalized_value={
                            "value": value,
                            "unit": unit,
                        },
                    )
                )

        return results

    def _is_valid_labeled_pair(
        self,
        label: str,
        value: str,
        *,
        table_field: bool,
    ) -> bool:
        label = label.strip()
        value = value.strip()

        if (
            not label
            or not value
            or label.casefold()
            in self._NON_VALUE_TOKENS
            or value.casefold()
            in self._NON_VALUE_TOKENS
        ):
            return False

        normalized_label = self._normalize_label(
            label
        )

        if (
            normalized_label
            in self._WEAK_LABELS
        ):
            return False

        # En una tabla, la etiqueta debe parecer un nombre de campo.
        # Esto evita convertir "191: 0452510..." o fragmentos de layout
        # en atributos documentales arbitrarios.
        if table_field:
            if not (
                normalized_label
                in self._LABEL_ALIASES
                or len(normalized_label) >= 3
            ):
                return False

            if any(
                token in normalized_label
                for token in (
                    "=",
                    "|",
                )
            ):
                return False

        # Las etiquetas extremadamente numéricas suelen ser residuos
        # de una reconstrucción de layout, no campos semánticos.
        if (
            sum(
                char.isdigit()
                for char in label
            )
            > sum(
                char.isalpha()
                for char in label
            )
        ):
            return False

        return len(label) <= 100

    @classmethod
    def _table_field_confidence(
        cls,
        label: str,
        value: str,
    ) -> float:
        normalized = cls._normalize_label(
            label
        )

        if normalized in cls._LABEL_ALIASES:
            return 0.96

        if len(value) >= 2:
            return 0.84

        return 0.62

    @classmethod
    def _label_confidence(
        cls,
        label: str,
        value: str,
    ) -> float:
        normalized = cls._normalize_label(
            label
        )

        if normalized in cls._LABEL_ALIASES:
            return 0.96

        if len(label) >= 4 and len(value) >= 2:
            return 0.82

        return 0.64

    def _fact(
        self,
        *,
        region: Any,
        fact_type: str,
        raw_value: str,
        label: str,
        line_index: int,
        confidence: float,
        normalized_value: Any = None,
    ) -> dict[str, Any]:
        normalized_label = self._normalize_label(
            label
        )

        fact_key = "|".join(
            (
                region.region_id,
                str(region.page_number),
                str(line_index),
                fact_type,
                normalized_label,
                raw_value,
            )
        )

        fact_id = (
            "fact-"
            + sha256(
                fact_key.encode("utf-8")
            ).hexdigest()[:24]
        )

        return {
            "fact_id": fact_id,
            "fact_type": fact_type,
            "label": label,
            "normalized_label": (
                self._LABEL_ALIASES.get(
                    normalized_label,
                    normalized_label.replace(
                        " ",
                        "_",
                    ),
                )
            ),
            "raw_value": raw_value,
            "normalized_value": (
                normalized_value
                if normalized_value is not None
                else self._normalize_text_value(
                    raw_value
                )
            ),
            "page_number": region.page_number,
            "region_id": region.region_id,
            "evidence_id": region.metadata.get(
                "evidence_id",
                f"evidence-{region.region_id}",
            ),
            "source_kind": region.source_kind,
            "confidence": round(
                max(
                    0.0,
                    min(
                        1.0,
                        confidence,
                    ),
                ),
                4,
            ),
            "line_index": line_index,
            "semantic_context": region.metadata.get(
                "document_section",
                "unknown",
            ),
        }

    @staticmethod
    def _normalize_label(
        value: str,
    ) -> str:
        return " ".join(
            value.casefold().split()
        )

    @staticmethod
    def _clean_text(
        value: str,
    ) -> str:
        return " ".join(
            str(value).strip().split()
        )

    @staticmethod
    def _normalize_number(
        value: str,
    ) -> float | None:
        cleaned = re.sub(
            r"[^\d,.\-+]",
            "",
            value,
        )

        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(
                    ".",
                    "",
                )
                cleaned = cleaned.replace(
                    ",",
                    ".",
                )
            else:
                cleaned = cleaned.replace(
                    ",",
                    "",
                )
        elif "," in cleaned:
            parts = cleaned.split(",")

            if (
                len(parts) == 2
                and len(parts[1]) <= 2
            ):
                cleaned = cleaned.replace(
                    ",",
                    ".",
                )
            else:
                cleaned = cleaned.replace(
                    ",",
                    "",
                )
        elif "." in cleaned:
            parts = cleaned.split(".")

            if (
                len(parts) > 2
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):
                cleaned = "".join(parts)

        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _normalize_text_value(
        value: str,
    ) -> str:
        return " ".join(
            str(value).strip().split()
        )

    @staticmethod
    def _symbol_currency(
        symbol: str,
    ) -> str:
        return {
            "S/": "PEN",
            "S/.": "PEN",
            "US$": "USD",
            "U$S": "USD",
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
        }.get(
            symbol.upper(),
            "",
        )

    @staticmethod
    def _deduplicate(
        values: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()

        for value in values:
            key = repr(
                (
                    value.get(
                        "fact_type",
                        value.get(
                            "name",
                            "",
                        ),
                    ),
                    value.get(
                        "label",
                        "",
                    ),
                    value.get(
                        "normalized_label",
                        "",
                    ),
                    value.get(
                        "raw_value",
                        value.get(
                            "value",
                            "",
                        ),
                    ),
                    value.get(
                        "page_number",
                        "",
                    ),
                    value.get(
                        "region_id",
                        "",
                    ),
                )
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(value)

        return unique

