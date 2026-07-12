"""Comparative Validation Framework — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.comparative_validation_framework.engine import (
    ComparativeValidationFrameworkCore,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.integration import (
    ComparativeValidationMotorIntegration,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
    ComparativeModelValidationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeValidationFramework(ComparativeTablesComponentPort):
    """
    Gestor del Comparative Validation Framework (CVF).

    Responsabilidad única: validar Modelos Comparativos Definitivos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparativeValidationFrameworkCore | None = None,
    ) -> None:
        self._engine = engine or ComparativeValidationFrameworkCore(
            config_provider=config_provider,
        )
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparative_validation_framework"

    @property
    def component_label(self) -> str:
        return "Comparative Validation Framework"

    @property
    def engine(self) -> ComparativeValidationFrameworkCore:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def validate(
        self,
        request: ComparativeModelValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeModelValidationResult:
        definitive_catalog_id = str(request.definitive_catalog.get("catalog_id", ""))
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparativeValidationMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_comparative_model_validation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                definitive_catalog_id=definitive_catalog_id,
            )

        result = self._engine.validate(request)

        if integration is not None and record_traceability:
            bridge = ComparativeValidationMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_comparative_model_validation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
