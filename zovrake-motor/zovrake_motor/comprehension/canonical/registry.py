"""Registro centralizado de transformadores del CRE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.exceptions import TransformerNotFoundError
from zovrake_motor.comprehension.canonical.port import CanonicalSectionTransformerPort
from zovrake_motor.comprehension.canonical.transformers import (
    CommercialInformationTransformer,
    ConditionsTransformer,
    ItemsTransformer,
    MetadataTransformer,
    ObservationsTransformer,
    ProviderTransformer,
    TechnicalInformationTransformer,
)
from zovrake_motor.config.categories.comprehension import DocumentCanonicalSettings


class TransformerRegistry:
    """
    Registro único de transformadores de sección del Modelo Canónico.

    Todo transformador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._transformers_by_name: dict[str, CanonicalSectionTransformerPort] = {}
        self._transformers_ordered: list[CanonicalSectionTransformerPort] = []

    def register(self, transformer: CanonicalSectionTransformerPort) -> None:
        if transformer.transformer_name in self._transformers_by_name:
            raise ValueError(f"Transformador ya registrado: {transformer.transformer_name}")
        self._transformers_by_name[transformer.transformer_name] = transformer
        self._transformers_ordered.append(transformer)

    def register_defaults(self, *, settings: DocumentCanonicalSettings | None = None) -> None:
        settings = settings or DocumentCanonicalSettings.default()
        candidates: list[tuple[bool, CanonicalSectionTransformerPort]] = [
            (settings.provider_transformer_enabled, ProviderTransformer()),
            (settings.commercial_transformer_enabled, CommercialInformationTransformer()),
            (settings.technical_transformer_enabled, TechnicalInformationTransformer()),
            (settings.items_transformer_enabled, ItemsTransformer()),
            (settings.conditions_transformer_enabled, ConditionsTransformer()),
            (settings.observations_transformer_enabled, ObservationsTransformer()),
            (settings.metadata_transformer_enabled, MetadataTransformer()),
        ]
        for enabled, transformer in candidates:
            if enabled:
                self.register(transformer)

    def get(self, name: str) -> CanonicalSectionTransformerPort | None:
        return self._transformers_by_name.get(name)

    def require(self, name: str) -> CanonicalSectionTransformerPort:
        transformer = self.get(name)
        if transformer is None:
            raise TransformerNotFoundError(f"Transformador no registrado: {name}")
        return transformer

    def all_transformers(self) -> tuple[CanonicalSectionTransformerPort, ...]:
        return tuple(self._transformers_ordered)

    def count(self) -> int:
        return len(self._transformers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [transformer.snapshot() for transformer in self._transformers_ordered]

    def get_provider_transformer(self) -> ProviderTransformer:
        transformer = self.require("provider_transformer")
        assert isinstance(transformer, ProviderTransformer)
        return transformer

    def get_commercial_transformer(self) -> CommercialInformationTransformer:
        transformer = self.require("commercial_information_transformer")
        assert isinstance(transformer, CommercialInformationTransformer)
        return transformer

    def get_technical_transformer(self) -> TechnicalInformationTransformer:
        transformer = self.require("technical_information_transformer")
        assert isinstance(transformer, TechnicalInformationTransformer)
        return transformer

    def get_items_transformer(self) -> ItemsTransformer:
        transformer = self.require("items_transformer")
        assert isinstance(transformer, ItemsTransformer)
        return transformer

    def get_conditions_transformer(self) -> ConditionsTransformer:
        transformer = self.require("conditions_transformer")
        assert isinstance(transformer, ConditionsTransformer)
        return transformer

    def get_observations_transformer(self) -> ObservationsTransformer:
        transformer = self.require("observations_transformer")
        assert isinstance(transformer, ObservationsTransformer)
        return transformer

    def get_metadata_transformer(self) -> MetadataTransformer:
        transformer = self.require("metadata_transformer")
        assert isinstance(transformer, MetadataTransformer)
        return transformer
