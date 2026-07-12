"""Comparative Domain Model Builder — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.comparative_domain_model.engine import ComparativeDomainModelBuilderEngine
from zovrake_motor.classification.comparative_domain_model.integration import (
    ComparativeDomainModelMotorIntegration,
)
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
    ComparativeDomainModelBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeDomainModelBuilder(ClassificationComponentPort):
    """
    Gestor del Comparative Domain Model Builder (CDMB).

    Responsabilidad única: construir el Modelo Comparativo de Dominio.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparativeDomainModelBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ComparativeDomainModelBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparative_domain_model_builder"

    @property
    def component_label(self) -> str:
        return "Comparative Domain Model Builder"

    @property
    def engine(self) -> ComparativeDomainModelBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparativeDomainModelBuildRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeDomainModelBuildResult:
        catalog_id = str(request.context_association_catalog.get("catalog_id", ""))
        document_id = str(request.context_association_catalog.get("document_id", ""))
        model_id = str(request.context_association_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparativeDomainModelMotorIntegration.from_classification_integration(integration)
            bridge.begin_comparative_domain_model_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                context_association_catalog_id=catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = ComparativeDomainModelMotorIntegration.from_classification_integration(integration)
            bridge.complete_comparative_domain_model_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
