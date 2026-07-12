"""Comparative Quality Framework — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.comparative_quality_framework.engine import (
    ComparativeQualityFrameworkCore,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.integration import (
    ComparativeQualityMotorIntegration,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeQualityFramework(ComparativeTablesComponentPort):
    """
    Gestor del Comparative Quality Framework (CQF).

    Responsabilidad única: auditar calidad integral del PM6.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ComparativeQualityFrameworkCore | None = None,
    ) -> None:
        self._engine = engine or ComparativeQualityFrameworkCore(
            config_provider=config_provider,
        )
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "comparative_quality_framework"

    @property
    def component_label(self) -> str:
        return "Comparative Quality Framework"

    @property
    def engine(self) -> ComparativeQualityFrameworkCore:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def audit(
        self,
        request: ComparativeQualityValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ComparativeQualityValidationResult:
        definitive_catalog_id = str(request.definitive_catalog.get("catalog_id", ""))
        document_id = str(request.definitive_catalog.get("document_id", ""))
        model_id = str(request.definitive_catalog.get("model_id", ""))
        validation_report_id = str(request.validation_report.get("report_id", ""))

        if integration is not None and record_traceability:
            bridge = ComparativeQualityMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_quality_audit(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                definitive_catalog_id=definitive_catalog_id,
                validation_report_id=validation_report_id,
            )

        result = self._engine.audit(request)

        if integration is not None and record_traceability:
            bridge = ComparativeQualityMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_quality_audit(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
