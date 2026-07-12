"""Ejecutor de constructores del Comparable Group Builder."""

from __future__ import annotations

from zovrake_motor.classification.comparable_group_builder.builders import build_comparable_group_catalog
from zovrake_motor.classification.comparable_group_builder.enums import ComparableGroupBuildStatus
from zovrake_motor.classification.comparable_group_builder.gateway import EquivalenceCatalogView
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupBuildIncident,
    ComparableGroupBuildResult,
    ComparableGroupRecord,
)
from zovrake_motor.classification.comparable_group_builder.registry import GroupBuilderRegistry
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings


class ComparableGroupBuildExecutor:
    """Coordina la ejecución secuencial de constructores sin modificar el catálogo de equivalencias."""

    def __init__(self, registry: GroupBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: EquivalenceCatalogView,
        *,
        settings: ComparableGroupBuilderSettings,
    ) -> ComparableGroupBuildResult:
        groups: list[ComparableGroupRecord] = []
        incidents: list[ComparableGroupBuildIncident] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                catalog_view,
                settings=settings,
                start_sequence=sequence,
            )
            groups.extend(result.groups)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.groups)

        if len(groups) > settings.max_groups_per_process:
            incidents.append(
                ComparableGroupBuildIncident(
                    builder_name="comparable_group_build_executor",
                    message=(
                        f"Se construyeron {len(groups)} grupos; "
                        f"límite configurado: {settings.max_groups_per_process}"
                    ),
                    severity="warning",
                ),
            )
            groups = groups[: settings.max_groups_per_process]

        catalog = build_comparable_group_catalog(
            catalog_view=catalog_view,
            groups=tuple(groups),
            context_association_prepared=settings.context_association_prepared,
            comparative_domain_model_prepared=settings.comparative_domain_model_prepared,
        )

        status = ComparableGroupBuildStatus.BUILT if groups else ComparableGroupBuildStatus.SKIPPED
        observations.extend(
            (
                "equivalence_catalog_preserved=True",
                "original_documents_unaccessed=True",
                "groups_built=" + str(len(groups)),
            ),
        )

        return ComparableGroupBuildResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            equivalence_catalog_preserved=True,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
