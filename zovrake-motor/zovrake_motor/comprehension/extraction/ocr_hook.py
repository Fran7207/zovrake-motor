"""Punto de integración preparado para OCR."""

from __future__ import annotations

from typing import Any

from zovrake_motor.config.categories.comprehension import DocumentExtractionSettings


class OcrIntegrationPoint:
    """
    Punto de integración para el módulo OCR futuro.

    No ejecuta OCR en esta etapa — únicamente prepara la arquitectura.
    """

    def __init__(self, *, settings: DocumentExtractionSettings | None = None) -> None:
        self._settings = settings or DocumentExtractionSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.ocr_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.ocr_enabled

    def can_execute(self) -> bool:
        return self.is_prepared and self.is_enabled

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "ocr_enabled": self.is_enabled,
            "can_execute": self.can_execute(),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_for_future_execution(self) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "OCR preparado — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
