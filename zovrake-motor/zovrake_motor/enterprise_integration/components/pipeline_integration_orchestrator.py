"""Componente Pipeline Integration Orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.pio.orchestrator import PipelineIntegrationOrchestrator

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class PipelineIntegrationOrchestratorComponent(EnterpriseIntegrationComponentPort):
    """
    Componente registrado del PIO.

    Ningún otro componente puede realizar orquestación del Pipeline.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration | None = None,
        orchestrator: PipelineIntegrationOrchestrator | None = None,
    ) -> None:
        if integration is None and orchestrator is None:
            raise ValueError("Se requiere integration u orchestrator")
        self._integration = integration
        self._orchestrator = orchestrator or PipelineIntegrationOrchestrator(
            integration=integration,  # type: ignore[arg-type]
        )

    @property
    def component_name(self) -> str:
        return "pipeline_integration_orchestrator"

    @property
    def component_label(self) -> str:
        return "Pipeline Integration Orchestrator"

    @property
    def orchestrator(self) -> PipelineIntegrationOrchestrator:
        return self._orchestrator

    def initialize(self) -> None:
        self._orchestrator.initialize()

    def is_ready(self) -> bool:
        return self._orchestrator.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["orchestrator"] = self._orchestrator.snapshot()
        base["traceability"] = self._orchestrator.traceability.snapshot()
        return base
