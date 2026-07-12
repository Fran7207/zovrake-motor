"""Configuración del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConceptAnalysisSettings:
    """
    Configuración del Concept Analysis Engine — fuente centralizada.

    Sin activar clasificación material/servicio en esta etapa.
    """

    enabled: bool = True
    preserve_model_immutability: bool = True
    max_concepts_per_process: int = 10_000
    item_detector_enabled: bool = True
    technical_detector_enabled: bool = True
    commercial_detector_enabled: bool = True
    condition_detector_enabled: bool = True
    observation_detector_enabled: bool = True
    material_classification_prepared: bool = True
    service_classification_prepared: bool = True
    normalization_prepared: bool = True

    @classmethod
    def default(cls) -> ConceptAnalysisSettings:
        return cls()


@dataclass(frozen=True)
class MaterialClassificationSettings:
    """
    Configuración del Material Classification Engine — fuente centralizada.

    Sin activar clasificación de servicios ni equivalencias en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_materials_per_process: int = 10_000
    item_classifier_enabled: bool = True
    partida_classifier_enabled: bool = True
    service_classification_prepared: bool = True
    normalization_prepared: bool = True
    equivalence_detection_prepared: bool = True
    comparable_group_builder_prepared: bool = True

    @classmethod
    def default(cls) -> MaterialClassificationSettings:
        return cls()


@dataclass(frozen=True)
class ServiceClassificationSettings:
    """
    Configuración del Service Classification Engine — fuente centralizada.

    Sin activar normalización ni equivalencias en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_services_per_process: int = 10_000
    commercial_condition_classifier_enabled: bool = True
    observation_classifier_enabled: bool = True
    technical_element_classifier_enabled: bool = True
    normalization_prepared: bool = True
    equivalence_detection_prepared: bool = True
    comparable_group_builder_prepared: bool = True

    @classmethod
    def default(cls) -> ServiceClassificationSettings:
        return cls()


@dataclass(frozen=True)
class ConceptNormalizationSettings:
    """
    Configuración del Concept Normalization Engine — fuente centralizada.

    Sin activar detección de equivalencias ni agrupación en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_normalized_concepts_per_process: int = 10_000
    material_normalizer_enabled: bool = True
    partida_normalizer_enabled: bool = True
    service_normalizer_enabled: bool = True
    technical_element_normalizer_enabled: bool = True
    commercial_element_normalizer_enabled: bool = True
    specification_normalizer_enabled: bool = True
    equivalence_detection_prepared: bool = True
    comparable_group_builder_prepared: bool = True

    @classmethod
    def default(cls) -> ConceptNormalizationSettings:
        return cls()


@dataclass(frozen=True)
class EquivalenceDetectionSettings:
    """
    Configuración del Equivalence Detection Engine — fuente centralizada.

    Sin activar agrupación ni asociación de contexto en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_equivalences_per_process: int = 10_000
    exact_match_detector_enabled: bool = True
    cross_type_distinct_detector_enabled: bool = True
    shared_origin_relation_detector_enabled: bool = True
    comparable_group_builder_prepared: bool = True
    context_association_prepared: bool = True
    comparative_domain_model_prepared: bool = True

    @classmethod
    def default(cls) -> EquivalenceDetectionSettings:
        return cls()


@dataclass(frozen=True)
class ComparableGroupBuilderSettings:
    """
    Configuración del Comparable Group Builder — fuente centralizada.

    Sin activar asociación de contexto ni modelo comparativo en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_groups_per_process: int = 5_000
    equivalence_cluster_builder_enabled: bool = True
    group_id_prefix: str = "GC"
    group_id_padding: int = 6
    group_id_immutable: bool = True
    min_members_per_group: int = 1
    context_association_prepared: bool = True
    comparative_domain_model_prepared: bool = True

    @classmethod
    def default(cls) -> ComparableGroupBuilderSettings:
        return cls()


@dataclass(frozen=True)
class ContextAssociationSettings:
    """
    Configuración del Context Association Engine — fuente centralizada.

    Sin activar construcción del modelo comparativo en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    preserve_context_immutability: bool = True
    max_associations_per_process: int = 5_000
    uniform_group_context_associator_enabled: bool = True
    comparative_domain_model_prepared: bool = True

    @classmethod
    def default(cls) -> ContextAssociationSettings:
        return cls()


@dataclass(frozen=True)
class ComparativeDomainModelBuilderSettings:
    """
    Configuración del Comparative Domain Model Builder — fuente centralizada.

    Define el contrato de salida oficial hacia el Prompt Maestro 6.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_models_per_process: int = 5_000
    group_context_aggregation_builder_enabled: bool = True
    model_id_prefix: str = "CDM"
    model_id_padding: int = 6
    model_id_immutable: bool = True
    default_confidence_level: str = "not_evaluated"
    pm6_output_contract: bool = True

    @classmethod
    def default(cls) -> ComparativeDomainModelBuilderSettings:
        return cls()


@dataclass(frozen=True)
class ClassificationQualityFrameworkSettings:
    """
    Configuración del Classification Quality Framework — fuente centralizada.

    Sin activar certificación final en esta etapa.
    """

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    model_consistency_validator_enabled: bool = True
    data_integrity_validator_enabled: bool = True
    identifier_uniqueness_validator_enabled: bool = True
    traceability_chain_validator_enabled: bool = True
    pipeline_flow_validator_enabled: bool = True
    require_related_context: bool = True
    require_pipeline_snapshot: bool = False
    allow_empty_catalog_validation: bool = True
    fail_on_error_findings: bool = True
    certification_prepared: bool = True

    @classmethod
    def default(cls) -> ClassificationQualityFrameworkSettings:
        return cls()


@dataclass(frozen=True)
class ClassificationSettings:
    """
    Configuración de Clasificación Inteligente — fuente centralizada.

    Sin activar clasificación de servicios, equivalencias ni agrupación en esta etapa.
    """

    enabled: bool = False
    max_concepts_per_process: int = 10_000
    max_materials_per_process: int = 10_000
    max_services_per_process: int = 10_000
    max_providers_per_process: int = 500
    max_groups_per_process: int = 5_000
    comprehension_integration_prepared: bool = True
    comprehension_enabled: bool = False
    concept_analysis: ConceptAnalysisSettings = field(default_factory=ConceptAnalysisSettings.default)
    material_classification: MaterialClassificationSettings = field(
        default_factory=MaterialClassificationSettings.default,
    )
    service_classification: ServiceClassificationSettings = field(
        default_factory=ServiceClassificationSettings.default,
    )
    concept_normalization: ConceptNormalizationSettings = field(
        default_factory=ConceptNormalizationSettings.default,
    )
    equivalence_detection: EquivalenceDetectionSettings = field(
        default_factory=EquivalenceDetectionSettings.default,
    )
    comparable_group_builder: ComparableGroupBuilderSettings = field(
        default_factory=ComparableGroupBuilderSettings.default,
    )
    context_association: ContextAssociationSettings = field(
        default_factory=ContextAssociationSettings.default,
    )
    comparative_domain_model_builder: ComparativeDomainModelBuilderSettings = field(
        default_factory=ComparativeDomainModelBuilderSettings.default,
    )
    classification_quality_framework: ClassificationQualityFrameworkSettings = field(
        default_factory=ClassificationQualityFrameworkSettings.default,
    )

    @classmethod
    def default(cls) -> ClassificationSettings:
        return cls()
