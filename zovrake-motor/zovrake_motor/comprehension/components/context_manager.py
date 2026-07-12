"""Gestor del Contexto Documental — integración con el Context Integration Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.context_integration.engine import ContextIntegrationEngine
from zovrake_motor.comprehension.context_integration.integration import ContextIntegrationMotorIntegration
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest, ContextIntegrationResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentContextManager(ComprehensionComponentPort):
    """
    Gestor del Context Integration Engine (CIE).

    Responsabilidad única: integrar el contexto del requerimiento con el
    Modelo Documental Interno sin modificar la información documental.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ContextIntegrationEngine | None = None,
    ) -> None:
        self._engine = engine or ContextIntegrationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "context_manager"

    @property
    def component_label(self) -> str:
        return "Gestor del Contexto"

    @property
    def engine(self) -> ContextIntegrationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def integrate(
        self,
        request: ContextIntegrationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ContextIntegrationResult:
        if integration is not None and record_traceability:
            bridge = ContextIntegrationMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_integration(
                request.process_id,
                document_id=request.model_result.document_id,
            )

        result = self._engine.integrate(request)

        if integration is not None and record_traceability:
            bridge = ContextIntegrationMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_integration(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
