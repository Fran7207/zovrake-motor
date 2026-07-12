"""Ejecutor de asociadores del Context Association Engine."""

from __future__ import annotations

from zovrake_motor.classification.context_association.builders import build_context_association_catalog
from zovrake_motor.classification.context_association.enums import ContextAssociationStatus
from zovrake_motor.classification.context_association.gateway import ContextAssociationInputView
from zovrake_motor.classification.context_association.models import (
    ContextAssociationIncident,
    ContextAssociationRecord,
    ContextAssociationResult,
)
from zovrake_motor.classification.context_association.registry import ContextAssociatorRegistry
from zovrake_motor.config.categories.classification import ContextAssociationSettings


class ContextAssociationExecutor:
    """Coordina asociadores sin modificar catálogo de grupos ni contexto."""

    def __init__(self, registry: ContextAssociatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ContextAssociationInputView,
        *,
        settings: ContextAssociationSettings,
    ) -> ContextAssociationResult:
        associations: list[ContextAssociationRecord] = []
        incidents: list[ContextAssociationIncident] = []
        observations: list[str] = []
        sequence = 1

        for associator in self._registry.all_associators():
            result = associator.associate(input_view, settings=settings, start_sequence=sequence)
            associations.extend(result.associations)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.associations)

        if len(associations) > settings.max_associations_per_process:
            incidents.append(
                ContextAssociationIncident(
                    associator_name="context_association_executor",
                    message=(
                        f"Se crearon {len(associations)} asociaciones; "
                        f"límite configurado: {settings.max_associations_per_process}"
                    ),
                    severity="warning",
                ),
            )
            associations = associations[: settings.max_associations_per_process]

        catalog = build_context_association_catalog(
            input_view=input_view,
            associations=tuple(associations),
            preserved_context=input_view.preserved_context,
            comparative_domain_model_prepared=settings.comparative_domain_model_prepared,
        )

        status = (
            ContextAssociationStatus.ASSOCIATED if associations else ContextAssociationStatus.SKIPPED
        )
        observations.extend(
            (
                "comparable_group_catalog_preserved=True",
                "context_preserved=True",
                "original_documents_unaccessed=True",
                f"associations_created={len(associations)}",
            ),
        )

        return ContextAssociationResult(
            process_id=input_view.group_catalog.process_id,
            document_id=input_view.group_catalog.document_id,
            model_id=input_view.group_catalog.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            comparable_group_catalog_preserved=True,
            context_preserved=True,
            associators_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
