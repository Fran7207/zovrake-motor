"""Estrategia de reconocimiento por extensión de archivo."""

from __future__ import annotations

from pathlib import PurePosixPath

from zovrake_motor.comprehension.recognition.catalog import FormatCatalog
from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, StrategyRecognitionResult
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.strategies.base import recognized_result, unrecognized_result


class ExtensionRecognitionStrategy(RecognitionStrategyPort):
    """Identifica el formato mediante la extensión del archivo."""

    @property
    def strategy_type(self) -> RecognitionStrategyType:
        return RecognitionStrategyType.EXTENSION

    @property
    def strategy_name(self) -> str:
        return "extension_strategy"

    @property
    def strategy_label(self) -> str:
        return "Reconocimiento por Extensión"

    def recognize(self, request: DocumentRecognitionRequest) -> StrategyRecognitionResult:
        if not request.file_name:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation="Nombre de archivo no proporcionado",
            )

        extension = PurePosixPath(request.file_name).suffix.lower()
        format_type = FormatCatalog.format_from_extension(extension)
        if format_type is None:
            return unrecognized_result(
                strategy_type=self.strategy_type,
                strategy_name=self.strategy_name,
                observation=f"Extensión no reconocida: {extension}",
            )

        return recognized_result(
            strategy_type=self.strategy_type,
            strategy_name=self.strategy_name,
            format_type=format_type,
            confidence=0.9,
            observation=f"Formato identificado por extensión: {extension}",
        )
