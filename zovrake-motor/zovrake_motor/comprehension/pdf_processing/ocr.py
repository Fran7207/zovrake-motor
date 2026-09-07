"""Backend OCR para páginas PDF que requieren reconocimiento óptico."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import hashlib
import os
import re
import shutil
from typing import Any

import pypdfium2 as pdfium
import pytesseract
from PIL import Image
from pytesseract import Output


@dataclass(frozen=True)
class OcrTextBlock:
    """Bloque de texto reconocido mediante OCR."""

    text: str
    bbox: tuple[float, float, float, float]
    confidence: float


@dataclass(frozen=True)
class OcrPageResult:
    """Resultado del OCR de una página."""

    text: str
    blocks: tuple[OcrTextBlock, ...]
    confidence: float
    page_number: int
    dpi: int
    language: str
    render_sha256: str = ""
    render_width_px: int | None = None
    render_height_px: int | None = None
    passes_executed: tuple[int, ...] = ()


class OcrProcessor:
    """
    Ejecuta OCR sobre páginas PDF rasterizadas.

    Este componente no modifica el PDF original.

    La ruta del ejecutable Tesseract se resuelve, en orden, mediante:
    1. ``TESSERACT_CMD`` si está definido.
    2. ``tesseract`` disponible en PATH.
    3. Instalación estándar de Windows en Program Files.
    """

    _WINDOWS_TESSERACT_PATHS = (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    )

    def __init__(
        self,
        *,
        dpi: int = 200,
        language: str = "spa+eng",
        psm: int = 6,
        multi_pass: bool = True,
        upscale_factor: float = 1.5,
    ) -> None:
        if dpi <= 0:
            raise ValueError("dpi debe ser mayor que cero.")

        if not language.strip():
            raise ValueError(
                "language no puede estar vacío."
            )

        if psm <= 0:
            raise ValueError("psm debe ser mayor que cero.")
        if upscale_factor < 1.0:
            raise ValueError("upscale_factor debe ser mayor o igual que 1.")

        self._dpi = dpi
        self._language = language
        self._psm = psm
        self._multi_pass = bool(multi_pass)
        self._upscale_factor = float(upscale_factor)
        self._tesseract_cmd = self._resolve_tesseract()

        # Configuramos explícitamente el ejecutable para que el OCR no
        # dependa de que el proceso que ejecuta pytest/Windows haya
        # heredado correctamente el PATH.
        pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd

    @property
    def dpi(self) -> int:
        return self._dpi

    @property
    def language(self) -> str:
        return self._language

    @property
    def psm(self) -> int:
        return self._psm

    @property
    def tesseract_cmd(self) -> str:
        return self._tesseract_cmd

    def process_page(
        self,
        *,
        pdf_bytes: bytes,
        page_number: int,
    ) -> OcrPageResult:
        if not pdf_bytes:
            raise ValueError(
                "No se proporcionaron datos PDF."
            )

        if page_number < 1:
            raise ValueError(
                "page_number debe ser mayor o igual a 1."
            )

        pdf = pdfium.PdfDocument(
            BytesIO(pdf_bytes)
        )

        try:
            page_index = page_number - 1

            if page_index >= len(pdf):
                raise ValueError(
                    f"La página {page_number} no existe."
                )

            page = pdf[page_index]

            scale = self._dpi / 72.0

            bitmap = page.render(
                scale=scale,
            )

            image = bitmap.to_pil()

            try:
                return self._run_ocr(
                    image=image,
                    page_number=page_number,
                )
            finally:
                image.close()

        finally:
            pdf.close()

    def _resolve_tesseract(self) -> str:
        """
        Resuelve el ejecutable real de Tesseract sin depender exclusivamente
        del PATH del proceso actual.
        """
        configured = os.environ.get("TESSERACT_CMD", "").strip()

        if configured:
            configured_path = Path(configured).expanduser()

            if configured_path.is_file():
                return str(configured_path)

            raise FileNotFoundError(
                "TESSERACT_CMD está configurado, pero el ejecutable "
                f"no existe: {configured_path}"
            )

        path_executable = shutil.which("tesseract")

        if path_executable:
            return str(Path(path_executable).resolve())

        for candidate in self._WINDOWS_TESSERACT_PATHS:
            if candidate.is_file():
                return str(candidate)

        raise FileNotFoundError(
            "No se encontró Tesseract OCR. "
            "Instale Tesseract o configure TESSERACT_CMD con la ruta "
            "completa de tesseract.exe. "
            "Ruta estándar esperada en Windows: "
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

    def process_image_bytes(
        self,
        *,
        image_bytes: bytes,
        page_number: int,
    ) -> OcrPageResult:
        """Ejecuta OCR directamente sobre una imagen embebida del PDF."""
        if not image_bytes:
            raise ValueError("No se proporcionaron datos de imagen.")

        image = Image.open(BytesIO(image_bytes))
        converted = None
        try:
            image.load()
            converted = image.convert("RGB")
            return self._run_ocr(
                image=converted,
                page_number=page_number,
            )
        finally:
            if converted is not None:
                converted.close()
            image.close()

    def _run_ocr(
        self,
        *,
        image: Image.Image,
        page_number: int,
    ) -> OcrPageResult:
        render_sha256 = self._image_sha256(image)
        passes = [self._psm]
        if self._multi_pass:
            for candidate in (3, 11):
                if candidate != self._psm:
                    passes.append(candidate)

        aggregate: list[OcrTextBlock] = []
        all_confidences: list[float] = []
        used_passes: list[int] = []

        prepared = self._prepare_image(image)
        try:
            for psm in passes:
                result = self._run_single_pass(
                    image=prepared,
                    page_number=page_number,
                    psm=psm,
                )
                used_passes.append(psm)
                all_confidences.extend(
                    block.confidence for block in result.blocks
                )
                aggregate.extend(result.blocks)

                # Un pass exitoso con texto abundante ya cubre buena parte
                # de la página; los demás passes siguen siendo necesarios para
                # descubrir regiones que el primer layout haya omitido.

        finally:
            if prepared is not image:
                prepared.close()

        merged = self._merge_blocks(aggregate)
        text = " ".join(
            block.text
            for block in merged
            if block.text.strip()
        ).strip()
        confidence = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences
            else 0.0
        )

        return OcrPageResult(
            text=text,
            blocks=tuple(merged),
            confidence=round(confidence, 4),
            page_number=page_number,
            dpi=self._dpi,
            language=self._language,
            render_sha256=render_sha256,
            render_width_px=image.width,
            render_height_px=image.height,
            passes_executed=tuple(used_passes),
        )

    def _run_single_pass(
        self,
        *,
        image: Image.Image,
        page_number: int,
        psm: int,
    ) -> OcrPageResult:
        config = f"--psm {psm}"
        data: dict[str, Any] = pytesseract.image_to_data(
            image,
            lang=self._language,
            config=config,
            output_type=Output.DICT,
        )
        blocks: list[OcrTextBlock] = []
        confidences: list[float] = []
        scale = 72.0 / self._dpi / self._upscale_factor

        for index, raw_text in enumerate(data.get("text", ())):
            text = str(raw_text or "").strip()
            if not text:
                continue
            try:
                confidence = float(data["conf"][index])
            except (TypeError, ValueError):
                continue
            if confidence < 0:
                continue
            x = float(data["left"][index])
            y = float(data["top"][index])
            width = float(data["width"][index])
            height = float(data["height"][index])
            blocks.append(
                OcrTextBlock(
                    text=text,
                    bbox=(
                        x * scale,
                        y * scale,
                        (x + width) * scale,
                        (y + height) * scale,
                    ),
                    confidence=confidence / 100.0,
                )
            )
            confidences.append(confidence / 100.0)

        return OcrPageResult(
            text=" ".join(block.text for block in blocks).strip(),
            blocks=tuple(blocks),
            confidence=(sum(confidences) / len(confidences) if confidences else 0.0),
            page_number=page_number,
            dpi=self._dpi,
            language=self._language,
            render_sha256="",
            render_width_px=image.width,
            render_height_px=image.height,
            passes_executed=(psm,),
        )

    def _prepare_image(self, image: Image.Image) -> Image.Image:
        rgb = image.convert("RGB")
        if self._upscale_factor == 1.0:
            return rgb
        width = max(1, round(rgb.width * self._upscale_factor))
        height = max(1, round(rgb.height * self._upscale_factor))
        return rgb.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def _image_sha256(image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return hashlib.sha256(buffer.getvalue()).hexdigest()

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\W+", " ", value.casefold()).strip()

    @classmethod
    def _merge_blocks(cls, blocks: list[OcrTextBlock]) -> list[OcrTextBlock]:
        merged: list[OcrTextBlock] = []
        for block in blocks:
            normalized = cls._normalize_text(block.text)
            duplicate_index = None
            for idx, existing in enumerate(merged):
                if cls._normalize_text(existing.text) != normalized:
                    continue
                ex = existing.bbox
                bx = block.bbox
                if ex is None or bx is None:
                    duplicate_index = idx
                    break
                overlap = cls._bbox_iou(ex, bx)
                if overlap >= 0.35:
                    duplicate_index = idx
                    break
            if duplicate_index is None:
                merged.append(block)
                continue
            existing = merged[duplicate_index]
            if block.confidence > existing.confidence:
                merged[duplicate_index] = block
        return merged

    @staticmethod
    def _bbox_iou(
        a: tuple[float, float, float, float],
        b: tuple[float, float, float, float],
    ) -> float:
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        ix0, iy0 = max(ax0, bx0), max(ay0, by0)
        ix1, iy1 = min(ax1, bx1), min(ay1, by1)
        iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
        inter = iw * ih
        area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
        area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0
