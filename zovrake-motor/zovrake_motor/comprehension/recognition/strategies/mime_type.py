"""Estrategia de reconocimiento por tipo MIME."""

from __future__ import annotations

from zovrake_motor.comprehension.recognition.catalog import FormatCatalog
from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, StrategyRecognitionResult
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.strategies.base import recognized_result, unrecognized_result


class MimeTypeRecognitionStrategy(RecognitionStrategyPort):
    """Identifica el formato mediante el tipo MIME disponible en metadatos."""

    @property
    def strategy_type(self) -> RecognitionStrategyType:
        return RecognitionStrategyType.MIME_TYPE

    @property
    def strategy_name(self) -> str:
        return "mime_type_strategy"

    @property
    def strategy_label(self) -> str:
        return "Reconocimiento por MIME"

    def recognize(self, request: DocumentRecognitionRequest) -> StrategyRecognitionResult:
        mime_type = request.mime_type or str(request.metadata.get("mime_type", "")).strip()
        if not mime_type:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation="Tipo MIME no proporcionado",
            )

        format_type = FormatCatalog.format_from_mime(mime_type)
        if format_type is None:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation=f"Tipo MIME no reconocido: {mime_type}",
            )

        return recognized_result(
            strategy_type=self.strategy_type,
            strategy_name=self.strategy_name,
            format_type=format_type,
            confidence=0.85,
            observation=f"Formato identificado por MIME: {mime_type}",
        )
