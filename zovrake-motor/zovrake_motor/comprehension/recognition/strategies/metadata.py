"""Estrategia de reconocimiento por metadatos."""

from __future__ import annotations

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, StrategyRecognitionResult
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.strategies.base import recognized_result, unrecognized_result


class MetadataRecognitionStrategy(RecognitionStrategyPort):
    """Identifica el formato mediante metadatos explícitos del documento."""

    @property
    def strategy_type(self) -> RecognitionStrategyType:
        return RecognitionStrategyType.METADATA

    @property
    def strategy_name(self) -> str:
        return "metadata_strategy"

    @property
    def strategy_label(self) -> str:
        return "Reconocimiento por Metadatos"

    def recognize(self, request: DocumentRecognitionRequest) -> StrategyRecognitionResult:
        raw_format = request.format_type or str(request.metadata.get("format_type", "")).strip()
        if not raw_format:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation="Metadato de formato no proporcionado",
            )

        format_type = DocumentFormatType.from_value(raw_format)
        if format_type is None:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation=f"Formato en metadatos no reconocido: {raw_format}",
            )

        return recognized_result(
            strategy_type=self.strategy_type,
            strategy_name=self.strategy_name,
            format_type=format_type,
            confidence=0.95,
            observation=f"Formato identificado por metadatos: {raw_format}",
        )
