"""Ejecutor de constructores del Comparative Domain Model Builder."""

from __future__ import annotations

from zovrake_motor.classification.comparative_domain_model.builders import (
    build_comparative_domain_model_catalog,
)
from zovrake_motor.classification.comparative_domain_model.enums import ComparativeDomainModelBuildStatus
from zovrake_motor.classification.comparative_domain_model.gateway import ContextAssociationCatalogView
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildIncident,
    ComparativeDomainModelBuildResult,
    ComparativeDomainModelRecord,
)
from zovrake_motor.classification.comparative_domain_model.registry import DomainModelBuilderRegistry
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings


class ComparativeDomainModelBuildExecutor:
    """Coordina constructores sin modificar datos de origen."""

    def __init__(self, registry: DomainModelBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: ContextAssociationCatalogView,
        *,
        settings: ComparativeDomainModelBuilderSettings,
    ) -> ComparativeDomainModelBuildResult:
        models: list[ComparativeDomainModelRecord] = []
        incidents: list[ComparativeDomainModelBuildIncident] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                catalog_view,
                settings=settings,
                start_sequence=sequence,
            )
            models.extend(result.models)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.models)

        if len(models) > settings.max_models_per_process:
            incidents.append(
                ComparativeDomainModelBuildIncident(
                    builder_name="comparative_domain_model_build_executor",
                    message=(
                        f"Se construyeron {len(models)} modelos; "
                        f"límite configurado: {settings.max_models_per_process}"
                    ),
                    severity="warning",
                ),
            )
            models = models[: settings.max_models_per_process]

        catalog = build_comparative_domain_model_catalog(
            catalog_view=catalog_view,
            models=tuple(models),
            pm6_output_contract=settings.pm6_output_contract,
        )

        status = (
            ComparativeDomainModelBuildStatus.BUILT if models else ComparativeDomainModelBuildStatus.SKIPPED
        )
        observations.extend(
            (
                "source_data_preserved=True",
                "original_documents_unaccessed=True",
                f"models_built={len(models)}",
                f"pm6_output_contract={settings.pm6_output_contract}",
            ),
        )

        return ComparativeDomainModelBuildResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            source_data_preserved=True,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
