"""Motor central de Representación Canónica (CRE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.canonical.assembler import CanonicalAssembler
from zovrake_motor.comprehension.canonical.classification_hook import ClassificationIntegrationPoint
from zovrake_motor.comprehension.canonical.gateway import ExtractionResultGateway
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest, CanonicalRepresentationResult
from zovrake_motor.comprehension.canonical.port import CanonicalSectionTransformerPort
from zovrake_motor.comprehension.canonical.registry import TransformerRegistry
from zovrake_motor.config.categories.comprehension import DocumentCanonicalSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class CanonicalRepresentationEngine:
    """
    Canonical Representation Engine (CRE).

    Transforma la información estructural extraída en Representación Canónica uniforme.
    Ningún otro módulo realiza transformaciones estructurales.
    """

    EXPECTED_TRANSFORMER_COUNT = 7

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: TransformerRegistry | None = None,
        gateway: ExtractionResultGateway | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or TransformerRegistry()
        self._gateway = gateway or ExtractionResultGateway()
        self._assembler: CanonicalAssembler | None = None
        self._classification_hook: ClassificationIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> TransformerRegistry:
        return self._registry

    @property
    def assembler(self) -> CanonicalAssembler:
        if self._assembler is None:
            self._assembler = CanonicalAssembler(self._registry)
        return self._assembler

    @property
    def classification_integration(self) -> ClassificationIntegrationPoint:
        if self._classification_hook is None:
            self._classification_hook = ClassificationIntegrationPoint(
                settings=self._canonical_settings(),
            )
        return self._classification_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_TRANSFORMER_COUNT

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults(settings=self._canonical_settings())
        self._assembler = CanonicalAssembler(self._registry)
        self._classification_hook = ClassificationIntegrationPoint(settings=self._canonical_settings())
        self._initialized = True

    def represent(self, request: CanonicalRepresentationRequest) -> CanonicalRepresentationResult:
        extraction = self._gateway.validate(request)
        traceability = self._gateway.build_traceability(extraction)
        result = self.assembler.assemble(
            extraction,
            traceability=traceability,
            classification_integration_prepared=self.classification_integration.is_prepared,
        )
        classification_status = self.classification_integration.prepare_for_future_consumption(
            result.representation,
        )
        observations = (
            *result.technical_observations,
            f"classification_status={classification_status['status']}",
            "document_original_unmodified=True",
        )
        return CanonicalRepresentationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            representation=result.representation,
            incidents=result.incidents,
            original_preserved=result.original_preserved,
            classification_integration_prepared=result.classification_integration_prepared,
            transformers_executed=result.transformers_executed,
            technical_observations=observations,
        )

    def extend(self, transformer: CanonicalSectionTransformerPort) -> None:
        """Incorpora un nuevo transformador mediante extensión sin modificar el núcleo."""
        self._registry.register(transformer)

    def _canonical_settings(self) -> DocumentCanonicalSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().canonical
        return DocumentCanonicalSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._canonical_settings()
        return {
            "initialized": self._initialized,
            "transformers_count": self._registry.count(),
            "transformers": self._registry.snapshot(),
            "classification_integration": self.classification_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_immutability": settings.preserve_immutability,
                "classification_integration_prepared": settings.classification_integration_prepared,
                "classification_enabled": settings.classification_enabled,
            },
        }
