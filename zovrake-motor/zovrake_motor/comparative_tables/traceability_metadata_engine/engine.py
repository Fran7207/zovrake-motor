"""Motor central del Traceability & Metadata Engine (TME)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.traceability_metadata_engine.catalog_store import (
    EnrichedComparativeTableCatalogStore,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.executor import (
    TraceabilityMetadataEnrichmentExecutor,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    MetadataEnrichmentInputGateway,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.integration_hooks import (
    ComparativeModelBuilderIntegrationPoint,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.port import MetadataEnricherPort
from zovrake_motor.comparative_tables.traceability_metadata_engine.registry import (
    MetadataEnricherRegistry,
)
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class TraceabilityMetadataEngineCore:
    """
    Traceability & Metadata Engine (TME).

    Enriquece cuadros comparativos con trazabilidad, contexto y metadatos
    a partir de catálogos del CSE, DCB, DRB, POE y GIE.
    """

    EXPECTED_ENRICHER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: MetadataEnricherRegistry | None = None,
        gateway: MetadataEnrichmentInputGateway | None = None,
        catalog_store: EnrichedComparativeTableCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or MetadataEnricherRegistry()
        self._gateway = gateway or MetadataEnrichmentInputGateway()
        self._catalog_store = catalog_store or EnrichedComparativeTableCatalogStore()
        self._executor: TraceabilityMetadataEnrichmentExecutor | None = None
        self._cmb_hook: ComparativeModelBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> MetadataEnricherRegistry:
        return self._registry

    @property
    def catalog_store(self) -> EnrichedComparativeTableCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> TraceabilityMetadataEnrichmentExecutor:
        if self._executor is None:
            self._executor = TraceabilityMetadataEnrichmentExecutor(self._registry)
        return self._executor

    @property
    def comparative_model_integration(self) -> ComparativeModelBuilderIntegrationPoint:
        if self._cmb_hook is None:
            self._cmb_hook = ComparativeModelBuilderIntegrationPoint(
                settings=self._metadata_settings(),
            )
        return self._cmb_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_ENRICHER_COUNT

    def initialize(self) -> None:
        settings = self._metadata_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = TraceabilityMetadataEnrichmentExecutor(self._registry)
        self._cmb_hook = ComparativeModelBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def enrich(
        self,
        request: TraceabilityMetadataEnrichmentRequest,
    ) -> TraceabilityMetadataEnrichmentResult:
        settings = self._metadata_settings()
        input_view = self._gateway.validate(
            request.structure_catalog,
            request.column_catalog,
            request.row_catalog,
            request.provider_catalog,
            request.integrity_report,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        cmb_status = self.comparative_model_integration.prepare_for_future_model_build(
            result.catalog,
        )
        observations = (
            *result.technical_observations,
            f"comparative_model_builder_status={cmb_status['status']}",
        )
        return TraceabilityMetadataEnrichmentResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            enriched_tables_count=result.enriched_tables_count,
            structure_catalog_preserved=result.structure_catalog_preserved,
            column_catalog_preserved=result.column_catalog_preserved,
            row_catalog_preserved=result.row_catalog_preserved,
            provider_catalog_preserved=result.provider_catalog_preserved,
            integrity_report_preserved=result.integrity_report_preserved,
            domain_model_preserved=result.domain_model_preserved,
            enrichers_executed=result.enrichers_executed,
            technical_observations=observations,
        )

    def extend(self, enricher: MetadataEnricherPort) -> None:
        """Incorpora un nuevo enriquecedor mediante extensión sin modificar el núcleo."""
        self._registry.register(enricher)

    def _metadata_settings(self) -> TraceabilityMetadataEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().traceability_metadata_engine
        return TraceabilityMetadataEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._metadata_settings()
        return {
            "initialized": self._initialized,
            "enrichers_count": self._registry.count(),
            "enrichers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "comparative_model_integration": self.comparative_model_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "comparative_table_metadata_enricher_enabled": (
                    settings.comparative_table_metadata_enricher_enabled
                ),
                "enrichment_id_prefix": settings.enrichment_id_prefix,
                "enrichment_id_padding": settings.enrichment_id_padding,
                "comparative_model_builder_prepared": settings.comparative_model_builder_prepared,
            },
        }
