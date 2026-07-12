"""Configuración del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReasoningResultBuilderSettings:
    """Configuración del Reasoning Result Builder — fuente centralizada."""

    enabled: bool = True
    preserve_input_immutability: bool = True
    max_results_per_process: int = 5_000
    organized_result_builder_enabled: bool = True
    result_id_prefix: str = "RRB"
    result_id_padding: int = 6
    integration_certification_framework_prepared: bool = True

    @classmethod
    def default(cls) -> ReasoningResultBuilderSettings:
        return cls()


@dataclass(frozen=True)
class TraceabilityManagementEngineSettings:
    """Configuración del Traceability Management Engine — fuente centralizada."""

    enabled: bool = False
    prepared: bool = True

    @classmethod
    def default(cls) -> TraceabilityManagementEngineSettings:
        return cls()


@dataclass(frozen=True)
class ConfidenceManagementEngineSettings:
    """Configuración del Confidence Management Engine — fuente centralizada."""

    enabled: bool = False
    traceability_management_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ConfidenceManagementEngineSettings:
        return cls()


@dataclass(frozen=True)
class RecommendationGenerationEngineSettings:
    """Configuración del Recommendation Generation Engine — fuente centralizada."""

    enabled: bool = True
    preserve_input_immutability: bool = True
    max_profiles_per_process: int = 5_000
    organized_recommendation_generator_enabled: bool = True
    min_evidence_for_recommendation: int = 1
    clear_winner_score_gap: float = 2.0
    equivalence_score_threshold: float = 1.0
    insufficient_missing_ratio: float = 0.6
    high_confidence_min_coverage: float = 0.8
    medium_confidence_min_coverage: float = 0.5
    high_confidence_max_risks: int = 2
    high_confidence_max_context_gaps: int = 1
    high_confidence_max_inconsistencies: int = 1
    reasoning_result_builder_prepared: bool = True

    @classmethod
    def default(cls) -> RecommendationGenerationEngineSettings:
        return cls()


@dataclass(frozen=True)
class ConclusionGenerationEngineSettings:
    """Configuración del Conclusion Generation Engine — fuente centralizada."""

    enabled: bool = False
    recommendation_generation_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ConclusionGenerationEngineSettings:
        return cls()


@dataclass(frozen=True)
class ExplanationGenerationEngineSettings:
    """Configuración del Explanation Generation Engine — fuente centralizada."""

    enabled: bool = True
    preserve_input_immutability: bool = True
    max_profiles_per_process: int = 5_000
    organized_explanation_generator_enabled: bool = True
    generate_summary_sections: bool = True
    generate_evidence_sections: bool = True
    generate_strength_sections: bool = True
    generate_weakness_sections: bool = True
    generate_risk_sections: bool = True
    generate_consistency_sections: bool = True
    generate_context_sections: bool = True
    generate_missing_information_sections: bool = True
    generate_limitation_sections: bool = True
    segment_id_prefix: str = "EGE"
    segment_id_padding: int = 6
    recommendation_generation_engine_prepared: bool = True
    conclusion_generation_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ExplanationGenerationEngineSettings:
        return cls()


@dataclass(frozen=True)
class ContextEvaluationEngineSettings:
    """Configuración del Context Evaluation Engine — fuente centralizada."""

    enabled: bool = True
    preserve_input_immutability: bool = True
    max_profiles_per_process: int = 5_000
    organized_context_evaluator_enabled: bool = True
    detect_commercial_alignment: bool = True
    detect_technical_alignment: bool = True
    detect_context_gaps: bool = True
    detect_context_limitations: bool = True
    detect_quotation_alignment: bool = True
    association_id_prefix: str = "CXEE"
    association_id_padding: int = 6
    gap_id_prefix: str = "CXEE"
    gap_id_padding: int = 6
    explanation_generation_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ContextEvaluationEngineSettings:
        return cls()


@dataclass(frozen=True)
class RiskAnalysisEngineSettings:
    """Configuración del Risk Analysis Engine — fuente centralizada."""

    enabled: bool = True
    preserve_input_immutability: bool = True
    max_profiles_per_process: int = 5_000
    organized_evidence_risk_analyzer_enabled: bool = True
    detect_documentation_risks: bool = True
    detect_consistency_risks: bool = True
    detect_information_risks: bool = True
    detect_commercial_risks: bool = True
    detect_technical_risks: bool = True
    risk_id_prefix: str = "RAE"
    risk_id_padding: int = 6
    context_evaluation_engine_prepared: bool = True

    @classmethod
    def default(cls) -> RiskAnalysisEngineSettings:
        return cls()


@dataclass(frozen=True)
class ConsistencyEvaluationEngineSettings:
    """Configuración del Consistency Evaluation Engine — fuente centralizada."""

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_profiles_per_process: int = 5_000
    organized_evidence_evaluator_enabled: bool = True
    detect_commercial_technical_contradictions: bool = True
    detect_provider_attribute_differences: bool = True
    detect_integrity_violations: bool = True
    detect_incomplete_references: bool = True
    detect_contradictions: bool = True
    block_on_contradictions: bool = True
    max_missing_evidence_for_sufficiency: int = 50
    max_inconsistencies_for_sufficiency: int = 100
    inconsistency_id_prefix: str = "CEE"
    inconsistency_id_padding: int = 6
    risk_analysis_engine_prepared: bool = True

    @classmethod
    def default(cls) -> ConsistencyEvaluationEngineSettings:
        return cls()


@dataclass(frozen=True)
class EvidenceAnalysisEngineSettings:
    """Configuración del Evidence Analysis Engine — fuente centralizada."""

    enabled: bool = True
    preserve_catalog_immutability: bool = True
    max_models_per_process: int = 5_000
    max_evidence_records_per_model: int = 50_000
    definitive_model_evidence_analyzer_enabled: bool = True
    detect_missing_categories: bool = True
    detect_missing_cell_values: bool = True
    evidence_id_prefix: str = "EAE"
    evidence_id_padding: int = 6
    missing_evidence_id_prefix: str = "EAE"
    missing_evidence_id_padding: int = 6
    consistency_evaluation_engine_prepared: bool = True

    @classmethod
    def default(cls) -> EvidenceAnalysisEngineSettings:
        return cls()


@dataclass(frozen=True)
class IntelligentAnalysisSettings:
    """
    Configuración de Razonamiento Inteligente — fuente centralizada.

    Sin activar razonamiento completo en esta etapa.
    """

    enabled: bool = False
    max_models_per_process: int = 5_000
    max_analyses_per_process: int = 5_000
    comparative_tables_integration_prepared: bool = True
    comparative_tables_enabled: bool = False
    pm7_input_contract_required: bool = True
    integration_certification_framework_prepared: bool = True
    evidence_analysis_engine: EvidenceAnalysisEngineSettings = field(
        default_factory=EvidenceAnalysisEngineSettings.default,
    )
    consistency_evaluation_engine: ConsistencyEvaluationEngineSettings = field(
        default_factory=ConsistencyEvaluationEngineSettings.default,
    )
    risk_analysis_engine: RiskAnalysisEngineSettings = field(
        default_factory=RiskAnalysisEngineSettings.default,
    )
    context_evaluation_engine: ContextEvaluationEngineSettings = field(
        default_factory=ContextEvaluationEngineSettings.default,
    )
    explanation_generation_engine: ExplanationGenerationEngineSettings = field(
        default_factory=ExplanationGenerationEngineSettings.default,
    )
    conclusion_generation_engine: ConclusionGenerationEngineSettings = field(
        default_factory=ConclusionGenerationEngineSettings.default,
    )
    recommendation_generation_engine: RecommendationGenerationEngineSettings = field(
        default_factory=RecommendationGenerationEngineSettings.default,
    )
    reasoning_result_builder: ReasoningResultBuilderSettings = field(
        default_factory=ReasoningResultBuilderSettings.default,
    )
    confidence_management_engine: ConfidenceManagementEngineSettings = field(
        default_factory=ConfidenceManagementEngineSettings.default,
    )
    traceability_management_engine: TraceabilityManagementEngineSettings = field(
        default_factory=TraceabilityManagementEngineSettings.default,
    )

    @classmethod
    def default(cls) -> IntelligentAnalysisSettings:
        return cls()
