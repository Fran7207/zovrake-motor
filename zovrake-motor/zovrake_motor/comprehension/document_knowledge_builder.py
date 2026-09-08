"""Construcción determinista del conocimiento documental unificado."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from zovrake_motor.comprehension.models import (
    DocumentEvidence,
    DocumentKnowledge,
    DocumentRegion,
)
from zovrake_motor.comprehension.pdf_processing.models import (
    PdfPageAnalysis,
    ProcessedPdfDocument,
)


class DocumentKnowledgeBuilder:
    """
    Convierte la representación física procesada del PDF en un modelo de
    conocimiento documental unificado.

    Esta primera etapa NO intenta adivinar el significado de todo el
    documento. Su responsabilidad es:

    - conservar el contenido ya extraído;
    - conservar su organización por página;
    - conservar tablas, tablas semánticas e imágenes;
    - conservar OCR separado del texto nativo;
    - crear regiones documentales;
    - crear evidencia trazable para cada región;
    - registrar advertencias y errores como información no resuelta.

    La interpretación semántica profunda se realizará encima de esta capa.
    """

    MODEL_VERSION = "1.0-physical-unified"

    def build(
        self,
        document: ProcessedPdfDocument,
    ) -> DocumentKnowledge:
        """
        Construye DocumentKnowledge a partir de ProcessedPdfDocument.

        No vuelve a abrir el PDF ni vuelve a extraer contenido.
        Utiliza exclusivamente la representación producida por
        PDFDocumentProcessor.
        """
        if not isinstance(
            document,
            ProcessedPdfDocument,
        ):
            raise TypeError(
                "document debe ser una instancia de "
                "ProcessedPdfDocument"
            )

        regions: list[DocumentRegion] = []
        evidence: list[DocumentEvidence] = []
        unresolved: list[dict[str, Any]] = []

        for page in document.pages:
            page_regions, page_evidence = (
                self._build_page_regions(page)
            )

            regions.extend(page_regions)
            evidence.extend(page_evidence)

            for warning in page.warnings:
                unresolved.append(
                    {
                        "type": "processing_warning",
                        "page_number": page.page_number,
                        "message": str(warning),
                    }
                )

            for error in page.errors:
                unresolved.append(
                    {
                        "type": "processing_error",
                        "page_number": page.page_number,
                        "message": str(error),
                    }
                )

        # ---------------------------------------------------------
        # Objetos estructurales globales y de página.
        # ---------------------------------------------------------
        for item in document.structural_objects:
            region_id = self._stable_id(
                item.page_number or 0,
                "structural",
                item.object_id,
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=item.page_number or 1,
                region_type="structural_object",
                bbox=item.bbox,
                content=item.text,
                source_kind="pdf_structure",
                confidence=1.0,
                metadata=item.to_dict(),
            )

            regions.append(region)
            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=item.object_id,
                )
            )

        regions = self._order_regions(
            regions=regions,
            reading_order=document.reading_order,
        )

        page_coverage = (
            sum(
                1
                for page in document.pages
                if not page.errors
            )
            / document.page_count
            if document.page_count
            else 0.0
        )

        # Esta confianza representa cobertura física del procesamiento.
        # NO representa todavía confianza semántica.
        confidence = round(
            max(
                0.0,
                min(
                    1.0,
                    page_coverage,
                ),
            ),
            4,
        )

        metadata = dict(
            document.pdf_metadata
        )

        metadata.update(
            {
                "knowledge_model_version": (
                    self.MODEL_VERSION
                ),
                "knowledge_stage": (
                    "physical_unified"
                ),
                "source_extraction_method": (
                    document.extraction_method
                ),
                "source_page_count": (
                    document.page_count
                ),
                "source_tables_count": (
                    len(document.tables)
                ),
                "source_semantic_tables_count": (
                    len(document.semantic_tables)
                ),
                "source_images_count": (
                    len(document.images)
                ),
                "source_structural_objects_count": (
                    len(document.structural_objects)
                ),
                "source_structural_object_counts": self._count_structural_objects(
                    document.structural_objects
                ),
                "source_coverage": dict(document.coverage),
                "source_ocr_required": (
                    document.ocr_required
                ),
                "source_ocr_executed": (
                    document.ocr_executed
                ),
                "source_ocr_confidence": (
                    document.ocr_confidence
                ),
                "source_ocr_language": (
                    document.ocr_language
                ),
                "source_ocr_dpi": (
                    document.ocr_dpi
                ),
                "source_visual_ocr_complete": (
                    document.visual_ocr_complete
                ),
                "source_visual_ocr_pages_executed": (
                    list(document.visual_ocr_pages_executed)
                ),
                "source_visual_text_length": (
                    len(document.visual_text)
                ),
                "source_reading_order_count": len(document.reading_order),
                "source_ordered_text_length": len(document.ordered_text),
                "source_unordered_text": document.full_text,
                "reading_contract_version": "1.0-spatial-preserved",
                "region_count": len(regions),
                "evidence_count": len(evidence),
                "unresolved_count": len(unresolved),
            }
        )

        return DocumentKnowledge(
            document_id=document.document_id,
            file_name=document.file_name,
            content_type="application/pdf",
            page_count=document.page_count,
            regions=tuple(regions),
            # La comprensión recibe como texto principal la secuencia espacial
            # ordenada; el texto nativo original queda preservado en metadata.
            text=document.ordered_text or document.full_text,
            visual_text=document.visual_text,
            tables=tuple(
                table.to_dict()
                for table in document.tables
            ),
            images=tuple(
                image.to_dict()
                for image in document.images
            ),
            structural_objects=tuple(
                item.to_dict()
                for item in document.structural_objects
            ),
            ocr_blocks=tuple(
                block.to_dict()
                for page in document.pages
                for block in page.ocr_blocks
            ),
            reading_order=tuple(
                entry.to_dict()
                for entry in document.reading_order
            ),
            ordered_text=document.ordered_text,
            sections=(),
            entities=(),
            attributes=(),
            relationships=(),
            facts=(),
            evidence=tuple(evidence),
            unresolved=tuple(unresolved),
            confidence=confidence,
            metadata=metadata,
        )

    @staticmethod
    def _order_regions(
        *,
        regions: list[DocumentRegion],
        reading_order: tuple[Any, ...],
    ) -> list[DocumentRegion]:
        """Ordena regiones según la secuencia espacial sin descartar regiones auxiliares."""
        source_rank: dict[str, int] = {}
        for entry in reading_order:
            source_id = str(getattr(entry, "source_id", "") or "")
            if source_id:
                source_rank[source_id] = int(getattr(entry, "sequence", 0) or 0)

        def key(region: DocumentRegion) -> tuple[int, int, float, float, str]:
            direct_rank = source_rank.get(region.metadata.get("block_id", ""), 0)
            if not direct_rank:
                direct_rank = source_rank.get(region.metadata.get("table_id", ""), 0)
            if not direct_rank:
                direct_rank = source_rank.get(region.metadata.get("image_id", ""), 0)
            if not direct_rank and region.source_kind == "visual_understanding":
                direct_rank = source_rank.get(
                    f"page-{region.page_number}-visual",
                    0,
                )

            if region.bbox is not None:
                y, x = float(region.bbox[1]), float(region.bbox[0])
            else:
                y, x = float("inf"), float("inf")

            return (
                region.page_number,
                direct_rank if direct_rank else 10**9,
                y,
                x,
                region.region_id,
            )

        return sorted(regions, key=key)

    def _build_page_regions(
        self,
        page: PdfPageAnalysis,
    ) -> tuple[
        list[DocumentRegion],
        list[DocumentEvidence],
    ]:
        regions: list[DocumentRegion] = []
        evidence: list[DocumentEvidence] = []

        # ---------------------------------------------------------
        # 1. Texto / bloques de texto.
        # ---------------------------------------------------------
        for index, block in enumerate(
            page.text_blocks,
            start=1,
        ):
            region_id = self._stable_id(
                page.page_number,
                "text",
                block.block_id,
                index,
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="text_block",
                bbox=block.bbox,
                content=block.text,
                source_kind="native_text",
                confidence=1.0,
                metadata={
                    "block_id": block.block_id,
                },
            )

            regions.append(region)

            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=block.block_id,
                )
            )

        # ---------------------------------------------------------
        # 2. Tablas físicas.
        # ---------------------------------------------------------
        for index, table in enumerate(
            page.tables,
            start=1,
        ):
            region_id = self._stable_id(
                page.page_number,
                "table",
                table.table_id,
                index,
            )

            content = "\n".join(
                " | ".join(
                    str(cell)
                    for cell in row
                )
                for row in table.rows
            )

            table_confidence = (
                table.semantic.confidence
                if table.semantic is not None
                else 1.0
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="table",
                bbox=table.bbox,
                content=content,
                source_kind="pdf_table",
                confidence=max(
                    0.0,
                    min(
                        1.0,
                        table_confidence,
                    ),
                ),
                metadata={
                    "table_id": table.table_id,
                    "row_count": len(table.rows),
                    "has_semantic_table": (
                        table.semantic is not None
                    ),
                },
            )

            regions.append(region)

            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=table.table_id,
                )
            )

        # ---------------------------------------------------------
        # 3. Tablas semánticas.
        #
        # Se mantienen como regiones independientes de las tablas físicas
        # porque tienen significado adicional que después utilizarán las
        # capas semánticas.
        # ---------------------------------------------------------
        for index, table in enumerate(
            page.semantic_tables,
            start=1,
        ):
            region_id = self._stable_id(
                page.page_number,
                "semantic_table",
                table.table_id,
                index,
            )

            content = "\n".join(
                " | ".join(
                    f"{key}={value}"
                    for key, value in row.items()
                )
                for row in table.rows
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="semantic_table",
                content=content,
                source_kind="semantic_table",
                confidence=max(
                    0.0,
                    min(
                        1.0,
                        table.confidence,
                    ),
                ),
                metadata={
                    "table_id": table.table_id,
                    "source_table_id": (
                        table.source_table_id
                    ),
                    "table_role": table.table_role,
                    "table_roles": list(
                        table.table_roles
                    ),
                    "table_role_confidence": (
                        table.table_role_confidence
                    ),
                    "table_role_evidence": list(
                        table.table_role_evidence
                    ),
                    "source_page_number": (
                        table.source_page_number
                    ),
                    "row_count": len(table.rows),
                },
            )

            regions.append(region)

            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=table.table_id,
                )
            )

        # ---------------------------------------------------------
        # 4. Imágenes embebidas.
        # ---------------------------------------------------------
        for index, image in enumerate(
            page.images,
            start=1,
        ):
            region_id = self._stable_id(
                page.page_number,
                "image",
                image.image_id,
                index,
            )

            image_payload = image.to_dict()
            visual = dict(image_payload.get("visual_understanding") or {})
            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="image",
                bbox=image.bbox,
                content=str(visual.get("description") or "").strip(),
                source_kind="pdf_image",
                confidence=max(
                    0.0,
                    min(
                        1.0,
                        float(visual.get("visual_confidence", 1.0) or 0.0),
                    ),
                ),
                metadata=image_payload,
            )

            regions.append(region)

            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=image.image_id,
                )
            )

        # ---------------------------------------------------------
        # 5. OCR directo sobre imágenes embebidas.
        # ---------------------------------------------------------
        for index, image in enumerate(
            page.images,
            start=1,
        ):
            if not image.ocr_text.strip():
                continue

            region_id = self._stable_id(
                page.page_number,
                "image_ocr",
                image.image_id,
                index,
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="image_ocr",
                bbox=image.bbox,
                content=image.ocr_text,
                source_kind="embedded_image_ocr",
                confidence=image.ocr_confidence,
                metadata={
                    "image_id": image.image_id,
                    "content_sha256": image.content_sha256,
                    "ocr_block_count": len(image.ocr_blocks),
                },
            )

            regions.append(region)
            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=image.image_id,
                )
            )

        # ---------------------------------------------------------
        # 6. OCR de página completa.
        #
        # El OCR se conserva separado del texto nativo.
        # ---------------------------------------------------------
        for index, block in enumerate(
            page.ocr_blocks,
            start=1,
        ):
            region_id = self._stable_id(
                page.page_number,
                "ocr",
                block.block_id,
                index,
            )

            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="ocr_block",
                bbox=block.bbox,
                content=block.text,
                source_kind="ocr",
                confidence=max(
                    0.0,
                    min(
                        1.0,
                        block.confidence,
                    ),
                ),
                metadata={
                    "block_id": block.block_id,
                    "ocr_confidence": (
                        block.confidence
                    ),
                    "ocr_language": (
                        page.ocr_language
                    ),
                    "ocr_dpi": page.ocr_dpi,
                },
            )

            regions.append(region)

            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=block.block_id,
                )
            )

        # ---------------------------------------------------------
        # 7. Comprensión visual de la página completa.
        # ---------------------------------------------------------
        page_visual = dict(page.visual_understanding or {})
        if page_visual:
            region_id = self._stable_id(
                page.page_number,
                "page_visual",
                page_visual.get("object_type", "visual_content"),
            )
            content = str(
                page_visual.get("description")
                or "Contenido visual de página procesado."
            )
            confidence = max(
                0.0,
                min(
                    1.0,
                    float(page_visual.get("visual_confidence", 0.0) or 0.0),
                ),
            )
            region = DocumentRegion(
                region_id=region_id,
                page_number=page.page_number,
                region_type="page_visual",
                content=content,
                source_kind="visual_understanding",
                confidence=confidence,
                metadata=page_visual,
            )
            regions.append(region)
            evidence.append(
                self._evidence_for_region(
                    region,
                    source_id=f"page-{page.page_number}-visual",
                )
            )

        return regions, evidence

    @staticmethod
    def _count_structural_objects(items: tuple[Any, ...]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            object_type = str(
                getattr(item, "object_type", "unknown")
                or "unknown"
            )
            counts[object_type] = counts.get(object_type, 0) + 1
        return counts

    @staticmethod
    def _evidence_for_region(
        region: DocumentRegion,
        *,
        source_id: str,
    ) -> DocumentEvidence:
        """
        Crea evidencia determinista para una región.

        La evidencia apunta a la región, conserva la página, bbox, contenido
        y procedencia, y no intenta inferir significado adicional.
        """
        evidence_id = DocumentKnowledgeBuilder._stable_id(
            region.page_number,
            "evidence",
            region.region_id,
        )

        return DocumentEvidence(
            evidence_id=evidence_id,
            source_kind=region.source_kind,
            source_id=source_id,
            page_number=region.page_number,
            text=region.content,
            bbox=region.bbox,
            confidence=region.confidence,
            metadata={
                "region_id": region.region_id,
                "region_type": region.region_type,
            },
        )

    @staticmethod
    def _stable_id(*parts: object) -> str:
        """
        Genera IDs deterministas.

        El mismo documento procesado con la misma representación física
        produce los mismos IDs, facilitando trazabilidad y comparación.
        """
        raw = "|".join(
            str(part)
            for part in parts
        )

        return sha256(
            raw.encode("utf-8")
        ).hexdigest()[:24]