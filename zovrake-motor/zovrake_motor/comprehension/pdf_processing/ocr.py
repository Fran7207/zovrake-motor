"""Backend OCR para páginas PDF que requieren reconocimiento óptico."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import os
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
    ) -> None:
        if dpi <= 0:
            raise ValueError("dpi debe ser mayor que cero.")

        if not language.strip():
            raise ValueError(
                "language no puede estar vacío."
            )

        if psm <= 0:
            raise ValueError("psm debe ser mayor que cero.")

        self._dpi = dpi
        self._language = language
        self._psm = psm
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

    def _run_ocr(
        self,
        *,
        image: Image.Image,
        page_number: int,
    ) -> OcrPageResult:
        config = f"--psm {self._psm}"

        data: dict[str, Any] = pytesseract.image_to_data(
            image,
            lang=self._language,
            config=config,
            output_type=Output.DICT,
        )

        blocks: list[OcrTextBlock] = []
        text_parts: list[str] = []
        confidences: list[float] = []

        for index, raw_text in enumerate(
            data.get("text", ())
        ):
            text = str(raw_text or "").strip()

            if not text:
                continue

            raw_confidence = data["conf"][index]

            try:
                confidence = float(
                    raw_confidence
                )
            except (TypeError, ValueError):
                continue

            if confidence < 0:
                continue

            x = float(data["left"][index])
            y = float(data["top"][index])
            width = float(data["width"][index])
            height = float(data["height"][index])

            # Convertimos las coordenadas de píxeles
            # a puntos PDF (72 puntos por pulgada).
            scale = 72.0 / self._dpi

            bbox = (
                x * scale,
                y * scale,
                (x + width) * scale,
                (y + height) * scale,
            )

            blocks.append(
                OcrTextBlock(
                    text=text,
                    bbox=bbox,
                    confidence=confidence / 100.0,
                )
            )

            text_parts.append(text)
            confidences.append(
                confidence / 100.0
            )

        text = " ".join(text_parts).strip()

        document_confidence = (
            sum(confidences) / len(confidences)
            if confidences
            else 0.0
        )

        return OcrPageResult(
            text=text,
            blocks=tuple(blocks),
            confidence=round(
                document_confidence,
                4,
            ),
            page_number=page_number,
            dpi=self._dpi,
            language=self._language,
        )
