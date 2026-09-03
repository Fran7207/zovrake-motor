"""Motor central del Equivalence Detection Engine (EDE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.equivalence_detection.catalog import EquivalenceCatalogStore
from zovrake_motor.classification.equivalence_detection.executor import EquivalenceDetectionExecutor
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogGateway
from zovrake_motor.classification.equivalence_detection.integration_hooks import (
    ComparableGroupBuilderIntegrationPoint,
    ComparativeDomainModelIntegrationPoint,
    ContextAssociationIntegrationPoint,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
)
from zovrake_motor.classification.equivalence_detection.port import EquivalenceDetectorPort
from zovrake_motor.classification.equivalence_detection.registry import EquivalenceDetectorRegistry
from zovrake_motor.config.categories.classification import EquivalenceDetectionSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class EquivalenceDetectionEngine:
    """
    Equivalence Detection Engine (EDE).

    Detecta equivalencias entre conceptos normalizados.
    Ningún otro componente detecta equivalencias directamente.
    """

    EXPECTED_DETECTOR_COUNT = 4

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: EquivalenceDetectorRegistry | None = None,
        gateway: NormalizedConceptCatalogGateway | None = None,
        catalog_store: EquivalenceCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or EquivalenceDetectorRegistry()
        self._gateway = gateway or NormalizedConceptCatalogGateway()
        self._catalog_store = catalog_store or EquivalenceCatalogStore()
        self._executor: EquivalenceDetectionExecutor | None = None
        self._group_builder_hook: ComparableGroupBuilderIntegrationPoint | None = None
        self._context_hook: ContextAssociationIntegrationPoint | None = None
        self._domain_model_hook: ComparativeDomainModelIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> EquivalenceDetectorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> EquivalenceCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> EquivalenceDetectionExecutor:
        if self._executor is None:
            self._executor = EquivalenceDetectionExecutor(self._registry)
        return self._executor

    @property
    def comparable_group_builder_integration(self) -> ComparableGroupBuilderIntegrationPoint:
        if self._group_builder_hook is None:
            self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(
                settings=self._equivalence_detection_settings(),
            )
        return self._group_builder_hook

    @property
    def context_association_integration(self) -> ContextAssociationIntegrationPoint:
        if self._context_hook is None:
            self._context_hook = ContextAssociationIntegrationPoint(
                settings=self._equivalence_detection_settings(),
            )
        return self._context_hook

    @property
    def comparative_domain_model_integration(self) -> ComparativeDomainModelIntegrationPoint:
        if self._domain_model_hook is None:
            self._domain_model_hook = ComparativeDomainModelIntegrationPoint(
                settings=self._equivalence_detection_settings(),
            )
        return self._domain_model_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_DETECTOR_COUNT

    def initialize(self) -> None:
        settings = self._equivalence_detection_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = EquivalenceDetectionExecutor(self._registry)
        self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(settings=settings)
        self._context_hook = ContextAssociationIntegrationPoint(settings=settings)
        self._domain_model_hook = ComparativeDomainModelIntegrationPoint(settings=settings)
        self._initialized = True

    def detect(self, request: EquivalenceDetectionRequest) -> EquivalenceDetectionResult:
        settings = self._equivalence_detection_settings()
        catalog_view = self._gateway.validate(request.normalized_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        grouping_status = self.comparable_group_builder_integration.prepare_for_future_grouping(
            result.catalog,
        )
        context_status = self.context_association_integration.prepare_for_future_association(
            result.catalog,
        )
        domain_status = self.comparative_domain_model_integration.prepare_for_future_modeling(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"comparable_group_builder_status={grouping_status['status']}",
            f"context_association_status={context_status['status']}",
            f"comparative_domain_model_status={domain_status['status']}",
        )
        return EquivalenceDetectionResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            normalized_catalog_preserved=result.normalized_catalog_preserved,
            detectors_executed=result.detectors_executed,
            technical_observations=observations,
        )

    def extend(self, detector: EquivalenceDetectorPort) -> None:
        """Incorpora un nuevo detector mediante extensión sin modificar el núcleo."""
        self._registry.register(detector)

    def _equivalence_detection_settings(self) -> EquivalenceDetectionSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().equivalence_detection
        return EquivalenceDetectionSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._equivalence_detection_settings()
        return {
            "initialized": self._initialized,
            "detectors_count": self._registry.count(),
            "detectors": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "comparable_group_builder_integration": self.comparable_group_builder_integration.snapshot(),
            "context_association_integration": self.context_association_integration.snapshot(),
            "comparative_domain_model_integration": self.comparative_domain_model_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "exact_match_detector_enabled": settings.exact_match_detector_enabled,
                "cross_type_distinct_detector_enabled": settings.cross_type_distinct_detector_enabled,
                "shared_origin_relation_detector_enabled": settings.shared_origin_relation_detector_enabled,
                "semantic_similarity_enabled": settings.semantic_similarity_enabled,
                "semantic_similarity_related_threshold": settings.semantic_similarity_related_threshold,
                "semantic_similarity_comparable_threshold": settings.semantic_similarity_comparable_threshold,
                "semantic_similarity_equivalent_threshold": settings.semantic_similarity_equivalent_threshold,
                "semantic_similarity_min_shared_tokens": settings.semantic_similarity_min_shared_tokens,
                "semantic_similarity_max_comparisons": settings.semantic_similarity_max_comparisons,
                "semantic_similarity_cross_document_only": settings.semantic_similarity_cross_document_only,
                "comparable_group_builder_prepared": settings.comparable_group_builder_prepared,
                "context_association_prepared": settings.context_association_prepared,
                "comparative_domain_model_prepared": settings.comparative_domain_model_prepared,
            },
        }
