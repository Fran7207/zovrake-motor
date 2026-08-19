"""Resolución de contenido documental real hacia metadatos de extracción del Motor."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote


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
    re.compile(r"(?i)(?:raz[oó]n\s+social|proveedor|empresa|emisor)\s*[:\-]\s*(.+)"),
    re.compile(r"(?i)(?:cotizaci[oó]n\s+de|oferta\s+de)\s+(.+)"),
)

_CURRENCY_PATTERNS = (
    re.compile(r"(?i)\b(PEN|USD|EUR|S/\.?|US\$|\$)\b"),
)

_TOTAL_PATTERNS = (
    re.compile(r"(?i)(?:total|importe\s+total|monto\s+total)\s*[:\-]?\s*([0-9][0-9.,]*)"),
)

_PAYMENT_PATTERNS = (
    re.compile(r"(?i)(?:condiciones?\s+de\s+pago|forma\s+de\s+pago|pago)\s*[:\-]\s*(.+)"),
)

_LINE_ITEM_PATTERN = re.compile(
    r"^\s*(?P<desc>.+?)\s{2,}(?P<qty>\d+[.,]?\d*)\s*(?P<unit>[A-Za-z%/]+)?\s+(?P<price>\d+[.,]\d{2})\s*$"
)
_LINE_ITEM_FLEX_PATTERN = re.compile(
    r"^\s*(?P<desc>.+?)\s+(?P<qty>\d+[.,]?\d*)\s+(?P<unit>[A-Za-z%/]+)\s+(?P<price>\d+[.,]\d{2})\s*$"
)

_PRICE_LINE_PATTERN = re.compile(
    r"(?P<desc>.+?)\s+[x×]\s*(?P<qty>\d+[.,]?\d*)\s+(?P<price>\d+[.,]\d{2})",
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

    def to_adapter_metadata(self) -> dict[str, Any]:
        return {
            "text_content": self.text_content,
            "tables": list(self.tables),
            "items": list(self.items),
            "provider_name": self.provider_name,
            "provider_id": self.document_id,
            "commercial_currency": self.commercial_currency,
            "commercial_total_amount": self.commercial_total_amount,
            "commercial_payment_terms": self.commercial_payment_terms,
            "format_type": _format_from_content_type(self.content_type, self.file_name),
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
            "commercial_currency": self.commercial_currency,
            "commercial_total_amount": self.commercial_total_amount,
            "commercial_payment_terms": self.commercial_payment_terms,
        }


def resolve_evidence_documents(
    evidence_documents: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> tuple[ResolvedDocumentContent, ...]:
    """Resuelve documentos del Centro de Evidencias hacia contenido estructurado."""
    resolved: list[ResolvedDocumentContent] = []
    for index, raw in enumerate(evidence_documents):
        if not isinstance(raw, dict):
            continue
        document_id = str(raw.get("document_id") or f"doc-{index + 1}")
        metadata = dict(raw.get("metadata") or {})
        document_label = str(raw.get("document_label") or metadata.get("file_name") or document_id)
        content_type = str(
            raw.get("content_type")
            or metadata.get("content_type")
            or "application/octet-stream"
        )
        file_name = str(metadata.get("file_name") or document_label)
        data_url = str(metadata.get("content_data_url") or "")
        text = _decode_document_text(data_url=data_url, content_type=content_type, file_name=file_name)
        if not text.strip():
            # Fallback: al menos registra identidad documental para trazabilidad.
            text = f"{document_label}\n{file_name}"
        provider_name = _detect_provider(text, document_label, file_name)
        items = _extract_items(text)
        tables = _items_to_tables(items) if items else _extract_tables_from_text(text)
        if not items and tables:
            items = _tables_to_items(tables)
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
                metadata={
                    "uploaded_at": metadata.get("uploaded_at"),
                    "file_size": metadata.get("file_size"),
                },
            )
        )
    return tuple(resolved)


def _format_from_content_type(content_type: str, file_name: str) -> str:
    lowered = (content_type or "").lower()
    name = (file_name or "").lower()
    if lowered.startswith("text/") or "text/plain" in lowered:
        return "text"
    if "pdf" in lowered:
        return "pdf"
    if "word" in lowered or "officedocument.wordprocessingml" in lowered:
        return "docx"
    if "sheet" in lowered or "excel" in lowered or "spreadsheetml" in lowered:
        return "xlsx"
    if lowered.startswith("image/"):
        return "image"
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith((".docx", ".doc")):
        return "docx"
    if name.endswith((".xlsx", ".xls")):
        return "xlsx"
    if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    if name.endswith(".txt"):
        return "text"
    return "pdf"


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    # Conserva separaciones múltiples: son significativas para tablas/ítems.
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode_document_text(*, data_url: str, content_type: str, file_name: str) -> str:
    if not data_url:
        return ""
    payload = data_url
    mime = content_type
    if data_url.startswith("data:"):
        header, _, payload = data_url.partition(",")
        mime_part = header[5:].split(";")[0] if header.startswith("data:") else content_type
        mime = mime_part or content_type
        if ";base64" in header.lower():
            try:
                raw = base64.b64decode(payload)
            except Exception:
                return ""
        else:
            return unquote(payload)
    else:
        try:
            raw = base64.b64decode(payload)
        except Exception:
            return payload

    fmt = _format_from_content_type(mime, file_name)
    if fmt == "pdf":
        return _extract_pdf_text(raw)
    if fmt in {"text", "docx", "xlsx", "image"}:
        # DOCX/XLSX/imagen: conservar bytes decodificables; texto plano directo.
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return raw.decode("latin-1")
            except Exception:
                return _extract_pdf_text(raw) if fmt == "pdf" else ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return _extract_pdf_text(raw)


def _extract_pdf_text(raw: bytes) -> str:
    """Extracción de texto embebido en PDF sin dependencias externas."""
    chunks: list[str] = []
    # Cadenas literales PDF (entre paréntesis) y bloques Tj/TJ.
    for match in re.finditer(rb"\((?:\\.|[^\\()])*\)\s*Tj", raw):
        literal = match.group(0)[:-2]  # quita " Tj"
        chunks.append(_unescape_pdf_literal(literal[1:-1]))
    for match in re.finditer(rb"\[(.*?)\]\s*TJ", raw, re.DOTALL):
        for lit in re.finditer(rb"\((?:\\.|[^\\()])*\)", match.group(1)):
            chunks.append(_unescape_pdf_literal(lit.group(0)[1:-1]))
    # Fallback: strings ASCII largos legibles.
    if not chunks:
        ascii_parts = re.findall(rb"[\x20-\x7E\xC0-\xFF]{4,}", raw)
        text = "\n".join(part.decode("latin-1", errors="ignore") for part in ascii_parts)
        return _clean_text(text)
    return _clean_text("\n".join(chunks))


def _unescape_pdf_literal(raw: bytes) -> str:
    text = raw.decode("latin-1", errors="ignore")
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
        text = text.replace(src, dst)
    return text


def _detect_provider(text: str, document_label: str, file_name: str) -> str:
    for pattern in _PROVIDER_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip(" .-:\n\r\t")
            if candidate:
                return candidate[:120]
    base = re.sub(r"(?i)^cotizaci[oó]n[\s\-_]*", "", document_label).strip()
    base = re.sub(r"\.pdf$", "", base, flags=re.IGNORECASE).strip()
    if base:
        return base[:120]
    return re.sub(r"\.pdf$", "", file_name, flags=re.IGNORECASE)[:120] or "Proveedor"


def _detect_currency(text: str) -> str:
    for pattern in _CURRENCY_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        token = match.group(1).upper().replace(".", "")
        if token in {"S/", "S"}:
            return "PEN"
        if token in {"US$", "$"}:
            return "USD"
        return token
    return ""


def _detect_total(text: str) -> str:
    for pattern in _TOTAL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""


def _detect_payment_terms(text: str) -> str:
    for pattern in _PAYMENT_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()[:200]
    return ""


def _extract_items(text: str) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped or _looks_like_header(stripped):
            continue
        match = (
            _LINE_ITEM_PATTERN.match(stripped)
            or _LINE_ITEM_FLEX_PATTERN.match(stripped)
            or _PRICE_LINE_PATTERN.search(stripped)
        )
        if not match:
            continue
        groups = match.groupdict()
        items.append(
            {
                "item_id": f"item-{index + 1}",
                "description": groups.get("desc", "").strip(),
                "quantity": str(groups.get("qty") or "").strip(),
                "unit_price": str(groups.get("price") or "").strip(),
                "unit": str(groups.get("unit") or "").strip(),
            }
        )
    return tuple(items)


def _looks_like_header(line: str) -> bool:
    lowered = line.lower()
    hits = sum(1 for marker in _HEADER_MARKERS if marker in lowered)
    return hits >= 2


def _items_to_tables(items: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    rows = [("Descripción", "Cantidad", "Precio unitario", "Unidad")]
    for item in items:
        rows.append(
            (
                str(item.get("description", "")),
                str(item.get("quantity", "")),
                str(item.get("unit_price", "")),
                str(item.get("unit", "")),
            )
        )
    return ({"table_id": "table-items-1", "rows": rows},)


def _extract_tables_from_text(text: str) -> tuple[dict[str, Any], ...]:
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        if "|" in line:
            cells = tuple(cell.strip() for cell in line.split("|") if cell.strip())
            if len(cells) >= 2:
                rows.append(cells)
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 3 and any(ch.isdigit() for ch in line):
            rows.append(tuple(parts[:4]))
    if not rows:
        return ()
    if not _looks_like_header(" ".join(rows[0])):
        rows = [("Descripción", "Cantidad", "Precio", "Unidad"), *rows]
    return ({"table_id": "table-text-1", "rows": rows},)


def _tables_to_items(tables: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for table in tables:
        rows = list(table.get("rows") or [])
        start = 1 if rows and _looks_like_header(" ".join(str(c) for c in rows[0])) else 0
        for index, row in enumerate(rows[start:]):
            cells = list(row)
            if not cells:
                continue
            items.append(
                {
                    "item_id": f"{table.get('table_id', 'table')}-row-{index}",
                    "description": str(cells[0]) if len(cells) > 0 else "",
                    "quantity": str(cells[1]) if len(cells) > 1 else "",
                    "unit_price": str(cells[2]) if len(cells) > 2 else "",
                    "unit": str(cells[3]) if len(cells) > 3 else "",
                }
            )
    return tuple(items)
