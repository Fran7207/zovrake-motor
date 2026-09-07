"""Comprensión visual determinista y local para contenido PDF.

Esta capa NO usa servicios ni modelos de IA externos. Combina visión
computacional clásica, características de imagen, OCR ya ejecutado y
reglas semánticas reproducibles para transformar evidencia visual en
observaciones estructuradas y trazables.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any
import hashlib
import math
import re

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class VisualUnderstandingResult:
    """Resultado estructurado de la inspección visual local."""

    object_type: str
    description: str
    detected_text: str = ""
    semantic_hints: tuple[str, ...] = ()
    detected_features: tuple[str, ...] = ()
    qr_codes: tuple[str, ...] = ()
    visual_confidence: float = 0.0
    analysis_status: str = "completed"
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "description": self.description,
            "detected_text": self.detected_text,
            "semantic_hints": list(self.semantic_hints),
            "detected_features": list(self.detected_features),
            "qr_codes": list(self.qr_codes),
            "visual_confidence": self.visual_confidence,
            "analysis_status": self.analysis_status,
            "metrics": dict(self.metrics),
        }


class MultimodalVisualUnderstandingEngine:
    """Analizador visual local, reproducible y extensible de ZOVRAKE.

    ENGINE_VERSION = "1.0-local-vision"

    No llama a ningún proveedor de IA ni a ningún modelo remoto. Su propósito
    es convertir píxeles en evidencia visual estructurada que después pueda
    ser razonada por las capas documentales de ZOVRAKE.
    """

    _SEMANTIC_PATTERNS = {
        "supplier_identity": re.compile(
            r"\b(?:ruc|raz[oó]n\s+social|empresa|corporaci[oó]n|proveedor|s\.?a\.?c?\.?|s\.?r\.?l\.?)\b",
            re.IGNORECASE,
        ),
        "commercial_data": re.compile(
            r"\b(?:precio|p\.?\s*/?\.?unit|unitario|total|subtotal|igv|cantidad|cant\.?|unid\.?|importe|moneda|soles|usd|d[oó]lares)\b",
            re.IGNORECASE,
        ),
        "product_identity": re.compile(
            r"\b(?:modelo|marca|c[oó]digo|sku|serie|producto|material|tipo|medida|presentaci[oó]n)\b",
            re.IGNORECASE,
        ),
        "approval_or_signature": re.compile(
            r"\b(?:firma|firmado|aprobado|aprobaci[oó]n|sello|visto\s+bueno|vo\.?bo\.?)\b",
            re.IGNORECASE,
        ),
    }

    def analyze_image_bytes(
        self,
        *,
        image_bytes: bytes,
        detected_text: str = "",
        page_number: int | None = None,
        source_id: str = "",
    ) -> VisualUnderstandingResult:
        """Analiza una imagen embebida sin depender de texto previo."""
        if not image_bytes:
            return VisualUnderstandingResult(
                object_type="unknown",
                description="No hay datos binarios disponibles para analizar la imagen.",
                analysis_status="unavailable",
            )
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            result = self.analyze_pil_image(
                image=image,
                detected_text=detected_text,
                source_id=source_id,
                page_number=page_number,
            )
            image.close()
            return result
        except Exception as exc:
            return VisualUnderstandingResult(
                object_type="unknown",
                description="No fue posible decodificar la imagen para análisis visual.",
                analysis_status="failed",
                metrics={"error": str(exc)},
            )

    def analyze_pil_image(
        self,
        *,
        image: Image.Image,
        detected_text: str = "",
        page_number: int | None = None,
        source_id: str = "",
    ) -> VisualUnderstandingResult:
        """Extrae características visuales y relaciones observables."""
        if image.width <= 0 or image.height <= 0:
            return VisualUnderstandingResult(
                object_type="unknown",
                description="La imagen no tiene dimensiones válidas.",
                analysis_status="failed",
            )

        rgb = np.asarray(image.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        edge_density = float(np.count_nonzero(edges)) / float(edges.size or 1)
        gray_std = float(np.std(gray))
        color_std = float(np.std(rgb.reshape(-1, 3), axis=0).mean())
        dark_ratio = float(np.mean(gray < 75))
        bright_ratio = float(np.mean(gray > 220))
        entropy = self._entropy(gray)
        aspect_ratio = image.width / image.height

        horizontal_lines, vertical_lines, diagonal_lines = self._line_features(edges)
        rect_count = self._rectangle_count(edges)
        qr_codes = self._decode_qr_codes(rgb)

        normalized_text = self._normalize_text(detected_text)
        text_length = len(normalized_text)
        text_density = min(1.0, text_length / max(1.0, image.width * image.height / 3500.0))

        semantic_hints = self._semantic_hints(normalized_text)
        detected_features: list[str] = []
        if text_length:
            detected_features.append("text_present")
        if qr_codes:
            detected_features.append("qr_code")
        if edge_density >= 0.10:
            detected_features.append("high_edge_density")
        if horizontal_lines + vertical_lines >= 4:
            detected_features.append("structured_lines")
        if rect_count >= 2:
            detected_features.append("rectangular_regions")
        if color_std >= 35:
            detected_features.append("color_variation")
        if diagonal_lines >= 3:
            detected_features.append("diagonal_geometry")

        object_type, confidence, rationale = self._classify(
            text_length=text_length,
            text_density=text_density,
            edge_density=edge_density,
            gray_std=gray_std,
            color_std=color_std,
            entropy=entropy,
            horizontal_lines=horizontal_lines,
            vertical_lines=vertical_lines,
            diagonal_lines=diagonal_lines,
            rect_count=rect_count,
            qr_codes=qr_codes,
            semantic_hints=semantic_hints,
        )

        description = self._description(
            object_type=object_type,
            rationale=rationale,
            detected_text=detected_text,
            semantic_hints=semantic_hints,
        )

        return VisualUnderstandingResult(
            object_type=object_type,
            description=description,
            detected_text=detected_text.strip(),
            semantic_hints=tuple(semantic_hints),
            detected_features=tuple(detected_features),
            qr_codes=tuple(qr_codes),
            visual_confidence=round(max(0.0, min(1.0, confidence)), 4),
            analysis_status="completed",
            metrics={
                "page_number": page_number,
                "source_id": source_id,
                "width_px": image.width,
                "height_px": image.height,
                "aspect_ratio": round(aspect_ratio, 4),
                "edge_density": round(edge_density, 6),
                "gray_std": round(gray_std, 4),
                "color_std": round(color_std, 4),
                "dark_ratio": round(dark_ratio, 4),
                "bright_ratio": round(bright_ratio, 4),
                "entropy": round(entropy, 4),
                "text_length": text_length,
                "text_density": round(text_density, 6),
                "horizontal_lines": horizontal_lines,
                "vertical_lines": vertical_lines,
                "diagonal_lines": diagonal_lines,
                "rectangle_count": rect_count,
                "content_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
            },
        )

    @classmethod
    def _classify(
        cls,
        *,
        text_length: int,
        text_density: float,
        edge_density: float,
        gray_std: float,
        color_std: float,
        entropy: float,
        horizontal_lines: int,
        vertical_lines: int,
        diagonal_lines: int,
        rect_count: int,
        qr_codes: list[str],
        semantic_hints: list[str],
    ) -> tuple[str, float, tuple[str, ...]]:
        if qr_codes:
            return "qr_code", 0.99, ("se decodificaron uno o más códigos QR",)

        structured = horizontal_lines + vertical_lines + rect_count
        commercial = "commercial_data" in semantic_hints
        identity = "supplier_identity" in semantic_hints or "product_identity" in semantic_hints
        approval = "approval_or_signature" in semantic_hints

        if approval and text_length:
            return "stamp_or_signature", 0.82, ("el texto visual contiene señales de sello/firma/aprobación",)
        if text_length and commercial and structured >= 5:
            return "commercial_graphic", 0.88, ("texto comercial combinado con estructura geométrica",)
        if text_length and identity and color_std < 28 and edge_density < 0.16:
            return "logo_or_identity_graphic", 0.78, ("texto identificativo con variación cromática moderada",)
        if structured >= 12 and text_length >= 20 and diagonal_lines >= 2:
            return "diagram_or_chart", 0.74, ("alta densidad de geometría estructurada y texto",)
        if color_std >= 38 and entropy >= 5.2 and edge_density >= 0.08:
            return "photograph_or_visual", 0.76, ("alta variación de color, entropía y bordes",)
        if text_length >= 30 and text_density >= 0.15 and color_std < 30:
            return "text_document_image", 0.86, ("imagen dominada por texto de bajo color",)
        if structured >= 6 and gray_std < 55:
            return "diagram_or_form", 0.68, ("geometría organizada compatible con formulario o diagrama",)
        return "visual_content", 0.52, ("contenido visual capturado sin evidencia suficiente para una categoría más específica",)

    @staticmethod
    def _description(
        *,
        object_type: str,
        rationale: tuple[str, ...],
        detected_text: str,
        semantic_hints: list[str],
    ) -> str:
        label = object_type.replace("_", " ")
        parts = [f"Contenido visual clasificado provisionalmente como {label}."]
        if rationale:
            parts.append(rationale[0] + ".")
        if semantic_hints:
            parts.append("Se detectan señales semánticas: " + ", ".join(semantic_hints) + ".")
        if detected_text.strip():
            preview = re.sub(r"\s+", " ", detected_text.strip())
            if len(preview) > 240:
                preview = preview[:237] + "..."
            parts.append(f"Texto visible detectado: {preview}")
        return " ".join(parts)

    @classmethod
    def _semantic_hints(cls, text: str) -> list[str]:
        return [
            key
            for key, pattern in cls._SEMANTIC_PATTERNS.items()
            if pattern.search(text)
        ]

    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

    @staticmethod
    def _entropy(gray: np.ndarray) -> float:
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
        probabilities = histogram / max(float(histogram.sum()), 1.0)
        probabilities = probabilities[probabilities > 0]
        return float(-(probabilities * np.log2(probabilities)).sum())

    @staticmethod
    def _line_features(edges: np.ndarray) -> tuple[int, int, int]:
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180.0, threshold=40, minLineLength=30, maxLineGap=6)
        if lines is None:
            return 0, 0, 0
        horizontal = vertical = diagonal = 0
        for line in lines[:, 0]:
            x1, y1, x2, y2 = map(int, line)
            dx, dy = abs(x2 - x1), abs(y2 - y1)
            angle = math.degrees(math.atan2(dy, max(dx, 1)))
            if angle <= 10:
                horizontal += 1
            elif angle >= 80:
                vertical += 1
            elif 15 <= angle <= 75:
                diagonal += 1
        return horizontal, vertical, diagonal

    @staticmethod
    def _rectangle_count(edges: np.ndarray) -> int:
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        count = 0
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter <= 0:
                continue
            polygon = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue
            x, y, width, height = cv2.boundingRect(polygon)
            if width >= 20 and height >= 20:
                count += 1
        return min(count, 100)

    @staticmethod
    def _decode_qr_codes(rgb: np.ndarray) -> list[str]:
        decoder = cv2.QRCodeDetector()
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        values: list[str] = []
        try:
            ok, decoded, _, _ = decoder.detectAndDecodeMulti(rgb)
            if ok:
                values.extend(str(v).strip() for v in decoded if str(v).strip())
        except Exception:
            pass
        if not values:
            try:
                value, _, _ = decoder.detectAndDecode(gray)
                if value:
                    values.append(str(value).strip())
            except Exception:
                pass
        return list(dict.fromkeys(values))
