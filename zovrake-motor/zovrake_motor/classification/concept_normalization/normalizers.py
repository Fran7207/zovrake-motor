"""Normalizadores especializados del Concept Normalization Engine."""

from __future__ import annotations

from abc import abstractmethod

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.concept_normalization.builders import (
    build_normalized_concept_from_material,
    build_normalized_concept_from_service,
)
from zovrake_motor.classification.concept_normalization.enums import (
    ConceptNormalizerType,
    NormalizedConceptCategory,
)
from zovrake_motor.classification.concept_normalization.gateway import ClassificationCatalogView
from zovrake_motor.classification.concept_normalization.models import NormalizerResult
from zovrake_motor.classification.concept_normalization.port import ConceptNormalizerPort


class _BaseMaterialNormalizer(ConceptNormalizerPort):
    """Base común para normalizadores de materiales por tipo de concepto."""

    @property
    @abstractmethod
    def supported_concept_kind(self) -> ConceptKind:
        """Tipo de concepto soportado."""

    def normalize(self, catalog_view: ClassificationCatalogView, *, start_sequence: int) -> NormalizerResult:
        concepts = []
        sequence = start_sequence
        for material in catalog_view.materials:
            if material.concept_kind != self.supported_concept_kind.value:
                continue
            if not material.original_name.strip():
                continue
            concepts.append(
                build_normalized_concept_from_material(
                    catalog_view=catalog_view,
                    material=material,
                    concept_type=self.normalizer_type.value,
                    sequence=sequence,
                ),
            )
            sequence += 1

        return NormalizerResult(
            normalizer_type=self.normalizer_type,
            normalizer_name=self.normalizer_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"concept_kind={self.supported_concept_kind.value}",
                f"concepts_normalized={len(concepts)}",
            ),
        )


class MaterialConceptNormalizer(_BaseMaterialNormalizer):
    """Normaliza conceptos de tipo ítem (materiales)."""

    @property
    def normalizer_name(self) -> str:
        return "material_concept_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Materiales"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.MATERIAL

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.ITEM


class PartidaConceptNormalizer(_BaseMaterialNormalizer):
    """Normaliza conceptos de tipo partida."""

    @property
    def normalizer_name(self) -> str:
        return "partida_concept_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Partidas"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.PARTIDA

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.PARTIDA


class _BaseServiceNormalizer(ConceptNormalizerPort):
    """Base común para normalizadores de servicios por tipo de concepto."""

    @property
    @abstractmethod
    def supported_concept_kind(self) -> ConceptKind:
        """Tipo de concepto soportado."""

    def normalize(self, catalog_view: ClassificationCatalogView, *, start_sequence: int) -> NormalizerResult:
        concepts = []
        sequence = start_sequence
        for service in catalog_view.services:
            if service.concept_kind != self.supported_concept_kind.value:
                continue
            if not service.original_name.strip():
                continue
            concepts.append(
                build_normalized_concept_from_service(
                    catalog_view=catalog_view,
                    service=service,
                    concept_type=self.normalizer_type.value,
                    sequence=sequence,
                ),
            )
            sequence += 1

        return NormalizerResult(
            normalizer_type=self.normalizer_type,
            normalizer_name=self.normalizer_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"concept_kind={self.supported_concept_kind.value}",
                f"concepts_normalized={len(concepts)}",
            ),
        )


class ServiceConceptNormalizer(_BaseServiceNormalizer):
    """Normaliza observaciones como servicios."""

    @property
    def normalizer_name(self) -> str:
        return "service_concept_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Servicios"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.SERVICE

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.OBSERVATION


class TechnicalElementNormalizer(_BaseServiceNormalizer):
    """Normaliza elementos técnicos."""

    @property
    def normalizer_name(self) -> str:
        return "technical_element_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Elementos Técnicos"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.TECHNICAL_ELEMENT

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.TECHNICAL_ELEMENT


class CommercialElementNormalizer(_BaseServiceNormalizer):
    """Normaliza elementos comerciales (condiciones comerciales)."""

    @property
    def normalizer_name(self) -> str:
        return "commercial_element_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Elementos Comerciales"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.COMMERCIAL_ELEMENT

    @property
    def supported_concept_kind(self) -> ConceptKind:
        return ConceptKind.COMMERCIAL_CONDITION


class SpecificationNormalizer(ConceptNormalizerPort):
    """Normaliza especificaciones técnicas de materiales y servicios."""

    @property
    def normalizer_name(self) -> str:
        return "specification_normalizer"

    @property
    def normalizer_label(self) -> str:
        return "Normalizador de Conceptos — Especificaciones"

    @property
    def normalizer_type(self) -> ConceptNormalizerType:
        return ConceptNormalizerType.SPECIFICATION

    def normalize(self, catalog_view: ClassificationCatalogView, *, start_sequence: int) -> NormalizerResult:
        concepts = []
        sequence = start_sequence

        for material in catalog_view.materials:
            for spec in material.technical_information.specifications:
                if not str(spec).strip():
                    continue
                concepts.append(
                    build_normalized_concept_from_material(
                        catalog_view=catalog_view,
                        material=material,
                        concept_type=self.normalizer_type.value,
                        sequence=sequence,
                        original_value=str(spec),
                        metadata={"parent_material_id": material.material_id},
                    ),
                )
                sequence += 1

        for service in catalog_view.services:
            for spec in service.technical_information.specifications:
                if not str(spec).strip():
                    continue
                concepts.append(
                    build_normalized_concept_from_service(
                        catalog_view=catalog_view,
                        service=service,
                        concept_type=self.normalizer_type.value,
                        sequence=sequence,
                        original_value=str(spec),
                        source_category=NormalizedConceptCategory.SPECIFICATION.value,
                        metadata={"parent_service_id": service.service_id},
                    ),
                )
                sequence += 1

        return NormalizerResult(
            normalizer_type=self.normalizer_type,
            normalizer_name=self.normalizer_name,
            concepts=tuple(concepts),
            technical_observations=(
                f"concept_type={self.normalizer_type.value}",
                f"concepts_normalized={len(concepts)}",
            ),
        )
