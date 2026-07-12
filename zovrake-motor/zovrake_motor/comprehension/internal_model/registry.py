"""Registro centralizado de constructores de entidad del IDMB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.internal_model.builders import (
    CommercialConditionsEntityBuilder,
    CommercialInformationEntityBuilder,
    DocumentEntityBuilder,
    ItemsEntityBuilder,
    MetadataEntityBuilder,
    ObservationsEntityBuilder,
    OriginalReferencesEntityBuilder,
    ProviderEntityBuilder,
    RequirementContextEntityBuilder,
    TechnicalInformationEntityBuilder,
)
from zovrake_motor.comprehension.internal_model.exceptions import EntityBuilderNotFoundError
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort
from zovrake_motor.config.categories.comprehension import DocumentInternalModelSettings


class EntityBuilderRegistry:
    """
    Registro único de constructores de entidad del Modelo Documental Interno.

    Todo constructor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._builders_by_name: dict[str, InternalEntityBuilderPort] = {}
        self._builders_ordered: list[InternalEntityBuilderPort] = []

    def register(self, builder: InternalEntityBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: DocumentInternalModelSettings | None = None) -> None:
        settings = settings or DocumentInternalModelSettings.default()
        candidates: list[tuple[bool, InternalEntityBuilderPort]] = [
            (settings.document_builder_enabled, DocumentEntityBuilder()),
            (settings.provider_builder_enabled, ProviderEntityBuilder()),
            (settings.commercial_builder_enabled, CommercialInformationEntityBuilder()),
            (settings.technical_builder_enabled, TechnicalInformationEntityBuilder()),
            (settings.items_builder_enabled, ItemsEntityBuilder()),
            (settings.conditions_builder_enabled, CommercialConditionsEntityBuilder()),
            (settings.observations_builder_enabled, ObservationsEntityBuilder()),
            (settings.metadata_builder_enabled, MetadataEntityBuilder()),
            (settings.requirement_context_builder_enabled, RequirementContextEntityBuilder()),
            (settings.original_references_builder_enabled, OriginalReferencesEntityBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> InternalEntityBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> InternalEntityBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise EntityBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[InternalEntityBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]

    def get_document_builder(self) -> DocumentEntityBuilder:
        builder = self.require("document_entity_builder")
        assert isinstance(builder, DocumentEntityBuilder)
        return builder

    def get_provider_builder(self) -> ProviderEntityBuilder:
        builder = self.require("provider_entity_builder")
        assert isinstance(builder, ProviderEntityBuilder)
        return builder

    def get_commercial_builder(self) -> CommercialInformationEntityBuilder:
        builder = self.require("commercial_information_entity_builder")
        assert isinstance(builder, CommercialInformationEntityBuilder)
        return builder

    def get_technical_builder(self) -> TechnicalInformationEntityBuilder:
        builder = self.require("technical_information_entity_builder")
        assert isinstance(builder, TechnicalInformationEntityBuilder)
        return builder

    def get_items_builder(self) -> ItemsEntityBuilder:
        builder = self.require("items_entity_builder")
        assert isinstance(builder, ItemsEntityBuilder)
        return builder

    def get_conditions_builder(self) -> CommercialConditionsEntityBuilder:
        builder = self.require("commercial_conditions_entity_builder")
        assert isinstance(builder, CommercialConditionsEntityBuilder)
        return builder

    def get_observations_builder(self) -> ObservationsEntityBuilder:
        builder = self.require("observations_entity_builder")
        assert isinstance(builder, ObservationsEntityBuilder)
        return builder

    def get_metadata_builder(self) -> MetadataEntityBuilder:
        builder = self.require("metadata_entity_builder")
        assert isinstance(builder, MetadataEntityBuilder)
        return builder

    def get_requirement_context_builder(self) -> RequirementContextEntityBuilder:
        builder = self.require("requirement_context_entity_builder")
        assert isinstance(builder, RequirementContextEntityBuilder)
        return builder

    def get_original_references_builder(self) -> OriginalReferencesEntityBuilder:
        builder = self.require("original_references_entity_builder")
        assert isinstance(builder, OriginalReferencesEntityBuilder)
        return builder
