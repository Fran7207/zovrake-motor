"""Motor central del Concept Analysis Engine (CAE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.concept_analysis.catalog import TemporaryConceptCatalogStore
from zovrake_motor.classification.concept_analysis.executor import ConceptAnalysisExecutor
from zovrake_motor.classification.concept_analysis.gateway import InternalModelGateway
from zovrake_motor.classification.concept_analysis.integration_hooks import (
    ConceptNormalizationIntegrationPoint,
    MaterialClassificationIntegrationPoint,
    ServiceClassificationIntegrationPoint,
)
from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest, ConceptAnalysisResult
from zovrake_motor.classification.concept_analysis.port import ConceptDetectorPort
from zovrake_motor.classification.concept_analysis.registry import ConceptDetectorRegistry
from zovrake_motor.config.categories.classification import ConceptAnalysisSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ConceptAnalysisEngine:
    """
    Concept Analysis Engine (CAE).

    Identifica y estructura conceptos candidatos del Modelo Documental Interno.
    Ningún otro componente identifica conceptos directamente.
    """

    EXPECTED_DETECTOR_COUNT = 5

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ConceptDetectorRegistry | None = None,
        gateway: InternalModelGateway | None = None,
        catalog_store: TemporaryConceptCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ConceptDetectorRegistry()
        self._gateway = gateway or InternalModelGateway()
        self._catalog_store = catalog_store or TemporaryConceptCatalogStore()
        self._executor: ConceptAnalysisExecutor | None = None
        self._material_hook: MaterialClassificationIntegrationPoint | None = None
        self._service_hook: ServiceClassificationIntegrationPoint | None = None
        self._normalization_hook: ConceptNormalizationIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ConceptDetectorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> TemporaryConceptCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ConceptAnalysisExecutor:
        if self._executor is None:
            self._executor = ConceptAnalysisExecutor(self._registry)
        return self._executor

    @property
    def material_classification_integration(self) -> MaterialClassificationIntegrationPoint:
        if self._material_hook is None:
            self._material_hook = MaterialClassificationIntegrationPoint(
                settings=self._concept_analysis_settings(),
            )
        return self._material_hook

    @property
    def service_classification_integration(self) -> ServiceClassificationIntegrationPoint:
        if self._service_hook is None:
            self._service_hook = ServiceClassificationIntegrationPoint(
                settings=self._concept_analysis_settings(),
            )
        return self._service_hook

    @property
    def normalization_integration(self) -> ConceptNormalizationIntegrationPoint:
        if self._normalization_hook is None:
            self._normalization_hook = ConceptNormalizationIntegrationPoint(
                settings=self._concept_analysis_settings(),
            )
        return self._normalization_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_DETECTOR_COUNT

    def initialize(self) -> None:
        settings = self._concept_analysis_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ConceptAnalysisExecutor(self._registry)
        self._material_hook = MaterialClassificationIntegrationPoint(settings=settings)
        self._service_hook = ServiceClassificationIntegrationPoint(settings=settings)
        self._normalization_hook = ConceptNormalizationIntegrationPoint(settings=settings)
        self._initialized = True

    def analyze(self, request: ConceptAnalysisRequest) -> ConceptAnalysisResult:
        settings = self._concept_analysis_settings()
        model_view = self._gateway.validate(request.internal_model)
        result = self.executor.execute(model_view, settings=settings)
        self._catalog_store.save(result.catalog)

        material_status = self.material_classification_integration.prepare_for_future_classification(
            result.catalog,
        )
        service_status = self.service_classification_integration.prepare_for_future_classification(
            result.catalog,
        )
        normalization_status = self.normalization_integration.prepare_for_future_normalization(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"material_classification_status={material_status['status']}",
            f"service_classification_status={service_status['status']}",
            f"normalization_status={normalization_status['status']}",
        )
        return ConceptAnalysisResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            internal_model_preserved=result.internal_model_preserved,
            detectors_executed=result.detectors_executed,
            technical_observations=observations,
        )

    def extend(self, detector: ConceptDetectorPort) -> None:
        """Incorpora un nuevo detector mediante extensión sin modificar el núcleo."""
        self._registry.register(detector)

    def _concept_analysis_settings(self) -> ConceptAnalysisSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().concept_analysis
        return ConceptAnalysisSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._concept_analysis_settings()
        return {
            "initialized": self._initialized,
            "detectors_count": self._registry.count(),
            "detectors": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "material_classification_integration": self.material_classification_integration.snapshot(),
            "service_classification_integration": self.service_classification_integration.snapshot(),
            "normalization_integration": self.normalization_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_model_immutability": settings.preserve_model_immutability,
                "item_detector_enabled": settings.item_detector_enabled,
                "technical_detector_enabled": settings.technical_detector_enabled,
                "commercial_detector_enabled": settings.commercial_detector_enabled,
                "condition_detector_enabled": settings.condition_detector_enabled,
                "observation_detector_enabled": settings.observation_detector_enabled,
                "material_classification_prepared": settings.material_classification_prepared,
                "service_classification_prepared": settings.service_classification_prepared,
                "normalization_prepared": settings.normalization_prepared,
            },
        }
