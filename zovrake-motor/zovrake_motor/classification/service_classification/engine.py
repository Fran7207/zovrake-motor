"""Motor central del Service Classification Engine (SCE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.service_classification.catalog import ServiceCatalogStore
from zovrake_motor.classification.service_classification.executor import ServiceClassificationExecutor
from zovrake_motor.classification.service_classification.gateway import ConceptCatalogGateway
from zovrake_motor.classification.service_classification.integration_hooks import (
    ComparableGroupBuilderIntegrationPoint,
    ConceptNormalizationIntegrationPoint,
    EquivalenceDetectionIntegrationPoint,
)
from zovrake_motor.classification.service_classification.models import (
    ServiceClassificationRequest,
    ServiceClassificationResult,
)
from zovrake_motor.classification.service_classification.port import ServiceClassifierPort
from zovrake_motor.classification.service_classification.registry import ServiceClassifierRegistry
from zovrake_motor.config.categories.classification import ServiceClassificationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ServiceClassificationEngine:
    """
    Service Classification Engine (SCE).

    Clasifica conceptos del CAE como servicios.
    Ningún otro componente clasifica servicios directamente.
    """

    EXPECTED_CLASSIFIER_COUNT = 3

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ServiceClassifierRegistry | None = None,
        gateway: ConceptCatalogGateway | None = None,
        catalog_store: ServiceCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ServiceClassifierRegistry()
        self._gateway = gateway or ConceptCatalogGateway()
        self._catalog_store = catalog_store or ServiceCatalogStore()
        self._executor: ServiceClassificationExecutor | None = None
        self._normalization_hook: ConceptNormalizationIntegrationPoint | None = None
        self._equivalence_hook: EquivalenceDetectionIntegrationPoint | None = None
        self._group_builder_hook: ComparableGroupBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ServiceClassifierRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ServiceCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ServiceClassificationExecutor:
        if self._executor is None:
            self._executor = ServiceClassificationExecutor(self._registry)
        return self._executor

    @property
    def normalization_integration(self) -> ConceptNormalizationIntegrationPoint:
        if self._normalization_hook is None:
            self._normalization_hook = ConceptNormalizationIntegrationPoint(
                settings=self._service_classification_settings(),
            )
        return self._normalization_hook

    @property
    def equivalence_detection_integration(self) -> EquivalenceDetectionIntegrationPoint:
        if self._equivalence_hook is None:
            self._equivalence_hook = EquivalenceDetectionIntegrationPoint(
                settings=self._service_classification_settings(),
            )
        return self._equivalence_hook

    @property
    def comparable_group_builder_integration(self) -> ComparableGroupBuilderIntegrationPoint:
        if self._group_builder_hook is None:
            self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(
                settings=self._service_classification_settings(),
            )
        return self._group_builder_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_CLASSIFIER_COUNT

    def initialize(self) -> None:
        settings = self._service_classification_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ServiceClassificationExecutor(self._registry)
        self._normalization_hook = ConceptNormalizationIntegrationPoint(settings=settings)
        self._equivalence_hook = EquivalenceDetectionIntegrationPoint(settings=settings)
        self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def classify(self, request: ServiceClassificationRequest) -> ServiceClassificationResult:
        settings = self._service_classification_settings()
        catalog_view = self._gateway.validate(request.concept_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        normalization_status = self.normalization_integration.prepare_for_future_normalization(
            result.catalog,
        )
        equivalence_status = self.equivalence_detection_integration.prepare_for_future_detection(
            result.catalog,
        )
        grouping_status = self.comparable_group_builder_integration.prepare_for_future_grouping(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"normalization_status={normalization_status['status']}",
            f"equivalence_detection_status={equivalence_status['status']}",
            f"comparable_group_builder_status={grouping_status['status']}",
        )
        return ServiceClassificationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            concept_catalog_preserved=result.concept_catalog_preserved,
            classifiers_executed=result.classifiers_executed,
            technical_observations=observations,
        )

    def extend(self, classifier: ServiceClassifierPort) -> None:
        """Incorpora un nuevo clasificador mediante extensión sin modificar el núcleo."""
        self._registry.register(classifier)

    def _service_classification_settings(self) -> ServiceClassificationSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().service_classification
        return ServiceClassificationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._service_classification_settings()
        return {
            "initialized": self._initialized,
            "classifiers_count": self._registry.count(),
            "classifiers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "normalization_integration": self.normalization_integration.snapshot(),
            "equivalence_detection_integration": self.equivalence_detection_integration.snapshot(),
            "comparable_group_builder_integration": self.comparable_group_builder_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "commercial_condition_classifier_enabled": settings.commercial_condition_classifier_enabled,
                "observation_classifier_enabled": settings.observation_classifier_enabled,
                "technical_element_classifier_enabled": settings.technical_element_classifier_enabled,
                "normalization_prepared": settings.normalization_prepared,
                "equivalence_detection_prepared": settings.equivalence_detection_prepared,
                "comparable_group_builder_prepared": settings.comparable_group_builder_prepared,
            },
        }
