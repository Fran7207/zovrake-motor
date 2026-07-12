"""Estrategia de reconocimiento por firma de archivo (magic number)."""

from __future__ import annotations

from zovrake_motor.comprehension.recognition.catalog import FormatCatalog
from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, StrategyRecognitionResult
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.strategies.base import recognized_result, unrecognized_result


class MagicNumberRecognitionStrategy(RecognitionStrategyPort):
    """
    Identifica el formato mediante firma del archivo en metadatos.

    Sin lectura binaria del archivo en esta etapa.
    """

    @property
    def strategy_type(self) -> RecognitionStrategyType:
        return RecognitionStrategyType.MAGIC_NUMBER

    @property
    def strategy_name(self) -> str:
        return "magic_number_strategy"

    @property
    def strategy_label(self) -> str:
        return "Reconocimiento por Magic Number"

    def recognize(self, request: DocumentRecognitionRequest) -> StrategyRecognitionResult:
        signature = (
            request.file_signature
            or str(request.metadata.get("magic_number", "")).strip()
            or str(request.metadata.get("file_signature", "")).strip()
        )
        if not signature:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation="Firma de archivo no proporcionada en metadatos",
            )

        format_type = FormatCatalog.format_from_magic(signature)
        if format_type is None:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation=f"Firma no reconocida: {signature}",
            )

        return recognized_result(
            strategy_type=self.strategy_type,
            strategy_name=self.strategy_name,
            format_type=format_type,
            confidence=0.98,
            observation=f"Formato identificado por firma: {signature}",
        )
