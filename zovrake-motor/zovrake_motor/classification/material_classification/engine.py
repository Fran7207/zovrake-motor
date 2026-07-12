"""Motor central del Material Classification Engine (MCE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.material_classification.catalog import MaterialCatalogStore
from zovrake_motor.classification.material_classification.executor import MaterialClassificationExecutor
from zovrake_motor.classification.material_classification.gateway import ConceptCatalogGateway
from zovrake_motor.classification.material_classification.integration_hooks import (
    ComparableGroupBuilderIntegrationPoint,
    ConceptNormalizationIntegrationPoint,
    EquivalenceDetectionIntegrationPoint,
    ServiceClassificationIntegrationPoint,
)
from zovrake_motor.classification.material_classification.models import (
    MaterialClassificationRequest,
    MaterialClassificationResult,
)
from zovrake_motor.classification.material_classification.port import MaterialClassifierPort
from zovrake_motor.classification.material_classification.registry import MaterialClassifierRegistry
from zovrake_motor.config.categories.classification import MaterialClassificationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class MaterialClassificationEngine:
    """
    Material Classification Engine (MCE).

    Clasifica conceptos del CAE como materiales.
    Ningún otro componente clasifica materiales directamente.
    """

    EXPECTED_CLASSIFIER_COUNT = 2

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: MaterialClassifierRegistry | None = None,
        gateway: ConceptCatalogGateway | None = None,
        catalog_store: MaterialCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or MaterialClassifierRegistry()
        self._gateway = gateway or ConceptCatalogGateway()
        self._catalog_store = catalog_store or MaterialCatalogStore()
        self._executor: MaterialClassificationExecutor | None = None
        self._service_hook: ServiceClassificationIntegrationPoint | None = None
        self._normalization_hook: ConceptNormalizationIntegrationPoint | None = None
        self._equivalence_hook: EquivalenceDetectionIntegrationPoint | None = None
        self._group_builder_hook: ComparableGroupBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> MaterialClassifierRegistry:
        return self._registry

    @property
    def catalog_store(self) -> MaterialCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> MaterialClassificationExecutor:
        if self._executor is None:
            self._executor = MaterialClassificationExecutor(self._registry)
        return self._executor

    @property
    def service_classification_integration(self) -> ServiceClassificationIntegrationPoint:
        if self._service_hook is None:
            self._service_hook = ServiceClassificationIntegrationPoint(
                settings=self._material_classification_settings(),
            )
        return self._service_hook

    @property
    def normalization_integration(self) -> ConceptNormalizationIntegrationPoint:
        if self._normalization_hook is None:
            self._normalization_hook = ConceptNormalizationIntegrationPoint(
                settings=self._material_classification_settings(),
            )
        return self._normalization_hook

    @property
    def equivalence_detection_integration(self) -> EquivalenceDetectionIntegrationPoint:
        if self._equivalence_hook is None:
            self._equivalence_hook = EquivalenceDetectionIntegrationPoint(
                settings=self._material_classification_settings(),
            )
        return self._equivalence_hook

    @property
    def comparable_group_builder_integration(self) -> ComparableGroupBuilderIntegrationPoint:
        if self._group_builder_hook is None:
            self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(
                settings=self._material_classification_settings(),
            )
        return self._group_builder_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_CLASSIFIER_COUNT

    def initialize(self) -> None:
        settings = self._material_classification_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = MaterialClassificationExecutor(self._registry)
        self._service_hook = ServiceClassificationIntegrationPoint(settings=settings)
        self._normalization_hook = ConceptNormalizationIntegrationPoint(settings=settings)
        self._equivalence_hook = EquivalenceDetectionIntegrationPoint(settings=settings)
        self._group_builder_hook = ComparableGroupBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def classify(self, request: MaterialClassificationRequest) -> MaterialClassificationResult:
        settings = self._material_classification_settings()
        catalog_view = self._gateway.validate(request.concept_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        service_status = self.service_classification_integration.prepare_for_future_classification(
            result.catalog,
        )
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
            f"service_classification_status={service_status['status']}",
            f"normalization_status={normalization_status['status']}",
            f"equivalence_detection_status={equivalence_status['status']}",
            f"comparable_group_builder_status={grouping_status['status']}",
        )
        return MaterialClassificationResult(
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

    def extend(self, classifier: MaterialClassifierPort) -> None:
        """Incorpora un nuevo clasificador mediante extensión sin modificar el núcleo."""
        self._registry.register(classifier)

    def _material_classification_settings(self) -> MaterialClassificationSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().material_classification
        return MaterialClassificationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._material_classification_settings()
        return {
            "initialized": self._initialized,
            "classifiers_count": self._registry.count(),
            "classifiers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "service_classification_integration": self.service_classification_integration.snapshot(),
            "normalization_integration": self.normalization_integration.snapshot(),
            "equivalence_detection_integration": self.equivalence_detection_integration.snapshot(),
            "comparable_group_builder_integration": self.comparable_group_builder_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "item_classifier_enabled": settings.item_classifier_enabled,
                "partida_classifier_enabled": settings.partida_classifier_enabled,
                "service_classification_prepared": settings.service_classification_prepared,
                "normalization_prepared": settings.normalization_prepared,
                "equivalence_detection_prepared": settings.equivalence_detection_prepared,
                "comparable_group_builder_prepared": settings.comparable_group_builder_prepared,
            },
        }
