"""Comparable Group Builder — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.comparable_group_builder.engine import ComparableGroupBuilderEngine
from zovrake_motor.classification.comparable_group_builder.integration import ComparableGroupMotorIntegration
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupBuildRequest,
    ComparableGroupBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparableGroupBuilder(ClassificationComponentPort):
    """
    Gestor del Comparable Group Builder (CGB).

    Responsabilidad única: construir Grupos Comparables a partir del Modelo de Equivalencias.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparableGroupBuilderEngine | None = None,
    ) -> None:
        self._engine = engine or ComparableGroupBuilderEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparable_group_builder"

    @property
    def component_label(self) -> str:
        return "Comparable Group Builder"

    @property
    def engine(self) -> ComparableGroupBuilderEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def build(
        self,
        request: ComparableGroupBuildRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparableGroupBuildResult:
        catalog_id = str(request.equivalence_catalog.get("catalog_id", ""))
        document_id = str(request.equivalence_catalog.get("document_id", ""))
        model_id = str(request.equivalence_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparableGroupMotorIntegration.from_classification_integration(integration)
            bridge.begin_comparable_group_build(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                equivalence_catalog_id=catalog_id,
            )

        result = self._engine.build(request)

        if integration is not None and record_traceability:
            bridge = ComparableGroupMotorIntegration.from_classification_integration(integration)
            bridge.complete_comparable_group_build(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
