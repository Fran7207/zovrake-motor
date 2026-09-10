"""Selección de evidencia para reducir contexto sin perder señales críticas."""

from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from typing import Any
import base64
import hashlib

from PIL import Image


class ComprehensionEvidenceSelector:
    def __init__(self, *, max_pages_normal: int = 4, max_pages_complex: int = 8) -> None:
        self.max_pages_normal = max_pages_normal
        self.max_pages_complex = max_pages_complex

    def select(self, knowledge, route, pdf_bytes: bytes | None) -> dict[str, Any]:
        metadata = getattr(knowledge, "metadata", {}) or {}
        universal = metadata.get("deep_universal_understanding", {}) or {}
        scores: defaultdict[int, int] = defaultdict(int)

        def add_page(page: Any, score: int) -> None:
            if isinstance(page, int) and page > 0:
                scores[page] += score

        for collection_name, weight in (
            ("resolved_roles", 10),
            ("semantic_fields", 5),
            ("conflicts", 9),
        ):
            for item in universal.get(collection_name, ()) or ():
                if not isinstance(item, dict):
                    continue
                add_page(item.get("page_number"), weight)
                for source_id in item.get("source_ids", ()) or ():
                    for entry in getattr(knowledge, "reading_order", ()) or ():
                        if str(entry.get("source_id", "")) == str(source_id):
                            add_page(entry.get("page_number"), weight)

        for table in getattr(knowledge, "tables", ()) or ():
            if isinstance(table, dict):
                add_page(
                    table.get("page_number") or table.get("source_page_number"),
                    7,
                )

        for image in getattr(knowledge, "images", ()) or ():
            if isinstance(image, dict):
                add_page(image.get("page_number"), 4)

        max_pages = (
            self.max_pages_complex
            if str(getattr(route, "value", route)) == "full_pdf"
            else self.max_pages_normal
        )

        pages = sorted(scores, key=lambda p: (-scores[p], p))[:max_pages]
        if not pages:
            total = int(getattr(knowledge, "page_count", 0) or 0)
            pages = list(range(1, min(total, max_pages) + 1))

        selected_text = self._compact_text(knowledge, pages)
        selected_images = self._render_selected_pages(pdf_bytes, pages)

        return {
            "selected_pages": pages,
            "selected_text": selected_text,
            "selected_images": selected_images,
            "evidence_mode": "page_ranked",
        }

    @staticmethod
    def _compact_text(knowledge, pages: list[int], max_chars_per_page: int = 14_000) -> str:
        by_page: dict[int, list[str]] = defaultdict(list)
        for entry in getattr(knowledge, "reading_order", ()) or ():
            if not isinstance(entry, dict):
                continue
            page = entry.get("page_number")
            if page not in pages:
                continue
            text = str(entry.get("text") or "").strip()
            if text:
                source_id = str(entry.get("source_id") or "")
                by_page[int(page)].append(f"[{source_id}] {text}")

        blocks: list[str] = []
        for page in pages:
            text = "\n".join(by_page.get(page, ()))
            if text:
                blocks.append(f"=== PAGE {page} ===\n{text[:max_chars_per_page]}")
        if not blocks and str(getattr(knowledge, "text", "") or "").strip():
            blocks.append(str(getattr(knowledge, "text", "")).strip()[:max_chars_per_page])
        return "\n\n".join(blocks)

    @staticmethod
    def _render_selected_pages(
        pdf_bytes: bytes | None,
        pages: list[int],
    ) -> list[dict[str, Any]]:
        """
        Renderiza páginas solamente cuando hay bytes reales del PDF.

        pypdfium2 se usa aquí de forma directa para evitar acoplar la capa
        de comprensión remota al pipeline de OCR.
        """
        if not pdf_bytes:
            return []

        try:
            import pypdfium2 as pdfium
        except ImportError:
            return []

        result: list[dict[str, Any]] = []
        document = None
        try:
            document = pdfium.PdfDocument(pdf_bytes)
            for page_number in pages:
                if page_number < 1 or page_number > len(document):
                    continue
                page = None
                bitmap = None
                try:
                    page = document[page_number - 1]
                    bitmap = page.render(scale=1.0)
                    image = bitmap.to_pil().convert("RGB")
                    buffer = BytesIO()
                    image.save(buffer, format="JPEG", quality=65, optimize=True)
                    raw = buffer.getvalue()
                    result.append(
                        {
                            "page_number": page_number,
                            "image_data_url": (
                                "data:image/jpeg;base64,"
                                + base64.b64encode(raw).decode("ascii")
                            ),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "detail": "low",
                        }
                    )
                except Exception:
                    continue
                finally:
                    for obj in (bitmap, page):
                        try:
                            if obj is not None:
                                obj.close()
                        except Exception:
                            pass
        except Exception:
            return []
        finally:
            try:
                if document is not None:
                    document.close()
            except Exception:
                pass
        return result
