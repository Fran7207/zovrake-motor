"""Motor central del Concept Normalization Engine (CNE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.concept_normalization.catalog import NormalizedConceptCatalogStore
from zovrake_motor.classification.concept_normalization.executor import ConceptNormalizationExecutor
from zovrake_motor.classification.concept_normalization.gateway import ClassificationCatalogGateway
from zovrake_motor.classification.concept_normalization.integration_hooks import (
    ComparableGroupBuilderIntegrationPoint,
    EquivalenceDetectionIntegrationPoint,
)
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
)
from zovrake_motor.classification.concept_normalization.port import ConceptNormalizerPort
from zovrake_motor.classification.concept_normalization.registry import ConceptNormalizerRegistry
from zovrake_motor.config.categories.classification import ConceptNormalizationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ConceptNormalizationEngine:
    """
    Concept Normalization Engine (CNE).

    Normaliza la representación de materiales y servicios clasificados.
    Ningún otro componente normaliza conceptos directamente.
    """

    EXPECTED_NORMALIZER_COUNT = 6

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ConceptNormalizerRegistry | None = None,
        gateway: ClassificationCatalogGateway | None = None,
        catalog_store: NormalizedConceptCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ConceptNormalizerRegistry()
        self._gateway = gateway or ClassificationCatalogGateway()
        self._catalog_store = catalog_store or NormalizedConceptCatalogStore()
        self._executor: ConceptNormalizationExecutor | None = None
        self._equivalence_hook: EquivalenceDetectionIntegrationPoint | None = None
        self._group_builder_hook: ComparableGroupBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ConceptNormalizerRegistry:
        return self._registry

    @property
    def catalog_store(self) -> NormalizedConceptCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ConceptNormalizationExecutor:
        if self._executor is None:
            self._executor = ConceptNormalizationExecutor(self._registry)
        return self._executor

    @property
    def equivalence_detection_integration(self) -> EquivalenceDetectionIntegrationPoint:
        if self._equivalence_hook is None:
            self._equivalence_hook = EquivalenceDetectionIntegrationPoint(
                settings=self._concept_normalization_settings(),
            )
        return self._equivalence_hook

    @property
    def comparable_group_builder_integration(self) -> ComparableGroupBuilderIntegrationPoint:
        if self._group_builder_hook is None:
            self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(
                settings=self._concept_normalization_settings(),
            )
        return self._group_builder_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_NORMALIZER_COUNT

    def initialize(self) -> None:
        settings = self._concept_normalization_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ConceptNormalizationExecutor(self._registry)
        self._equivalence_hook = EquivalenceDetectionIntegrationPoint(settings=settings)
        self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def normalize(self, request: ConceptNormalizationRequest) -> ConceptNormalizationResult:
        settings = self._concept_normalization_settings()
        catalog_view = self._gateway.validate(
            request.material_catalog,
            request.service_catalog,
        )
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        equivalence_status = self.equivalence_detection_integration.prepare_for_future_detection(
            result.catalog,
        )
        grouping_status = self.comparable_group_builder_integration.prepare_for_future_grouping(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"equivalence_detection_status={equivalence_status['status']}",
            f"comparable_group_builder_status={grouping_status['status']}",
        )
        return ConceptNormalizationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            source_catalogs_preserved=result.source_catalogs_preserved,
            normalizers_executed=result.normalizers_executed,
            technical_observations=observations,
        )

    def extend(self, normalizer: ConceptNormalizerPort) -> None:
        """Incorpora un nuevo normalizador mediante extensión sin modificar el núcleo."""
        self._registry.register(normalizer)

    def _concept_normalization_settings(self) -> ConceptNormalizationSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().concept_normalization
        return ConceptNormalizationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._concept_normalization_settings()
        return {
            "initialized": self._initialized,
            "normalizers_count": self._registry.count(),
            "normalizers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "equivalence_detection_integration": self.equivalence_detection_integration.snapshot(),
            "comparable_group_builder_integration": self.comparable_group_builder_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "material_normalizer_enabled": settings.material_normalizer_enabled,
                "partida_normalizer_enabled": settings.partida_normalizer_enabled,
                "service_normalizer_enabled": settings.service_normalizer_enabled,
                "technical_element_normalizer_enabled": settings.technical_element_normalizer_enabled,
                "commercial_element_normalizer_enabled": settings.commercial_element_normalizer_enabled,
                "specification_normalizer_enabled": settings.specification_normalizer_enabled,
                "equivalence_detection_prepared": settings.equivalence_detection_prepared,
                "comparable_group_builder_prepared": settings.comparable_group_builder_prepared,
            },
        }
