"""Motor central del Group Integrity Engine (GIE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.group_integrity_engine.executor import (
    GroupIntegrityValidationExecutor,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    IntegrityValidationInputGateway,
)
from zovrake_motor.comparative_tables.group_integrity_engine.integration_hooks import (
    TraceabilityMetadataEngineIntegrationPoint,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)
from zovrake_motor.comparative_tables.group_integrity_engine.port import IntegrityValidatorPort
from zovrake_motor.comparative_tables.group_integrity_engine.registry import (
    IntegrityValidatorRegistry,
)
from zovrake_motor.comparative_tables.group_integrity_engine.report_store import (
    GroupIntegrityReportStore,
)
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class GroupIntegrityEngineCore:
    """
    Group Integrity Engine (GIE).

    Valida integridad estructural a partir de catálogos del CSE, DCB, DRB y POE.
    Ningún otro componente valida integridad directamente.
    """

    EXPECTED_VALIDATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: IntegrityValidatorRegistry | None = None,
        gateway: IntegrityValidationInputGateway | None = None,
        report_store: GroupIntegrityReportStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or IntegrityValidatorRegistry()
        self._gateway = gateway or IntegrityValidationInputGateway()
        self._report_store = report_store or GroupIntegrityReportStore()
        self._executor: GroupIntegrityValidationExecutor | None = None
        self._tme_hook: TraceabilityMetadataEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> IntegrityValidatorRegistry:
        return self._registry

    @property
    def report_store(self) -> GroupIntegrityReportStore:
        return self._report_store

    @property
    def executor(self) -> GroupIntegrityValidationExecutor:
        if self._executor is None:
            self._executor = GroupIntegrityValidationExecutor(self._registry)
        return self._executor

    @property
    def traceability_metadata_integration(self) -> TraceabilityMetadataEngineIntegrationPoint:
        if self._tme_hook is None:
            self._tme_hook = TraceabilityMetadataEngineIntegrationPoint(
                settings=self._integrity_settings(),
            )
        return self._tme_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_VALIDATOR_COUNT

    def initialize(self) -> None:
        settings = self._integrity_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = GroupIntegrityValidationExecutor(self._registry)
        self._tme_hook = TraceabilityMetadataEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def validate(
        self,
        request: GroupIntegrityValidationRequest,
    ) -> GroupIntegrityValidationResult:
        settings = self._integrity_settings()
        input_view = self._gateway.validate(
            request.structure_catalog,
            request.column_catalog,
            request.row_catalog,
            request.provider_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._report_store.save(result.report)

        tme_status = self.traceability_metadata_integration.prepare_for_future_enrichment(
            result.report,
        )
        observations = (
            *result.technical_observations,
            f"traceability_metadata_engine_status={tme_status['status']}",
        )
        return GroupIntegrityValidationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            report=result.report,
            status=result.status,
            findings_count=result.findings_count,
            error_count=result.error_count,
            warning_count=result.warning_count,
            structure_catalog_preserved=result.structure_catalog_preserved,
            column_catalog_preserved=result.column_catalog_preserved,
            row_catalog_preserved=result.row_catalog_preserved,
            provider_catalog_preserved=result.provider_catalog_preserved,
            domain_model_preserved=result.domain_model_preserved,
            validators_executed=result.validators_executed,
            technical_observations=observations,
        )

    def extend(self, validator: IntegrityValidatorPort) -> None:
        """Incorpora un nuevo validador mediante extensión sin modificar el núcleo."""
        self._registry.register(validator)

    def _integrity_settings(self) -> GroupIntegrityEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().group_integrity_engine
        return GroupIntegrityEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._integrity_settings()
        return {
            "initialized": self._initialized,
            "validators_count": self._registry.count(),
            "validators": self._registry.snapshot(),
            "report_entries_count": self._report_store.count(),
            "gateway": self._gateway.snapshot(),
            "traceability_metadata_integration": self.traceability_metadata_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "comparative_table_integrity_validator_enabled": (
                    settings.comparative_table_integrity_validator_enabled
                ),
                "finding_id_prefix": settings.finding_id_prefix,
                "finding_id_padding": settings.finding_id_padding,
                "max_errors_before_invalid": settings.max_errors_before_invalid,
                "traceability_metadata_engine_prepared": (
                    settings.traceability_metadata_engine_prepared
                ),
            },
        }
