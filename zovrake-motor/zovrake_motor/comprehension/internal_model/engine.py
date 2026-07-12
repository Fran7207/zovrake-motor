"""Motor central del Internal Document Model Builder (IDMB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.internal_model.assembler import InternalModelAssembler
from zovrake_motor.comprehension.internal_model.classification_hook import ClassificationIntegrationPoint
from zovrake_motor.comprehension.internal_model.gateway import CanonicalRepresentationGateway
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalModelBuildResult
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort
from zovrake_motor.comprehension.internal_model.registry import EntityBuilderRegistry
from zovrake_motor.config.categories.comprehension import DocumentInternalModelSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class InternalDocumentModelBuilder:
    """
    Internal Document Model Builder (IDMB).

    Construye el Modelo Documental Interno definitivo a partir de la Representación Canónica.
    Ningún otro módulo construye este modelo.
    """

    EXPECTED_BUILDER_COUNT = 10

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: EntityBuilderRegistry | None = None,
        gateway: CanonicalRepresentationGateway | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or EntityBuilderRegistry()
        self._gateway = gateway or CanonicalRepresentationGateway()
        self._assembler: InternalModelAssembler | None = None
        self._classification_hook: ClassificationIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> EntityBuilderRegistry:
        return self._registry

    @property
    def assembler(self) -> InternalModelAssembler:
        if self._assembler is None:
            self._assembler = InternalModelAssembler(self._registry)
        return self._assembler

    @property
    def classification_integration(self) -> ClassificationIntegrationPoint:
        if self._classification_hook is None:
            self._classification_hook = ClassificationIntegrationPoint(
                settings=self._internal_model_settings(),
            )
        return self._classification_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults(settings=self._internal_model_settings())
        self._assembler = InternalModelAssembler(self._registry)
        self._classification_hook = ClassificationIntegrationPoint(
            settings=self._internal_model_settings(),
        )
        self._initialized = True

    def build(self, request: InternalModelBuildRequest) -> InternalModelBuildResult:
        canonical = self._gateway.validate(request)
        model_id = f"idm://{canonical.document_id}"
        traceability = self._gateway.build_traceability(canonical, model_id=model_id)
        representation = self._gateway.representation(canonical)
        result = self.assembler.assemble(
            representation,
            traceability=traceability,
            requirement_code=request.requirement_code,
            requirement_context=request.requirement_context,
            classification_integration_prepared=self.classification_integration.is_prepared,
        )
        classification_status = self.classification_integration.prepare_for_future_consumption(result.model)
        observations = (
            *result.technical_observations,
            f"classification_status={classification_status['status']}",
            "canonical_representation_unmodified=True",
        )
        return InternalModelBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model=result.model,
            incidents=result.incidents,
            original_preserved=result.original_preserved,
            classification_integration_prepared=result.classification_integration_prepared,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: InternalEntityBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _internal_model_settings(self) -> DocumentInternalModelSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().internal_model
        return DocumentInternalModelSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._internal_model_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "classification_integration": self.classification_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_immutability": settings.preserve_immutability,
                "classification_integration_prepared": settings.classification_integration_prepared,
                "classification_enabled": settings.classification_enabled,
            },
        }
