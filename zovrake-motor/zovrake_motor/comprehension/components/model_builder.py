"""Constructor del Modelo Interno — integración con el IDMB."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.internal_model.engine import InternalDocumentModelBuilder
from zovrake_motor.comprehension.internal_model.integration import InternalModelMotorIntegration
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalModelBuildResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class InternalModelBuilder(ComprehensionComponentPort):
    """
    Gestor del Internal Document Model Builder (IDMB).

    Responsabilidad única: construir el Modelo Documental Interno definitivo
    a partir de la Representación Canónica.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: InternalDocumentModelBuilder | None = None,
    ) -> None:
        self._engine = engine or InternalDocumentModelBuilder(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "internal_model_builder"

    @property
    def component_label(self) -> str:
        return "Constructor del Modelo Interno"

    @property
    def engine(self) -> InternalDocumentModelBuilder:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: InternalModelBuildRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> InternalModelBuildResult:
        if integration is not None and record_traceability:
            bridge = InternalModelMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_model_build(
                request.process_id,
                document_id=request.canonical_result.document_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = InternalModelMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_model_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
