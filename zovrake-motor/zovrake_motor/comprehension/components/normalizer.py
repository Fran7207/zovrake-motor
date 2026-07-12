"""Normalizador — integración con el Canonical Representation Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.canonical.engine import CanonicalRepresentationEngine
from zovrake_motor.comprehension.canonical.integration import RepresentationMotorIntegration
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest, CanonicalRepresentationResult
from zovrake_motor.comprehension.components.base import ComprehensionComponentPort

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ContentNormalizer(ComprehensionComponentPort):
    """
    Gestor del Canonical Representation Engine (CRE).

    Responsabilidad única: transformar la información extraída en
    Representación Canónica uniforme e inmutable.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: CanonicalRepresentationEngine | None = None,
    ) -> None:
        self._engine = engine or CanonicalRepresentationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "normalizer"

    @property
    def component_label(self) -> str:
        return "Normalizador"

    @property
    def engine(self) -> CanonicalRepresentationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def represent(
        self,
        request: CanonicalRepresentationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> CanonicalRepresentationResult:
        if integration is not None and record_traceability:
            bridge = RepresentationMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_representation(request.process_id, document_id=request.extraction_result.document_id)

        result = self._engine.represent(request)

        if integration is not None and record_traceability:
            bridge = RepresentationMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_representation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
