"""Resolución del mejor resultado de reconocimiento."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.recognition.catalog import FormatCatalog
from zovrake_motor.comprehension.recognition.enums import RecognitionConfidenceLevel
from zovrake_motor.comprehension.recognition.models import (
    DocumentRecognitionRequest,
    DocumentRecognitionResult,
    StrategyRecognitionResult,
)
from zovrake_motor.comprehension.recognition.registry import RecognitionStrategyRegistry
from zovrake_motor.config.categories.comprehension import DocumentRecognitionSettings


class RecognitionResolver:
    """
    Consolida resultados de estrategias y determina el reconocimiento final.

    Selecciona la estrategia con mayor confianza sin leer contenido del documento.
    """

    def __init__(
        self,
        registry: RecognitionStrategyRegistry,
        *,
        settings: DocumentRecognitionSettings | None = None,
    ) -> None:
        self._registry = registry
        self._settings = settings or DocumentRecognitionSettings.default()

    def resolve(self, request: DocumentRecognitionRequest) -> DocumentRecognitionResult:
        strategy_results = [strategy.recognize(request) for strategy in self._registry.all_strategies()]
        best = self._select_best(strategy_results)

        if best is None or not best.recognized:
            return DocumentRecognitionResult(
                process_id=request.process_id,
                document_id=request.document_id,
                recognized=False,
                identified_format=None,
                confidence=0.0,
                confidence_level=RecognitionConfidenceLevel.LOW,
                strategy_used=None,
                strategy_type=None,
                suggested_adapter=None,
                adapter_selection=None,
                technical_observations=("Formato no identificado por ninguna estrategia",),
                strategies_executed=len(strategy_results),
            )

        suggested_adapter = FormatCatalog.suggested_adapter(best.format_type) if best.format_type else None
        observations = tuple(
            observation
            for result in strategy_results
            for observation in result.technical_observations
        )

        return DocumentRecognitionResult(
            process_id=request.process_id,
            document_id=request.document_id,
            recognized=True,
            identified_format=best.format_type,
            confidence=best.confidence,
            confidence_level=RecognitionConfidenceLevel.from_score(best.confidence),
            strategy_used=best.strategy_name,
            strategy_type=best.strategy_type,
            suggested_adapter=suggested_adapter,
            adapter_selection=None,
            technical_observations=observations,
            strategies_executed=len(strategy_results),
        )

    def _select_best(
        self,
        results: list[StrategyRecognitionResult],
    ) -> StrategyRecognitionResult | None:
        recognized = [
            result
            for result in results
            if result.recognized
            and result.format_type is not None
            and self._is_supported(result.format_type)
        ]
        if not recognized:
            return None

        best = max(recognized, key=lambda item: item.confidence)
        if best.confidence < self._settings.min_confidence_threshold:
            return None
        return best

    def _is_supported(self, format_type: DocumentFormatType) -> bool:
        return format_type.value in self._settings.supported_formats
