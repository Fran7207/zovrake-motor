"""Utilidades compartidas para estrategias de reconocimiento."""

from __future__ import annotations

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.recognition.enums import RecognitionStrategyType
from zovrake_motor.comprehension.recognition.models import StrategyRecognitionResult


def recognized_result(
    *,
    strategy_type: RecognitionStrategyType,
    strategy_name: str,
    format_type: DocumentFormatType,
    confidence: float,
    observation: str,
) -> StrategyRecognitionResult:
    return StrategyRecognitionResult(
        strategy_type=strategy_type,
        strategy_name=strategy_name,
        recognized=True,
        format_type=format_type,
        confidence=confidence,
        technical_observations=(observation,),
    )


def unrecognized_result(
    *,
    strategy_type: RecognitionStrategyType,
    strategy_name: str,
    observation: str = "Sin coincidencia — estrategia preparada sin lectura de archivo",
) -> StrategyRecognitionResult:
    return StrategyRecognitionResult(
        strategy_type=strategy_type,
        strategy_name=strategy_name,
        recognized=False,
        format_type=None,
        confidence=0.0,
        technical_observations=(observation,),
    )
