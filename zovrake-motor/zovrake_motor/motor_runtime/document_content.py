"""Resolución de contenido documental real hacia metadatos de extracción del Motor."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote

from zovrake_motor.comprehension.pdf_processing.exceptions import (
    PdfProcessingError,
)
from zovrake_motor.comprehension.pdf_processing.processor import (
    PDFDocumentProcessor,
)


_HEADER_MARKERS = (
    "descripcion",
    "descripción",
    "item",
    "ítem",
    "cantidad",
    "precio",
    "unidad",
    "total",
    "concepto",
)

_PROVIDER_PATTERNS = (
    re.compile(
        r"(?i)(?:raz[oó]n\s+social|proveedor|empresa|emisor)\s*[:\-]\s*(.+)"
    ),
    re.compile(r"(?i)(?:cotizaci[oó]n\s+de|oferta\s+de)\s+(.+)"),
)

_CURRENCY_PATTERNS = (
    re.compile(
        r"(?i)\b(?P<code>PEN|USD|EUR|GBP|COP|MXN|CLP|ARS|BOB|BRL|"
        r"CAD|AUD|CHF|JPY|CNY|INR)\b"
    ),
    re.compile(
        r"(?i)(?P<symbol>S\/\.?|US\$|U\$S|\$|€|£|¥|Bs\.?|Bs)"
    ),
)

_FINANCIAL_LABEL_PATTERNS = {
    "subtotal": (
        re.compile(
            r"(?i)\bsub[\s\-]?total\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "discount": (
        re.compile(
            r"(?i)\bdescuent(?:o|os)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
        re.compile(
            r"(?i)\bdesc\.?\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "tax": (
        re.compile(
            r"(?i)\b(?:igv|iva|impuesto(?:s)?)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "total": (
        re.compile(
            r"(?i)\b(?:total\s+a\s+pagar|importe\s+total|monto\s+total)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
        re.compile(
            r"(?i)\btotal\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "additional_cost": (
        re.compile(
            r"(?i)\b(?:flete|transporte|env[ií]o|costo\s+adicional|"
            r"costos?\s+adicionales|recargo|cargo\s+adicional)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "withholding": (
        re.compile(
            r"(?i)\b(?:retenci[oó]n|retenciones)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "perception": (
        re.compile(
            r"(?i)\b(?:percepci[oó]n|percepciones)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
    "exchange_rate": (
        re.compile(
            r"(?i)\b(?:tipo\s+de\s+cambio|exchange\s+rate)\b"
            r"\s*[:\-]?\s*(?P<value>[^\n\r]+)"
        ),
    ),
}

_NUMBER_PATTERN = re.compile(
    r"(?<![\w])"
    r"(?:[-+]?\d{1,3}(?:[.,]\d{3})+|[-+]?\d+(?:[.,]\d+)?)"
    r"(?![\w])"
)

_PAYMENT_PATTERNS = (
    re.compile(
        r"(?i)(?:condiciones?\s+de\s+pago|forma\s+de\s+pago|pago)"
        r"\s*[:\-]\s*(.+)"
    ),
)

_LINE_ITEM_PATTERN = re.compile(
    r"^\s*(?P<desc>.+?)\s{2,}"
    r"(?P<qty>\d+[.,]?\d*)\s*"
    r"(?P<unit>[A-Za-z%/]+)?\s+"
    r"(?P<price>\d+[.,]\d{2})\s*$"
)

_LINE_ITEM_FLEX_PATTERN = re.compile(
    r"^\s*(?P<desc>.+?)\s+"
    r"(?P<qty>\d+[.,]?\d*)\s+"
    r"(?P<unit>[A-Za-z%/]+)\s+"
    r"(?P<price>\d+[.,]\d{2})\s*$"
)

_PRICE_LINE_PATTERN = re.compile(
    r"(?P<desc>.+?)\s+[x×]\s*"
    r"(?P<qty>\d+[.,]?\d*)\s+"
    r"(?P<price>\d+[.,]\d{2})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResolvedDocumentContent:
    """Contenido resuelto listo para ``AdapterDocumentContext.metadata``."""

    document_id: str
    document_label: str
    content_type: str
    file_name: str
    provider_name: str
    text_content: str
    tables: tuple[dict[str, Any], ...]
    items: tuple[dict[str, Any], ...]
    commercial_currency: str
    commercial_total_amount: str
    commercial_payment_terms: str
    metadata: dict[str, Any] = field(default_factory=dict)
    semantic_tables: tuple[dict[str, Any], ...] = ()

    def to_adapter_metadata(self) -> dict[str, Any]:
        return {
            "text_content": self.text_content,
            "tables": list(self.tables),
            "semantic_tables": list(self.semantic_tables),
            "items": list(self.items),
            "provider_name": self.provider_name,
            "provider_id": self.document_id,
            "commercial_currency": self.commercial_currency,
            "commercial_total_amount": self.commercial_total_amount,
            "commercial_payment_terms": self.commercial_payment_terms,
            "format_type": _format_from_content_type(
                self.content_type,
                self.file_name,
            ),
            "file_name": self.file_name,
            "document_label": self.document_label,
            "source": "evidence_center",
            **self.metadata,
        }

    def to_summary(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_label": self.document_label,
            "file_name": self.file_name,
            "provider_name": self.provider_name,
            "content_type": self.content_type,
            "text_length": len(self.text_content),
            "items_count": len(self.items),
            "tables_count": len(self.tables),
            "semantic_tables_count": len(self.semantic_tables),
            "commercial_currency": self.commercial_currency,
            "commercial_total_amount": self.commercial_total_amount,
            "commercial_payment_terms": self.commercial_payment_terms,
        }


def resolve_evidence_documents(
    evidence_documents: list[dict[str, Any]]
    | tuple[dict[str, Any], ...],
) -> tuple[ResolvedDocumentContent, ...]:
    """
    Resuelve documentos del Centro de Evidencias hacia contenido estructurado.

    Para PDF, la ruta principal utiliza PDFDocumentProcessor.
    La extracción PDF antigua queda solamente como fallback controlado.
    """
    resolved: list[ResolvedDocumentContent] = []

    for index, raw in enumerate(evidence_documents):
        if not isinstance(raw, dict):
            continue

        document_id = str(
            raw.get("document_id")
            or f"doc-{index + 1}"
        )

        metadata = dict(raw.get("metadata") or {})

        document_label = str(
            raw.get("document_label")
            or metadata.get("file_name")
            or document_id
        )

        content_type = str(
            raw.get("content_type")
            or metadata.get("content_type")
            or "application/octet-stream"
        )

        file_name = str(
            metadata.get("file_name")
            or document_label
        )

        data_url = str(
            metadata.get("content_data_url")
            or ""
        )

        (
            text,
            extracted_tables,
            pdf_processing,
            semantic_tables,
        ) = _decode_document_content(
            data_url=data_url,
            content_type=content_type,
            file_name=file_name,
        )

        if not text.strip():
            # Fallback de identidad documental para trazabilidad.
            text = (
                f"{document_label}\n"
                f"{file_name}"
            )

        provider_name = _detect_provider(
            text,
            document_label,
            file_name,
        )

        items = _extract_items(text)

        if extracted_tables:
            tables = extracted_tables
        elif items:
            tables = _items_to_tables(items)
        else:
            tables = _extract_tables_from_text(text)

        if not items and tables:
            items = _tables_to_items(tables)

        financial_information = _extract_financial_information(
            text,
            semantic_tables=semantic_tables,
        )

        currency = _detect_currency(text)
        total = _detect_total(text)
        payment = _detect_payment_terms(text)

        resolved.append(
            ResolvedDocumentContent(
                document_id=document_id,
                document_label=document_label,
                content_type=content_type,
                file_name=file_name,
                provider_name=provider_name,
                text_content=text,
                tables=tables,
                items=items,
                commercial_currency=currency,
                commercial_total_amount=total,
                commercial_payment_terms=payment,
                semantic_tables=semantic_tables,
                metadata={
                    "uploaded_at": metadata.get("uploaded_at"),
                    "file_size": metadata.get("file_size"),
                    "commercial_financial": financial_information,
                    **(
                        {"pdf_processing": pdf_processing}
                        if pdf_processing
                        else {}
                    ),
                },
            )
        )

    return tuple(resolved)


def _format_from_content_type(
    content_type: str,
    file_name: str,
) -> str:
    lowered = (content_type or "").lower()
    name = (file_name or "").lower()

    if lowered.startswith("text/") or "text/plain" in lowered:
        return "text"

    if "pdf" in lowered:
        return "pdf"

    if (
        "word" in lowered
        or "officedocument.wordprocessingml" in lowered
    ):
        return "docx"

    if (
        "sheet" in lowered
        or "excel" in lowered
        or "spreadsheetml" in lowered
    ):
        return "xlsx"

    if lowered.startswith("image/"):
        return "image"

    if name.endswith(".pdf"):
        return "pdf"

    if name.endswith((".docx", ".doc")):
        return "docx"

    if name.endswith((".xlsx", ".xls")):
        return "xlsx"

    if name.endswith(
        (".png", ".jpg", ".jpeg", ".webp")
    ):
        return "image"

    if name.endswith(".txt"):
        return "text"

    return "pdf"


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")

    # Conserva las separaciones de línea importantes para
    # detectar posteriormente tablas e ítems.
    text = re.sub(
        r"[ \t]*\n[ \t]*",
        "\n",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def _decode_document_content(
    *,
    data_url: str,
    content_type: str,
    file_name: str,
) -> tuple[
    str,
    tuple[dict[str, Any], ...],
    dict[str, Any] | None,
    tuple[dict[str, Any], ...],
]:
    """
    Decodifica y resuelve el contenido documental.

    Devuelve:
        texto,
        tablas estructuradas,
        metadata del procesamiento PDF cuando corresponda.
    """
    if not data_url:
        return "", (), None, ()

    payload = data_url
    mime = content_type

    if data_url.startswith("data:"):
        header, _, payload = data_url.partition(",")

        mime_part = (
            header[5:].split(";", 1)[0]
            if header.startswith("data:")
            else content_type
        )

        mime = mime_part or content_type

        if ";base64" in header.lower():
            try:
                raw = base64.b64decode(
                    payload,
                    validate=True,
                )
            except Exception:
                return (
                    "",
                    (),
                    {
                        "status": "decode_error",
                        "errors": [
                            "No fue posible decodificar "
                            "el contenido base64."
                        ],
                    },
                    (),
                )
        else:
            return (
                _clean_text(unquote(payload)),
                (),
                None,
                (),
            )

    else:
        try:
            raw = base64.b64decode(
                payload,
                validate=True,
            )
        except Exception:
            raw = payload.encode(
                "utf-8",
                errors="ignore",
            )

    fmt = _format_from_content_type(
        mime,
        file_name,
    )

    # ============================================================
    # NUEVA RUTA PDF
    # ============================================================

    if fmt == "pdf":
        processor = PDFDocumentProcessor()

        try:
            processed = processor.process(
                document_id=file_name,
                file_name=file_name,
                pdf_bytes=raw,
            )

            tables = tuple(
                table.to_dict()
                for table in processed.tables
            )

            semantic_tables = tuple(
                table.to_dict()
                for table in processed.semantic_tables
            )

            processing_metadata = {
                "status": (
                    "processed"
                    if processed.successfully_processed
                    else "processed_with_errors"
                ),
                "document_id": processed.document_id,
                "file_name": processed.file_name,
                "page_count": processed.page_count,
                "ocr_required": processed.ocr_required,
                "extraction_method": processed.extraction_method,
                "tables_count": len(processed.tables),
                "semantic_tables_count": len(
                    processed.semantic_tables
                ),
                "images_count": len(processed.images),
                "warnings": list(
                    processed.warnings
                ),
                "errors": list(
                    processed.errors
                ),
                "semantic_tables": list(
                    semantic_tables
                ),
                "pages": [
                    {
                        "page_number": page.page_number,
                        "width": page.width,
                        "height": page.height,
                        "has_text": page.has_text,
                        "has_tables": page.has_tables,
                        "has_images": page.has_images,
                        "requires_ocr": page.requires_ocr,
                        "tables_count": len(
                            page.tables
                        ),
                        "semantic_tables_count": len(
                            page.semantic_tables
                        ),
                        "semantic_tables": [
                            table.to_dict()
                            for table in page.semantic_tables
                        ],
                        "images_count": len(
                            page.images
                        ),
                        "text_length": len(
                            page.text
                        ),
                        "warnings": list(
                            page.warnings
                        ),
                    }
                    for page in processed.pages
                ],
                "pdf_metadata": dict(
                    processed.pdf_metadata
                ),
            }

            return (
                processed.full_text,
                tables,
                processing_metadata,
                semantic_tables,
            )

        except PdfProcessingError as exc:
            # Fallback controlado para mantener compatibilidad
            # mientras terminamos la transición al nuevo procesador.
            fallback_text = _extract_pdf_text(raw)

            return (
                fallback_text,
                (),
                {
                    "status": "fallback_legacy_extractor",
                    "extraction_method": (
                        "legacy_regex_fallback"
                    ),
                    "warnings": [
                        "El procesador PDF avanzado "
                        "no pudo completar el documento."
                    ],
                    "errors": [str(exc)],
                    "pages": [],
                },
                (),
            )

    # ============================================================
    # Rutas no PDF: se mantienen sin cambios funcionales
    # ============================================================

    if fmt == "text":
        try:
            return (
                _clean_text(
                    raw.decode("utf-8")
                ),
                (),
                None,
                (),
            )
        except UnicodeDecodeError:
            return (
                _clean_text(
                    raw.decode(
                        "latin-1",
                        errors="ignore",
                    )
                ),
                (),
                None,
                (),
            )

    if fmt in {
        "docx",
        "xlsx",
        "image",
    }:
        try:
            return (
                raw.decode("utf-8"),
                (),
                None,
                (),
            )
        except UnicodeDecodeError:
            try:
                return (
                    raw.decode("latin-1"),
                    (),
                    None,
                    (),
                )
            except Exception:
                return "", (), None, ()

    try:
        return (
            _clean_text(
                raw.decode("utf-8")
            ),
            (),
            None,
            (),
        )
    except UnicodeDecodeError:
        return (
            _clean_text(
                raw.decode(
                    "latin-1",
                    errors="ignore",
                )
            ),
            (),
            None,
            (),
        )


def _decode_document_text(
    *,
    data_url: str,
    content_type: str,
    file_name: str,
) -> str:
    """
    Función de compatibilidad.

    Devuelve solamente el texto y mantiene el contrato anterior para
    cualquier código interno que todavía la utilice directamente.
    """
    text, _, _, _ = _decode_document_content(
        data_url=data_url,
        content_type=content_type,
        file_name=file_name,
    )

    return text


def _extract_pdf_text(raw: bytes) -> str:
    """
    Fallback heredado para PDFs que no puedan procesarse con
    PDFDocumentProcessor.

    Esta función NO es la ruta principal.
    """
    chunks: list[str] = []

    # Cadenas literales PDF entre paréntesis seguidas de Tj.
    for match in re.finditer(
        rb"\((?:\\.|[^\\()])*\)\s*Tj",
        raw,
    ):
        literal = match.group(0)[:-2]
        chunks.append(
            _unescape_pdf_literal(
                literal[1:-1]
            )
        )

    # Bloques de cadenas seguidas de TJ.
    for match in re.finditer(
        rb"\[(.*?)\]\s*TJ",
        raw,
        re.DOTALL,
    ):
        for lit in re.finditer(
            rb"\((?:\\.|[^\\()])*\)",
            match.group(1),
        ):
            chunks.append(
                _unescape_pdf_literal(
                    lit.group(0)[1:-1]
                )
            )

    # Fallback final para cadenas ASCII/Latin-1 legibles.
    if not chunks:
        ascii_parts = re.findall(
            rb"[\x20-\x7E\xC0-\xFF]{4,}",
            raw,
        )

        text = "\n".join(
            part.decode(
                "latin-1",
                errors="ignore",
            )
            for part in ascii_parts
        )

        return _clean_text(text)

    return _clean_text(
        "\n".join(chunks)
    )


def _unescape_pdf_literal(raw: bytes) -> str:
    text = raw.decode(
        "latin-1",
        errors="ignore",
    )

    replacements = {
        r"\n": "\n",
        r"\r": "\r",
        r"\t": "\t",
        r"\b": " ",
        r"\f": " ",
        r"\(": "(",
        r"\)": ")",
        r"\\": "\\",
    }

    for src, dst in replacements.items():
        text = text.replace(
            src,
            dst,
        )

    return text


def _detect_provider(
    text: str,
    document_label: str,
    file_name: str,
) -> str:
    for pattern in _PROVIDER_PATTERNS:
        match = pattern.search(text)

        if match:
            candidate = match.group(1).strip(
                " .-:\n\r\t"
            )

            if candidate:
                return candidate[:120]

    base = re.sub(
        r"(?i)^cotizaci[oó]n[\s\-_]*",
        "",
        document_label,
    ).strip()

    base = re.sub(
        r"\.pdf$",
        "",
        base,
        flags=re.IGNORECASE,
    ).strip()

    if base:
        return base[:120]

    return (
        re.sub(
            r"\.pdf$",
            "",
            file_name,
            flags=re.IGNORECASE,
        )[:120]
        or "Proveedor"
    )


def _detect_currency(text: str) -> str:
    """
    Detecta la moneda documental dominante sin depender de la primera
    coincidencia encontrada.

    Se priorizan códigos explícitos y posteriormente símbolos monetarios.
    Mantiene el contrato histórico ``str -> str``.
    """
    if not text:
        return ""

    code_map = {
        "PEN": "PEN",
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
        "COP": "COP",
        "MXN": "MXN",
        "CLP": "CLP",
        "ARS": "ARS",
        "BOB": "BOB",
        "BRL": "BRL",
        "CAD": "CAD",
        "AUD": "AUD",
        "CHF": "CHF",
        "JPY": "JPY",
        "CNY": "CNY",
        "INR": "INR",
    }

    symbol_map = {
        "S/": "PEN",
        "S/.": "PEN",
        "US$": "USD",
        "U$S": "USD",
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "BS": "BOB",
        "BS.": "BOB",
    }

    scores: dict[str, float] = {}

    for pattern in _CURRENCY_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groupdict()
            token = (
                groups.get("code")
                or groups.get("symbol")
                or ""
            ).strip()

            if not token:
                continue

            normalized = token.upper().replace(" ", "")
            currency = code_map.get(normalized)

            if currency is None:
                currency = symbol_map.get(normalized)

            if currency is None:
                currency = symbol_map.get(token)

            if currency is None:
                continue

            weight = 3.0 if groups.get("code") else 1.0
            scores[currency] = scores.get(currency, 0.0) + weight

    if not scores:
        return ""

    return max(scores, key=scores.get)


def _detect_total(text: str) -> str:
    """
    Detecta el total principal de forma conservadora.

    Prioriza expresiones inequívocas antes que la etiqueta genérica
    ``total``. Mantiene el formato numérico encontrado.
    """
    if not text:
        return ""

    for pattern in _FINANCIAL_LABEL_PATTERNS["total"]:
        match = pattern.search(text)

        if not match:
            continue

        raw_value = match.group("value").strip()
        number_match = _NUMBER_PATTERN.search(raw_value)

        if number_match:
            return number_match.group(0).strip()

    return ""


def _extract_financial_information(
    text: str,
    *,
    semantic_tables: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """
    Construye información financiera documental rica y trazable.

    Conserva valor original, valor numérico normalizado cuando es posible,
    moneda, tipo de hecho, origen y referencia.

    No convierte monedas y no presupone una estructura financiera única.
    """

    fact_types = (
        "subtotal",
        "discount",
        "tax",
        "total",
        "additional_cost",
        "withholding",
        "perception",
        "exchange_rate",
    )

    facts: dict[str, list[dict[str, Any]]] = {
        fact_type: []
        for fact_type in fact_types
    }

    currencies: list[dict[str, Any]] = []

    def normalize_number(value: str) -> float | None:
        cleaned = re.sub(r"[^\d,.\-+]", "", value.strip())

        if not cleaned:
            return None

        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "")
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            decimal_part = cleaned.rsplit(",", 1)[-1]

            if len(decimal_part) <= 2:
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "." in cleaned:
            parts = cleaned.split(".")

            if (
                len(parts) > 2
                and all(len(part) == 3 for part in parts[1:])
            ):
                cleaned = "".join(parts)

        try:
            return float(cleaned)
        except ValueError:
            return None

    def detect_currency(value: str) -> str:
        normalized = value.upper()

        for code in (
            "PEN",
            "USD",
            "EUR",
            "GBP",
            "COP",
            "MXN",
            "CLP",
            "ARS",
            "BOB",
            "BRL",
            "CAD",
            "AUD",
            "CHF",
            "JPY",
            "CNY",
            "INR",
        ):
            if code in normalized:
                return code

        if "S/" in normalized:
            return "PEN"
        if "US$" in normalized or "U$S" in normalized:
            return "USD"
        if "$" in value:
            return "USD"
        if "€" in value:
            return "EUR"
        if "£" in value:
            return "GBP"
        if "¥" in value:
            return "JPY"
        if "BS." in normalized or re.search(r"\bBS\b", normalized):
            return "BOB"

        return ""

    def append_fact(
        *,
        fact_type: str,
        raw_value: str,
        source_kind: str,
        source_reference: str,
    ) -> None:
        value = raw_value.strip()

        if not value:
            return

        number_match = _NUMBER_PATTERN.search(value)

        fact = {
            "fact_type": fact_type,
            "raw_value": value,
            "normalized_value": (
                normalize_number(number_match.group(0))
                if number_match
                else None
            ),
            "currency": detect_currency(value),
            "source_kind": source_kind,
            "source_reference": source_reference,
        }

        facts[fact_type].append(fact)

        if fact["currency"]:
            currencies.append(
                {
                    "currency": fact["currency"],
                    "raw_value": value,
                    "source_kind": source_kind,
                    "source_reference": source_reference,
                }
            )

    # -------------------------------------------------------------
    # Texto documental.
    # -------------------------------------------------------------
    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        stripped = line.strip()

        if not stripped:
            continue

        for fact_type, patterns in _FINANCIAL_LABEL_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(stripped)

                if not match:
                    continue

                append_fact(
                    fact_type=fact_type,
                    raw_value=match.group("value"),
                    source_kind="text",
                    source_reference=f"line:{line_number}",
                )
                break

    # -------------------------------------------------------------
    # Tablas semánticas.
    # -------------------------------------------------------------
    for table_index, table in enumerate(semantic_tables):
        if not isinstance(table, dict):
            continue

        table_id = str(
            table.get(
                "table_id",
                f"semantic-table-{table_index + 1}",
            )
        ).strip()

        page_number = table.get("source_page_number")
        rows = table.get("rows", ())

        if not isinstance(rows, (list, tuple)):
            continue

        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue

            for key, raw_value in row.items():
                value = (
                    ""
                    if raw_value is None
                    else str(raw_value).strip()
                )

                if not value:
                    continue

                normalized_key = str(key).strip().lower()

                source_reference = (
                    f"{table_id}/"
                    f"page:{page_number}/"
                    f"row:{row_index}/"
                    f"column:{normalized_key}"
                )

                fact_type = {
                    "subtotal": "subtotal",
                    "discount": "discount",
                    "descuento": "discount",
                    "tax": "tax",
                    "igv": "tax",
                    "iva": "tax",
                    "impuesto": "tax",
                    "total": "total",
                    "total_amount": "total",
                    "additional_cost": "additional_cost",
                    "costo_adicional": "additional_cost",
                    "withholding": "withholding",
                    "retention": "withholding",
                    "perception": "perception",
                    "exchange_rate": "exchange_rate",
                }.get(normalized_key)

                if fact_type:
                    append_fact(
                        fact_type=fact_type,
                        raw_value=value,
                        source_kind="semantic_table",
                        source_reference=source_reference,
                    )
                elif normalized_key in {"currency", "moneda"}:
                    currency = detect_currency(value)

                    if currency:
                        currencies.append(
                            {
                                "currency": currency,
                                "raw_value": value,
                                "source_kind": "semantic_table",
                                "source_reference": source_reference,
                            }
                        )

    # -------------------------------------------------------------
    # Dedupe determinista.
    # -------------------------------------------------------------
    for fact_type, values in facts.items():
        unique: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()

        for fact in values:
            signature = (
                fact["fact_type"],
                fact["raw_value"],
                fact["normalized_value"],
                fact["currency"],
                fact["source_kind"],
                fact["source_reference"],
            )

            if signature in seen:
                continue

            seen.add(signature)
            unique.append(fact)

        facts[fact_type] = unique

    unique_currencies: list[dict[str, Any]] = []
    seen_currencies: set[tuple[str, str, str]] = set()

    for currency_fact in currencies:
        signature = (
            currency_fact["currency"],
            currency_fact["raw_value"],
            currency_fact["source_reference"],
        )

        if signature in seen_currencies:
            continue

        seen_currencies.add(signature)
        unique_currencies.append(currency_fact)

    return {
        "currencies": unique_currencies,
        "facts": facts,
        "currency_count": len(unique_currencies),
        "fact_count": sum(
            len(values)
            for values in facts.values()
        ),
    }


def _detect_payment_terms(text: str) -> str:
    for pattern in _PAYMENT_PATTERNS:
        match = pattern.search(text)

        if match:
            return match.group(1).strip()[:200]

    return ""


def _extract_items(
    text: str,
) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []

    for index, line in enumerate(
        text.splitlines()
    ):
        stripped = line.strip()

        if (
            not stripped
            or _looks_like_header(stripped)
        ):
            continue

        match = (
            _LINE_ITEM_PATTERN.match(stripped)
            or _LINE_ITEM_FLEX_PATTERN.match(
                stripped
            )
            or _PRICE_LINE_PATTERN.search(
                stripped
            )
        )

        if not match:
            continue

        groups = match.groupdict()

        items.append(
            {
                "item_id": f"item-{index + 1}",
                "description": str(
                    groups.get("desc", "")
                ).strip(),
                "quantity": str(
                    groups.get("qty") or ""
                ).strip(),
                "unit_price": str(
                    groups.get("price") or ""
                ).strip(),
                "unit": str(
                    groups.get("unit") or ""
                ).strip(),
            }
        )

    return tuple(items)


def _looks_like_header(
    line: str,
) -> bool:
    lowered = line.lower()

    hits = sum(
        1
        for marker in _HEADER_MARKERS
        if marker in lowered
    )

    return hits >= 2


def _items_to_tables(
    items: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    rows = [
        (
            "Descripción",
            "Cantidad",
            "Precio unitario",
            "Unidad",
        )
    ]

    for item in items:
        rows.append(
            (
                str(
                    item.get(
                        "description",
                        "",
                    )
                ),
                str(
                    item.get(
                        "quantity",
                        "",
                    )
                ),
                str(
                    item.get(
                        "unit_price",
                        "",
                    )
                ),
                str(
                    item.get(
                        "unit",
                        "",
                    )
                ),
            )
        )

    return (
        {
            "table_id": "table-items-1",
            "rows": rows,
        },
    )


def _extract_tables_from_text(
    text: str,
) -> tuple[dict[str, Any], ...]:
    rows: list[tuple[str, ...]] = []

    for line in text.splitlines():
        if "|" in line:
            cells = tuple(
                cell.strip()
                for cell in line.split("|")
                if cell.strip()
            )

            if len(cells) >= 2:
                rows.append(cells)

            continue

        parts = re.split(
            r"\s{2,}",
            line.strip(),
        )

        if (
            len(parts) >= 3
            and any(
                ch.isdigit()
                for ch in line
            )
        ):
            rows.append(
                tuple(parts[:4])
            )

    if not rows:
        return ()

    if not _looks_like_header(
        " ".join(rows[0])
    ):
        rows = [
            (
                "Descripción",
                "Cantidad",
                "Precio",
                "Unidad",
            ),
            *rows,
        ]

    return (
        {
            "table_id": "table-text-1",
            "rows": rows,
        },
    )


def _tables_to_items(
    tables: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []

    for table in tables:
        rows = list(
            table.get("rows") or []
        )

        start = (
            1
            if rows
            and _looks_like_header(
                " ".join(
                    str(c)
                    for c in rows[0]
                )
            )
            else 0
        )

        for index, row in enumerate(
            rows[start:],
        ):
            cells = list(row)

            if not cells:
                continue

            items.append(
                {
                    "item_id": (
                        f"{table.get('table_id', 'table')}"
                        f"-row-{index}"
                    ),
                    "description": (
                        str(cells[0])
                        if len(cells) > 0
                        else ""
                    ),
                    "quantity": (
                        str(cells[1])
                        if len(cells) > 1
                        else ""
                    ),
                    "unit_price": (
                        str(cells[2])
                        if len(cells) > 2
                        else ""
                    ),
                    "unit": (
                        str(cells[3])
                        if len(cells) > 3
                        else ""
                    ),
                }
            )

    return tuple(items)
