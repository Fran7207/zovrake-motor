"""Identificador de Formato — integración con el Document Recognition Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.adapters.framework import DocumentAdapterFramework
from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.recognition.engine import DocumentRecognitionEngine
from zovrake_motor.comprehension.recognition.integration import RecognitionMotorIntegration
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, DocumentRecognitionResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class FormatIdentifier(ComprehensionComponentPort):
    """
    Gestor del Document Recognition Engine (DRE).

    Responsabilidad única: identificar el tipo documental y preparar
    la selección del adaptador correspondiente.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: DocumentRecognitionEngine | None = None,
    ) -> None:
        self._engine = engine or DocumentRecognitionEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "format_identifier"

    @property
    def component_label(self) -> str:
        return "Identificador de Formato"

    @property
    def engine(self) -> DocumentRecognitionEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def recognize(
        self,
        request: DocumentRecognitionRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        adapter_framework: DocumentAdapterFramework | None = None,
        record_traceability: bool = True,
    ) -> DocumentRecognitionResult:
        if integration is not None and record_traceability:
            bridge = RecognitionMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_recognition(request.process_id, document_id=request.document_id)

        result = self._engine.recognize(request)
        result = self._engine.prepare_adapter_selection(
            result,
            adapter_framework=adapter_framework,
        )

        if integration is not None and record_traceability:
            bridge = RecognitionMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_recognition(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
