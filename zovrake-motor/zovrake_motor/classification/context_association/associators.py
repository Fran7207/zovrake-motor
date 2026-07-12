"""Asociadores especializados del Context Association Engine."""

from __future__ import annotations

from zovrake_motor.classification.context_association.builders import (
    build_association_id,
    build_context_association_record,
)
from zovrake_motor.classification.context_association.enums import ContextAssociatorStrategyType
from zovrake_motor.classification.context_association.gateway import ContextAssociationInputView
from zovrake_motor.classification.context_association.models import ContextAssociatorResult
from zovrake_motor.classification.context_association.port import ContextAssociatorPort
from zovrake_motor.config.categories.classification import ContextAssociationSettings


class UniformGroupContextAssociator(ContextAssociatorPort):
    """
    Asocia el contexto del requerimiento con cada Grupo Comparable.

    No modifica el contenido del contexto ni de los grupos.
    """

    @property
    def associator_name(self) -> str:
        return "uniform_group_context_associator"

    @property
    def associator_label(self) -> str:
        return "Asociador Uniforme — Contexto por Grupo"

    @property
    def associator_type(self) -> ContextAssociatorStrategyType:
        return ContextAssociatorStrategyType.UNIFORM_GROUP_CONTEXT

    def associate(
        self,
        input_view: ContextAssociationInputView,
        *,
        settings: ContextAssociationSettings,
        start_sequence: int,
    ) -> ContextAssociatorResult:
        associations = []
        sequence = start_sequence
        preserved_context = input_view.preserved_context

        for group in sorted(input_view.group_catalog.groups, key=lambda item: item.get("group_id", "")):
            association_id = build_association_id(input_view.group_catalog.model_id, sequence)
            associations.append(
                build_context_association_record(
                    input_view=input_view,
                    group=group,
                    preserved_context=preserved_context,
                    association_id=association_id,
                    settings=settings,
                ),
            )
            sequence += 1

        return ContextAssociatorResult(
            associator_type=self.associator_type.value,
            associator_name=self.associator_name,
            associations=tuple(associations),
            technical_observations=(
                f"associator_type={self.associator_type.value}",
                f"associations_created={len(associations)}",
                "context_preserved=True",
                "groups_unmodified=True",
            ),
        )
