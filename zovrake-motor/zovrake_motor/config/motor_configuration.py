"""Configuración agregada del Motor Inteligente — fuente única de verdad."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zovrake_motor.config.categories import (
    BehaviorSettings,
    ClassificationSettings,
    CommunicationSettings,
    ComparativeTablesSettings,
    ComprehensionSettings,
    EventsSettings,
    FutureSettings,
    GeneralSettings,
    EnterpriseIntegrationSettings,
    IntelligentAnalysisSettings,
    PathsSettings,
    PerformanceSettings,
    ProcessingSettings,
    SecuritySettings,
)
from zovrake_motor.config.enums import ConfigCategory


@dataclass(frozen=True)
class MotorConfiguration:
    """
    Configuración completa del Motor Inteligente.

    Agrupa todas las categorías en un único objeto inmutable.
    """

    general: GeneralSettings = field(default_factory=GeneralSettings.default)
    paths: PathsSettings = field(default_factory=PathsSettings.default)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings.default)
    communication: CommunicationSettings = field(default_factory=CommunicationSettings.default)
    processing: ProcessingSettings = field(default_factory=ProcessingSettings.default)
    security: SecuritySettings = field(default_factory=SecuritySettings.default)
    events: EventsSettings = field(default_factory=EventsSettings.default)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings.default)
    comprehension: ComprehensionSettings = field(default_factory=ComprehensionSettings.default)
    classification: ClassificationSettings = field(default_factory=ClassificationSettings.default)
    comparative_tables: ComparativeTablesSettings = field(
        default_factory=ComparativeTablesSettings.default,
    )
    intelligent_analysis: IntelligentAnalysisSettings = field(
        default_factory=IntelligentAnalysisSettings.default,
    )
    enterprise_integration: EnterpriseIntegrationSettings = field(
        default_factory=EnterpriseIntegrationSettings.default,
    )
    future: FutureSettings = field(default_factory=FutureSettings.default)

    def get_category(self, category: ConfigCategory) -> Any:
        """Acceso uniforme por categoría."""
        mapping = {
            ConfigCategory.GENERAL: self.general,
            ConfigCategory.PATHS: self.paths,
            ConfigCategory.BEHAVIOR: self.behavior,
            ConfigCategory.COMMUNICATION: self.communication,
            ConfigCategory.PROCESSING: self.processing,
            ConfigCategory.SECURITY: self.security,
            ConfigCategory.EVENTS: self.events,
            ConfigCategory.PERFORMANCE: self.performance,
            ConfigCategory.COMPREHENSION: self.comprehension,
            ConfigCategory.CLASSIFICATION: self.classification,
            ConfigCategory.COMPARATIVE_TABLES: self.comparative_tables,
            ConfigCategory.INTELLIGENT_ANALYSIS: self.intelligent_analysis,
            ConfigCategory.ENTERPRISE_INTEGRATION: self.enterprise_integration,
            ConfigCategory.FUTURE: self.future,
        }
        return mapping[category]

    def to_dict(self) -> dict[str, Any]:
        return {
            "general": {
                "service_name": self.general.service_name,
                "service_version": self.general.service_version,
                "environment": self.general.environment.value,
            },
            "paths": {
                "data_root": self.paths.data_root,
                "temp_root": self.paths.temp_root,
                "logs_root": self.paths.logs_root,
            },
            "behavior": {
                "coordinator_enabled": self.behavior.coordinator_enabled,
                "strict_module_validation": self.behavior.strict_module_validation,
            },
            "communication": {
                "enabled": self.communication.enabled,
                "protocol": self.communication.protocol,
            },
            "processing": {
                "enabled": self.processing.enabled,
                "max_concurrent_processes": self.processing.max_concurrent_processes,
            },
            "security": {
                "enabled": self.security.enabled,
                "require_module_validation": self.security.require_module_validation,
            },
            "events": {
                "logging_enabled": self.events.logging_enabled,
                "max_events_in_memory": self.events.max_events_in_memory,
            },
            "performance": {
                "monitoring_enabled": self.performance.monitoring_enabled,
                "metrics_collection_enabled": self.performance.metrics_collection_enabled,
            },
            "comprehension": {
                "enabled": self.comprehension.enabled,
                "max_documents_per_process": self.comprehension.max_documents_per_process,
                "supported_formats": list(self.comprehension.supported_formats),
                "adapters": {
                    "enabled": self.comprehension.adapters.enabled,
                    "auto_resolution_enabled": self.comprehension.adapters.auto_resolution_enabled,
                    "pdf_enabled": self.comprehension.adapters.pdf_enabled,
                    "word_enabled": self.comprehension.adapters.word_enabled,
                    "excel_enabled": self.comprehension.adapters.excel_enabled,
                    "image_enabled": self.comprehension.adapters.image_enabled,
                },
                "validation": {
                    "enabled": self.comprehension.validation.enabled,
                    "strict_mode": self.comprehension.validation.strict_mode,
                    "max_file_size_bytes": self.comprehension.validation.max_file_size_bytes,
                    "min_file_size_bytes": self.comprehension.validation.min_file_size_bytes,
                    "supported_formats": list(self.comprehension.validation.supported_formats),
                },
                "recognition": {
                    "enabled": self.comprehension.recognition.enabled,
                    "min_confidence_threshold": self.comprehension.recognition.min_confidence_threshold,
                    "extension_strategy_enabled": self.comprehension.recognition.extension_strategy_enabled,
                    "mime_type_strategy_enabled": self.comprehension.recognition.mime_type_strategy_enabled,
                    "metadata_strategy_enabled": self.comprehension.recognition.metadata_strategy_enabled,
                    "magic_number_strategy_enabled": self.comprehension.recognition.magic_number_strategy_enabled,
                    "supported_formats": list(self.comprehension.recognition.supported_formats),
                },
                "extraction": {
                    "enabled": self.comprehension.extraction.enabled,
                    "preserve_original": self.comprehension.extraction.preserve_original,
                    "ocr_integration_prepared": self.comprehension.extraction.ocr_integration_prepared,
                    "ocr_enabled": self.comprehension.extraction.ocr_enabled,
                    "text_extractor_enabled": self.comprehension.extraction.text_extractor_enabled,
                    "tables_extractor_enabled": self.comprehension.extraction.tables_extractor_enabled,
                    "metadata_extractor_enabled": self.comprehension.extraction.metadata_extractor_enabled,
                    "headers_extractor_enabled": self.comprehension.extraction.headers_extractor_enabled,
                    "footers_extractor_enabled": self.comprehension.extraction.footers_extractor_enabled,
                    "lists_extractor_enabled": self.comprehension.extraction.lists_extractor_enabled,
                    "embedded_images_extractor_enabled": self.comprehension.extraction.embedded_images_extractor_enabled,
                    "structural_elements_extractor_enabled": self.comprehension.extraction.structural_elements_extractor_enabled,
                },
                "canonical": {
                    "enabled": self.comprehension.canonical.enabled,
                    "preserve_immutability": self.comprehension.canonical.preserve_immutability,
                    "classification_integration_prepared": self.comprehension.canonical.classification_integration_prepared,
                    "classification_enabled": self.comprehension.canonical.classification_enabled,
                    "provider_transformer_enabled": self.comprehension.canonical.provider_transformer_enabled,
                    "commercial_transformer_enabled": self.comprehension.canonical.commercial_transformer_enabled,
                    "technical_transformer_enabled": self.comprehension.canonical.technical_transformer_enabled,
                    "items_transformer_enabled": self.comprehension.canonical.items_transformer_enabled,
                    "conditions_transformer_enabled": self.comprehension.canonical.conditions_transformer_enabled,
                    "observations_transformer_enabled": self.comprehension.canonical.observations_transformer_enabled,
                    "metadata_transformer_enabled": self.comprehension.canonical.metadata_transformer_enabled,
                },
                "internal_model": {
                    "enabled": self.comprehension.internal_model.enabled,
                    "preserve_immutability": self.comprehension.internal_model.preserve_immutability,
                    "classification_integration_prepared": self.comprehension.internal_model.classification_integration_prepared,
                    "classification_enabled": self.comprehension.internal_model.classification_enabled,
                    "document_builder_enabled": self.comprehension.internal_model.document_builder_enabled,
                    "provider_builder_enabled": self.comprehension.internal_model.provider_builder_enabled,
                    "commercial_builder_enabled": self.comprehension.internal_model.commercial_builder_enabled,
                    "technical_builder_enabled": self.comprehension.internal_model.technical_builder_enabled,
                    "items_builder_enabled": self.comprehension.internal_model.items_builder_enabled,
                    "conditions_builder_enabled": self.comprehension.internal_model.conditions_builder_enabled,
                    "observations_builder_enabled": self.comprehension.internal_model.observations_builder_enabled,
                    "metadata_builder_enabled": self.comprehension.internal_model.metadata_builder_enabled,
                    "requirement_context_builder_enabled": self.comprehension.internal_model.requirement_context_builder_enabled,
                    "original_references_builder_enabled": self.comprehension.internal_model.original_references_builder_enabled,
                },
                "knowledge_index": {
                    "enabled": self.comprehension.knowledge_index.enabled,
                    "prevent_duplicates": self.comprehension.knowledge_index.prevent_duplicates,
                    "query_integration_prepared": self.comprehension.knowledge_index.query_integration_prepared,
                    "reuse_integration_prepared": self.comprehension.knowledge_index.reuse_integration_prepared,
                    "query_enabled": self.comprehension.knowledge_index.query_enabled,
                    "reuse_enabled": self.comprehension.knowledge_index.reuse_enabled,
                    "max_entries_in_memory": self.comprehension.knowledge_index.max_entries_in_memory,
                },
                "context_integration": {
                    "enabled": self.comprehension.context_integration.enabled,
                    "preserve_document_immutability": self.comprehension.context_integration.preserve_document_immutability,
                    "dki_association_prepared": self.comprehension.context_integration.dki_association_prepared,
                    "classification_integration_prepared": self.comprehension.context_integration.classification_integration_prepared,
                    "reasoning_integration_prepared": self.comprehension.context_integration.reasoning_integration_prepared,
                    "classification_enabled": self.comprehension.context_integration.classification_enabled,
                    "reasoning_enabled": self.comprehension.context_integration.reasoning_enabled,
                    "max_associations_in_memory": self.comprehension.context_integration.max_associations_in_memory,
                },
            },
            "comparative_tables": {
                "enabled": self.comparative_tables.enabled,
                "max_tables_per_process": self.comparative_tables.max_tables_per_process,
                "max_groups_per_process": self.comparative_tables.max_groups_per_process,
                "max_providers_per_process": self.comparative_tables.max_providers_per_process,
                "classification_integration_prepared": (
                    self.comparative_tables.classification_integration_prepared
                ),
                "classification_enabled": self.comparative_tables.classification_enabled,
                "pm6_output_contract_required": self.comparative_tables.pm6_output_contract_required,
                "comparative_structure_engine": {
                    "enabled": self.comparative_tables.comparative_structure_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.comparative_structure_engine.preserve_catalog_immutability
                    ),
                    "max_structures_per_process": (
                        self.comparative_tables.comparative_structure_engine.max_structures_per_process
                    ),
                    "domain_model_group_structure_builder_enabled": (
                        self.comparative_tables.comparative_structure_engine.domain_model_group_structure_builder_enabled
                    ),
                    "structure_id_prefix": (
                        self.comparative_tables.comparative_structure_engine.structure_id_prefix
                    ),
                    "structure_id_padding": (
                        self.comparative_tables.comparative_structure_engine.structure_id_padding
                    ),
                    "structure_id_immutable": (
                        self.comparative_tables.comparative_structure_engine.structure_id_immutable
                    ),
                    "dynamic_column_builder_prepared": (
                        self.comparative_tables.comparative_structure_engine.dynamic_column_builder_prepared
                    ),
                    "dynamic_row_builder_prepared": (
                        self.comparative_tables.comparative_structure_engine.dynamic_row_builder_prepared
                    ),
                },
                "dynamic_column_builder": {
                    "enabled": self.comparative_tables.dynamic_column_builder.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.dynamic_column_builder.preserve_catalog_immutability
                    ),
                    "max_columns_per_process": (
                        self.comparative_tables.dynamic_column_builder.max_columns_per_process
                    ),
                    "structure_attribute_column_builder_enabled": (
                        self.comparative_tables.dynamic_column_builder.structure_attribute_column_builder_enabled
                    ),
                    "column_id_prefix": self.comparative_tables.dynamic_column_builder.column_id_prefix,
                    "column_id_padding": self.comparative_tables.dynamic_column_builder.column_id_padding,
                    "column_id_immutable": self.comparative_tables.dynamic_column_builder.column_id_immutable,
                    "dynamic_row_builder_prepared": (
                        self.comparative_tables.dynamic_column_builder.dynamic_row_builder_prepared
                    ),
                },
                "dynamic_row_builder": {
                    "enabled": self.comparative_tables.dynamic_row_builder.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.dynamic_row_builder.preserve_catalog_immutability
                    ),
                    "max_rows_per_process": (
                        self.comparative_tables.dynamic_row_builder.max_rows_per_process
                    ),
                    "provider_row_builder_enabled": (
                        self.comparative_tables.dynamic_row_builder.provider_row_builder_enabled
                    ),
                    "row_id_prefix": self.comparative_tables.dynamic_row_builder.row_id_prefix,
                    "row_id_padding": self.comparative_tables.dynamic_row_builder.row_id_padding,
                    "row_id_immutable": self.comparative_tables.dynamic_row_builder.row_id_immutable,
                    "provider_organization_engine_prepared": (
                        self.comparative_tables.dynamic_row_builder.provider_organization_engine_prepared
                    ),
                },
                "provider_organization_engine": {
                    "enabled": self.comparative_tables.provider_organization_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.provider_organization_engine.preserve_catalog_immutability
                    ),
                    "max_providers_per_organization": (
                        self.comparative_tables.provider_organization_engine.max_providers_per_organization
                    ),
                    "group_provider_organizer_enabled": (
                        self.comparative_tables.provider_organization_engine.group_provider_organizer_enabled
                    ),
                    "organization_id_prefix": (
                        self.comparative_tables.provider_organization_engine.organization_id_prefix
                    ),
                    "organization_id_padding": (
                        self.comparative_tables.provider_organization_engine.organization_id_padding
                    ),
                    "organization_id_immutable": (
                        self.comparative_tables.provider_organization_engine.organization_id_immutable
                    ),
                    "deterministic_sort_enabled": (
                        self.comparative_tables.provider_organization_engine.deterministic_sort_enabled
                    ),
                    "group_integrity_engine_prepared": (
                        self.comparative_tables.provider_organization_engine.group_integrity_engine_prepared
                    ),
                },
                "group_integrity_engine": {
                    "enabled": self.comparative_tables.group_integrity_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.group_integrity_engine.preserve_catalog_immutability
                    ),
                    "max_findings_per_report": (
                        self.comparative_tables.group_integrity_engine.max_findings_per_report
                    ),
                    "comparative_table_integrity_validator_enabled": (
                        self.comparative_tables.group_integrity_engine.comparative_table_integrity_validator_enabled
                    ),
                    "finding_id_prefix": self.comparative_tables.group_integrity_engine.finding_id_prefix,
                    "finding_id_padding": self.comparative_tables.group_integrity_engine.finding_id_padding,
                    "max_errors_before_invalid": (
                        self.comparative_tables.group_integrity_engine.max_errors_before_invalid
                    ),
                    "traceability_metadata_engine_prepared": (
                        self.comparative_tables.group_integrity_engine.traceability_metadata_engine_prepared
                    ),
                },
                "traceability_metadata_engine": {
                    "enabled": self.comparative_tables.traceability_metadata_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.traceability_metadata_engine.preserve_catalog_immutability
                    ),
                    "max_enriched_tables_per_process": (
                        self.comparative_tables.traceability_metadata_engine.max_enriched_tables_per_process
                    ),
                    "comparative_table_metadata_enricher_enabled": (
                        self.comparative_tables.traceability_metadata_engine.comparative_table_metadata_enricher_enabled
                    ),
                    "enrichment_id_prefix": (
                        self.comparative_tables.traceability_metadata_engine.enrichment_id_prefix
                    ),
                    "enrichment_id_padding": (
                        self.comparative_tables.traceability_metadata_engine.enrichment_id_padding
                    ),
                    "comparative_model_builder_prepared": (
                        self.comparative_tables.traceability_metadata_engine.comparative_model_builder_prepared
                    ),
                },
                "comparative_model_builder": {
                    "enabled": self.comparative_tables.comparative_model_builder.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.comparative_model_builder.preserve_catalog_immutability
                    ),
                    "max_models_per_process": (
                        self.comparative_tables.comparative_model_builder.max_models_per_process
                    ),
                    "group_comparative_model_builder_enabled": (
                        self.comparative_tables.comparative_model_builder.group_comparative_model_builder_enabled
                    ),
                    "definitive_model_id_prefix": (
                        self.comparative_tables.comparative_model_builder.definitive_model_id_prefix
                    ),
                    "definitive_model_id_padding": (
                        self.comparative_tables.comparative_model_builder.definitive_model_id_padding
                    ),
                    "comparative_validation_framework_prepared": (
                        self.comparative_tables.comparative_model_builder.comparative_validation_framework_prepared
                    ),
                },
                "comparative_validation_framework": {
                    "enabled": self.comparative_tables.comparative_validation_framework.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.comparative_validation_framework.preserve_catalog_immutability
                    ),
                    "max_findings_per_report": (
                        self.comparative_tables.comparative_validation_framework.max_findings_per_report
                    ),
                    "definitive_comparative_model_validator_enabled": (
                        self.comparative_tables.comparative_validation_framework.definitive_comparative_model_validator_enabled
                    ),
                    "finding_id_prefix": (
                        self.comparative_tables.comparative_validation_framework.finding_id_prefix
                    ),
                    "finding_id_padding": (
                        self.comparative_tables.comparative_validation_framework.finding_id_padding
                    ),
                    "max_errors_before_invalid": (
                        self.comparative_tables.comparative_validation_framework.max_errors_before_invalid
                    ),
                    "comparative_quality_framework_prepared": (
                        self.comparative_tables.comparative_validation_framework.comparative_quality_framework_prepared
                    ),
                },
                "comparative_quality_framework": {
                    "enabled": self.comparative_tables.comparative_quality_framework.enabled,
                    "preserve_catalog_immutability": (
                        self.comparative_tables.comparative_quality_framework.preserve_catalog_immutability
                    ),
                    "architectural_compliance_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.architectural_compliance_validator_enabled
                    ),
                    "definitive_model_consistency_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.definitive_model_consistency_validator_enabled
                    ),
                    "validation_report_integrity_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.validation_report_integrity_validator_enabled
                    ),
                    "identifier_uniqueness_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.identifier_uniqueness_validator_enabled
                    ),
                    "traceability_chain_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.traceability_chain_validator_enabled
                    ),
                    "pipeline_flow_validator_enabled": (
                        self.comparative_tables.comparative_quality_framework.pipeline_flow_validator_enabled
                    ),
                    "module_certification_prepared": (
                        self.comparative_tables.comparative_quality_framework.module_certification_prepared
                    ),
                },
            },
            "intelligent_analysis": {
                "enabled": self.intelligent_analysis.enabled,
                "max_models_per_process": self.intelligent_analysis.max_models_per_process,
                "max_analyses_per_process": self.intelligent_analysis.max_analyses_per_process,
                "comparative_tables_integration_prepared": (
                    self.intelligent_analysis.comparative_tables_integration_prepared
                ),
                "comparative_tables_enabled": self.intelligent_analysis.comparative_tables_enabled,
                "pm7_input_contract_required": self.intelligent_analysis.pm7_input_contract_required,
                "integration_certification_framework_prepared": (
                    self.intelligent_analysis.integration_certification_framework_prepared
                ),
                "evidence_analysis_engine": {
                    "enabled": self.intelligent_analysis.evidence_analysis_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.intelligent_analysis.evidence_analysis_engine.preserve_catalog_immutability
                    ),
                    "max_models_per_process": (
                        self.intelligent_analysis.evidence_analysis_engine.max_models_per_process
                    ),
                    "definitive_model_evidence_analyzer_enabled": (
                        self.intelligent_analysis.evidence_analysis_engine.definitive_model_evidence_analyzer_enabled
                    ),
                    "detect_missing_categories": (
                        self.intelligent_analysis.evidence_analysis_engine.detect_missing_categories
                    ),
                    "detect_missing_cell_values": (
                        self.intelligent_analysis.evidence_analysis_engine.detect_missing_cell_values
                    ),
                    "consistency_evaluation_engine_prepared": (
                        self.intelligent_analysis.evidence_analysis_engine.consistency_evaluation_engine_prepared
                    ),
                },
                "consistency_evaluation_engine": {
                    "enabled": self.intelligent_analysis.consistency_evaluation_engine.enabled,
                    "preserve_catalog_immutability": (
                        self.intelligent_analysis.consistency_evaluation_engine.preserve_catalog_immutability
                    ),
                    "organized_evidence_evaluator_enabled": (
                        self.intelligent_analysis.consistency_evaluation_engine.organized_evidence_evaluator_enabled
                    ),
                    "detect_commercial_technical_contradictions": (
                        self.intelligent_analysis.consistency_evaluation_engine.detect_commercial_technical_contradictions
                    ),
                    "detect_provider_attribute_differences": (
                        self.intelligent_analysis.consistency_evaluation_engine.detect_provider_attribute_differences
                    ),
                    "detect_integrity_violations": (
                        self.intelligent_analysis.consistency_evaluation_engine.detect_integrity_violations
                    ),
                    "detect_incomplete_references": (
                        self.intelligent_analysis.consistency_evaluation_engine.detect_incomplete_references
                    ),
                    "detect_contradictions": (
                        self.intelligent_analysis.consistency_evaluation_engine.detect_contradictions
                    ),
                    "risk_analysis_engine_prepared": (
                        self.intelligent_analysis.consistency_evaluation_engine.risk_analysis_engine_prepared
                    ),
                },
                "risk_analysis_engine": {
                    "enabled": self.intelligent_analysis.risk_analysis_engine.enabled,
                    "preserve_input_immutability": (
                        self.intelligent_analysis.risk_analysis_engine.preserve_input_immutability
                    ),
                    "organized_evidence_risk_analyzer_enabled": (
                        self.intelligent_analysis.risk_analysis_engine.organized_evidence_risk_analyzer_enabled
                    ),
                    "detect_documentation_risks": (
                        self.intelligent_analysis.risk_analysis_engine.detect_documentation_risks
                    ),
                    "detect_consistency_risks": (
                        self.intelligent_analysis.risk_analysis_engine.detect_consistency_risks
                    ),
                    "detect_information_risks": (
                        self.intelligent_analysis.risk_analysis_engine.detect_information_risks
                    ),
                    "detect_commercial_risks": (
                        self.intelligent_analysis.risk_analysis_engine.detect_commercial_risks
                    ),
                    "detect_technical_risks": (
                        self.intelligent_analysis.risk_analysis_engine.detect_technical_risks
                    ),
                    "context_evaluation_engine_prepared": (
                        self.intelligent_analysis.risk_analysis_engine.context_evaluation_engine_prepared
                    ),
                },
                "context_evaluation_engine": {
                    "enabled": self.intelligent_analysis.context_evaluation_engine.enabled,
                    "preserve_input_immutability": (
                        self.intelligent_analysis.context_evaluation_engine.preserve_input_immutability
                    ),
                    "organized_context_evaluator_enabled": (
                        self.intelligent_analysis.context_evaluation_engine.organized_context_evaluator_enabled
                    ),
                    "detect_commercial_alignment": (
                        self.intelligent_analysis.context_evaluation_engine.detect_commercial_alignment
                    ),
                    "detect_technical_alignment": (
                        self.intelligent_analysis.context_evaluation_engine.detect_technical_alignment
                    ),
                    "detect_context_gaps": (
                        self.intelligent_analysis.context_evaluation_engine.detect_context_gaps
                    ),
                    "detect_context_limitations": (
                        self.intelligent_analysis.context_evaluation_engine.detect_context_limitations
                    ),
                    "detect_quotation_alignment": (
                        self.intelligent_analysis.context_evaluation_engine.detect_quotation_alignment
                    ),
                    "explanation_generation_engine_prepared": (
                        self.intelligent_analysis.context_evaluation_engine.explanation_generation_engine_prepared
                    ),
                },
                "explanation_generation_engine": {
                    "enabled": self.intelligent_analysis.explanation_generation_engine.enabled,
                    "preserve_input_immutability": (
                        self.intelligent_analysis.explanation_generation_engine.preserve_input_immutability
                    ),
                    "organized_explanation_generator_enabled": (
                        self.intelligent_analysis.explanation_generation_engine.organized_explanation_generator_enabled
                    ),
                    "generate_summary_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_summary_sections
                    ),
                    "generate_evidence_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_evidence_sections
                    ),
                    "generate_strength_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_strength_sections
                    ),
                    "generate_weakness_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_weakness_sections
                    ),
                    "generate_risk_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_risk_sections
                    ),
                    "generate_consistency_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_consistency_sections
                    ),
                    "generate_context_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_context_sections
                    ),
                    "generate_missing_information_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_missing_information_sections
                    ),
                    "generate_limitation_sections": (
                        self.intelligent_analysis.explanation_generation_engine.generate_limitation_sections
                    ),
                    "recommendation_generation_engine_prepared": (
                        self.intelligent_analysis.explanation_generation_engine.recommendation_generation_engine_prepared
                    ),
                    "conclusion_generation_engine_prepared": (
                        self.intelligent_analysis.explanation_generation_engine.conclusion_generation_engine_prepared
                    ),
                },
                "conclusion_generation_engine": {
                    "enabled": self.intelligent_analysis.conclusion_generation_engine.enabled,
                    "recommendation_generation_engine_prepared": (
                        self.intelligent_analysis.conclusion_generation_engine.recommendation_generation_engine_prepared
                    ),
                },
                "recommendation_generation_engine": {
                    "enabled": self.intelligent_analysis.recommendation_generation_engine.enabled,
                    "preserve_input_immutability": (
                        self.intelligent_analysis.recommendation_generation_engine.preserve_input_immutability
                    ),
                    "organized_recommendation_generator_enabled": (
                        self.intelligent_analysis.recommendation_generation_engine.organized_recommendation_generator_enabled
                    ),
                    "min_evidence_for_recommendation": (
                        self.intelligent_analysis.recommendation_generation_engine.min_evidence_for_recommendation
                    ),
                    "clear_winner_score_gap": (
                        self.intelligent_analysis.recommendation_generation_engine.clear_winner_score_gap
                    ),
                    "equivalence_score_threshold": (
                        self.intelligent_analysis.recommendation_generation_engine.equivalence_score_threshold
                    ),
                    "reasoning_result_builder_prepared": (
                        self.intelligent_analysis.recommendation_generation_engine.reasoning_result_builder_prepared
                    ),
                },
                "reasoning_result_builder": {
                    "enabled": self.intelligent_analysis.reasoning_result_builder.enabled,
                    "preserve_input_immutability": (
                        self.intelligent_analysis.reasoning_result_builder.preserve_input_immutability
                    ),
                    "max_results_per_process": (
                        self.intelligent_analysis.reasoning_result_builder.max_results_per_process
                    ),
                    "organized_result_builder_enabled": (
                        self.intelligent_analysis.reasoning_result_builder.organized_result_builder_enabled
                    ),
                    "result_id_prefix": self.intelligent_analysis.reasoning_result_builder.result_id_prefix,
                    "result_id_padding": (
                        self.intelligent_analysis.reasoning_result_builder.result_id_padding
                    ),
                    "integration_certification_framework_prepared": (
                        self.intelligent_analysis.reasoning_result_builder.integration_certification_framework_prepared
                    ),
                },
                "confidence_management_engine": {
                    "enabled": self.intelligent_analysis.confidence_management_engine.enabled,
                    "traceability_management_engine_prepared": (
                        self.intelligent_analysis.confidence_management_engine.traceability_management_engine_prepared
                    ),
                },
                "traceability_management_engine": {
                    "enabled": self.intelligent_analysis.traceability_management_engine.enabled,
                    "prepared": self.intelligent_analysis.traceability_management_engine.prepared,
                },
            },
            "enterprise_integration": {
                "enabled": self.enterprise_integration.enabled,
                "max_requests_per_process": self.enterprise_integration.max_requests_per_process,
                "max_concurrent_integrations": self.enterprise_integration.max_concurrent_integrations,
                "intelligent_analysis_integration_prepared": (
                    self.enterprise_integration.intelligent_analysis_integration_prepared
                ),
                "intelligent_analysis_enabled": self.enterprise_integration.intelligent_analysis_enabled,
                "pm8_input_contract_required": self.enterprise_integration.pm8_input_contract_required,
                "erp_communication_gateway": {
                    "enabled": self.enterprise_integration.erp_communication_gateway.enabled,
                    "prepared": self.enterprise_integration.erp_communication_gateway.prepared,
                    "evidence_center_integration_prepared": (
                        self.enterprise_integration.erp_communication_gateway.evidence_center_integration_prepared
                    ),
                    "immutability_enforced": (
                        self.enterprise_integration.erp_communication_gateway.immutability_enforced
                    ),
                    "http_transport_prepared": (
                        self.enterprise_integration.erp_communication_gateway.http_transport_prepared
                    ),
                    "queue_processing_prepared": (
                        self.enterprise_integration.erp_communication_gateway.queue_processing_prepared
                    ),
                    "authentication_prepared": (
                        self.enterprise_integration.erp_communication_gateway.authentication_prepared
                    ),
                },
                "async_processing_queue_manager": {
                    "enabled": self.enterprise_integration.async_processing_queue_manager.enabled,
                    "prepared": self.enterprise_integration.async_processing_queue_manager.prepared,
                    "in_memory_queue_prepared": (
                        self.enterprise_integration.async_processing_queue_manager.in_memory_queue_prepared
                    ),
                    "worker_prepared": (
                        self.enterprise_integration.async_processing_queue_manager.worker_prepared
                    ),
                    "max_queue_depth": (
                        self.enterprise_integration.async_processing_queue_manager.max_queue_depth
                    ),
                    "max_concurrent_workers": (
                        self.enterprise_integration.async_processing_queue_manager.max_concurrent_workers
                    ),
                    "priority_prepared": (
                        self.enterprise_integration.async_processing_queue_manager.priority_prepared
                    ),
                    "retry_prepared": (
                        self.enterprise_integration.async_processing_queue_manager.retry_prepared
                    ),
                    "distributed_processing_prepared": (
                        self.enterprise_integration.async_processing_queue_manager.distributed_processing_prepared
                    ),
                },
                "fault_tolerance_retry_recovery_framework": {
                    "enabled": self.enterprise_integration.fault_tolerance_retry_recovery_framework.enabled,
                    "prepared": self.enterprise_integration.fault_tolerance_retry_recovery_framework.prepared,
                    "error_classification_prepared": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.error_classification_prepared
                    ),
                    "retry_policies_prepared": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.retry_policies_prepared
                    ),
                    "default_max_retries": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.default_max_retries
                    ),
                    "recovery_prepared": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.recovery_prepared
                    ),
                    "process_isolation_enforced": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.process_isolation_enforced
                    ),
                    "circuit_breaker_prepared": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.circuit_breaker_prepared
                    ),
                    "dead_letter_queue_prepared": (
                        self.enterprise_integration.fault_tolerance_retry_recovery_framework.dead_letter_queue_prepared
                    ),
                },
                "security_validation_audit_framework": {
                    "enabled": self.enterprise_integration.security_validation_audit_framework.enabled,
                    "prepared": self.enterprise_integration.security_validation_audit_framework.prepared,
                    "validation_engine_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.validation_engine_prepared
                    ),
                    "integrity_validation_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.integrity_validation_prepared
                    ),
                    "audit_framework_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.audit_framework_prepared
                    ),
                    "oauth_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.oauth_prepared
                    ),
                    "jwt_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.jwt_prepared
                    ),
                    "rbac_prepared": (
                        self.enterprise_integration.security_validation_audit_framework.rbac_prepared
                    ),
                },
                "observability_metrics_monitoring_framework": {
                    "enabled": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.enabled
                    ),
                    "prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.prepared
                    ),
                    "metrics_collector_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.metrics_collector_prepared
                    ),
                    "trace_collector_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.trace_collector_prepared
                    ),
                    "performance_tracker_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.performance_tracker_prepared
                    ),
                    "health_monitor_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.health_monitor_prepared
                    ),
                    "opentelemetry_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.opentelemetry_prepared
                    ),
                    "prometheus_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.prometheus_prepared
                    ),
                    "grafana_prepared": (
                        self.enterprise_integration.observability_metrics_monitoring_framework.grafana_prepared
                    ),
                },
                "performance_optimization_scalability_framework": {
                    "enabled": (
                        self.enterprise_integration.performance_optimization_scalability_framework.enabled
                    ),
                    "prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.prepared
                    ),
                    "pipeline_optimization_prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.pipeline_optimization_prepared
                    ),
                    "resource_optimization_prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.resource_optimization_prepared
                    ),
                    "horizontal_scaling_prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.horizontal_scaling_prepared
                    ),
                    "load_balancing_prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.load_balancing_prepared
                    ),
                    "kubernetes_prepared": (
                        self.enterprise_integration.performance_optimization_scalability_framework.kubernetes_prepared
                    ),
                },
                "pipeline_integration_orchestrator": {
                    "enabled": self.enterprise_integration.pipeline_integration_orchestrator.enabled,
                    "prepared": self.enterprise_integration.pipeline_integration_orchestrator.prepared,
                    "deterministic_pipeline": (
                        self.enterprise_integration.pipeline_integration_orchestrator.deterministic_pipeline
                    ),
                    "async_processing_prepared": (
                        self.enterprise_integration.pipeline_integration_orchestrator.async_processing_prepared
                    ),
                    "retry_prepared": (
                        self.enterprise_integration.pipeline_integration_orchestrator.retry_prepared
                    ),
                    "cancellation_prepared": (
                        self.enterprise_integration.pipeline_integration_orchestrator.cancellation_prepared
                    ),
                },
                "internal_integration_api": {
                    "enabled": self.enterprise_integration.internal_integration_api.enabled,
                    "prepared": self.enterprise_integration.internal_integration_api.prepared,
                    "active_contract_version": (
                        self.enterprise_integration.internal_integration_api.active_contract_version
                    ),
                    "contract_versioning_prepared": (
                        self.enterprise_integration.internal_integration_api.contract_versioning_prepared
                    ),
                    "structural_validation_enabled": (
                        self.enterprise_integration.internal_integration_api.structural_validation_enabled
                    ),
                },
                "api_gateway_internal": {
                    "enabled": self.enterprise_integration.api_gateway_internal.enabled,
                    "prepared": self.enterprise_integration.api_gateway_internal.prepared,
                },
                "request_dispatcher": {
                    "enabled": self.enterprise_integration.request_dispatcher.enabled,
                    "prepared": self.enterprise_integration.request_dispatcher.prepared,
                },
                "response_dispatcher": {
                    "enabled": self.enterprise_integration.response_dispatcher.enabled,
                    "prepared": self.enterprise_integration.response_dispatcher.prepared,
                },
                "process_status_manager": {
                    "enabled": self.enterprise_integration.process_status_manager.enabled,
                    "prepared": self.enterprise_integration.process_status_manager.prepared,
                },
                "error_management_framework": {
                    "enabled": self.enterprise_integration.error_management_framework.enabled,
                    "prepared": self.enterprise_integration.error_management_framework.prepared,
                },
                "communication_contracts": {
                    "enabled": self.enterprise_integration.communication_contracts.enabled,
                    "prepared": self.enterprise_integration.communication_contracts.prepared,
                },
                "integration_event_manager": {
                    "enabled": self.enterprise_integration.integration_event_manager.enabled,
                    "prepared": self.enterprise_integration.integration_event_manager.prepared,
                },
                "integration_traceability_manager": {
                    "enabled": self.enterprise_integration.integration_traceability_manager.enabled,
                    "prepared": self.enterprise_integration.integration_traceability_manager.prepared,
                },
                "integration_configuration_manager": {
                    "enabled": self.enterprise_integration.integration_configuration_manager.enabled,
                    "prepared": self.enterprise_integration.integration_configuration_manager.prepared,
                },
            },
            "classification": {
                "enabled": self.classification.enabled,
                "max_concepts_per_process": self.classification.max_concepts_per_process,
                "max_materials_per_process": self.classification.max_materials_per_process,
                "max_services_per_process": self.classification.max_services_per_process,
                "max_providers_per_process": self.classification.max_providers_per_process,
                "max_groups_per_process": self.classification.max_groups_per_process,
                "comprehension_integration_prepared": self.classification.comprehension_integration_prepared,
                "comprehension_enabled": self.classification.comprehension_enabled,
                "concept_analysis": {
                    "enabled": self.classification.concept_analysis.enabled,
                    "preserve_model_immutability": self.classification.concept_analysis.preserve_model_immutability,
                    "max_concepts_per_process": self.classification.concept_analysis.max_concepts_per_process,
                    "item_detector_enabled": self.classification.concept_analysis.item_detector_enabled,
                    "technical_detector_enabled": self.classification.concept_analysis.technical_detector_enabled,
                    "commercial_detector_enabled": self.classification.concept_analysis.commercial_detector_enabled,
                    "condition_detector_enabled": self.classification.concept_analysis.condition_detector_enabled,
                    "observation_detector_enabled": self.classification.concept_analysis.observation_detector_enabled,
                    "material_classification_prepared": self.classification.concept_analysis.material_classification_prepared,
                    "service_classification_prepared": self.classification.concept_analysis.service_classification_prepared,
                    "normalization_prepared": self.classification.concept_analysis.normalization_prepared,
                },
                "material_classification": {
                    "enabled": self.classification.material_classification.enabled,
                    "preserve_catalog_immutability": self.classification.material_classification.preserve_catalog_immutability,
                    "max_materials_per_process": self.classification.material_classification.max_materials_per_process,
                    "item_classifier_enabled": self.classification.material_classification.item_classifier_enabled,
                    "partida_classifier_enabled": self.classification.material_classification.partida_classifier_enabled,
                    "service_classification_prepared": self.classification.material_classification.service_classification_prepared,
                    "normalization_prepared": self.classification.material_classification.normalization_prepared,
                    "equivalence_detection_prepared": self.classification.material_classification.equivalence_detection_prepared,
                    "comparable_group_builder_prepared": self.classification.material_classification.comparable_group_builder_prepared,
                },
                "service_classification": {
                    "enabled": self.classification.service_classification.enabled,
                    "preserve_catalog_immutability": self.classification.service_classification.preserve_catalog_immutability,
                    "max_services_per_process": self.classification.service_classification.max_services_per_process,
                    "commercial_condition_classifier_enabled": self.classification.service_classification.commercial_condition_classifier_enabled,
                    "observation_classifier_enabled": self.classification.service_classification.observation_classifier_enabled,
                    "technical_element_classifier_enabled": self.classification.service_classification.technical_element_classifier_enabled,
                    "normalization_prepared": self.classification.service_classification.normalization_prepared,
                    "equivalence_detection_prepared": self.classification.service_classification.equivalence_detection_prepared,
                    "comparable_group_builder_prepared": self.classification.service_classification.comparable_group_builder_prepared,
                },
                "concept_normalization": {
                    "enabled": self.classification.concept_normalization.enabled,
                    "preserve_catalog_immutability": self.classification.concept_normalization.preserve_catalog_immutability,
                    "max_normalized_concepts_per_process": self.classification.concept_normalization.max_normalized_concepts_per_process,
                    "material_normalizer_enabled": self.classification.concept_normalization.material_normalizer_enabled,
                    "partida_normalizer_enabled": self.classification.concept_normalization.partida_normalizer_enabled,
                    "service_normalizer_enabled": self.classification.concept_normalization.service_normalizer_enabled,
                    "technical_element_normalizer_enabled": self.classification.concept_normalization.technical_element_normalizer_enabled,
                    "commercial_element_normalizer_enabled": self.classification.concept_normalization.commercial_element_normalizer_enabled,
                    "specification_normalizer_enabled": self.classification.concept_normalization.specification_normalizer_enabled,
                    "equivalence_detection_prepared": self.classification.concept_normalization.equivalence_detection_prepared,
                    "comparable_group_builder_prepared": self.classification.concept_normalization.comparable_group_builder_prepared,
                },
                "equivalence_detection": {
                    "enabled": self.classification.equivalence_detection.enabled,
                    "preserve_catalog_immutability": self.classification.equivalence_detection.preserve_catalog_immutability,
                    "max_equivalences_per_process": self.classification.equivalence_detection.max_equivalences_per_process,
                    "exact_match_detector_enabled": self.classification.equivalence_detection.exact_match_detector_enabled,
                    "cross_type_distinct_detector_enabled": self.classification.equivalence_detection.cross_type_distinct_detector_enabled,
                    "shared_origin_relation_detector_enabled": self.classification.equivalence_detection.shared_origin_relation_detector_enabled,
                    "comparable_group_builder_prepared": self.classification.equivalence_detection.comparable_group_builder_prepared,
                    "context_association_prepared": self.classification.equivalence_detection.context_association_prepared,
                    "comparative_domain_model_prepared": self.classification.equivalence_detection.comparative_domain_model_prepared,
                },
                "comparable_group_builder": {
                    "enabled": self.classification.comparable_group_builder.enabled,
                    "preserve_catalog_immutability": self.classification.comparable_group_builder.preserve_catalog_immutability,
                    "max_groups_per_process": self.classification.comparable_group_builder.max_groups_per_process,
                    "equivalence_cluster_builder_enabled": self.classification.comparable_group_builder.equivalence_cluster_builder_enabled,
                    "group_id_prefix": self.classification.comparable_group_builder.group_id_prefix,
                    "group_id_padding": self.classification.comparable_group_builder.group_id_padding,
                    "group_id_immutable": self.classification.comparable_group_builder.group_id_immutable,
                    "min_members_per_group": self.classification.comparable_group_builder.min_members_per_group,
                    "context_association_prepared": self.classification.comparable_group_builder.context_association_prepared,
                    "comparative_domain_model_prepared": self.classification.comparable_group_builder.comparative_domain_model_prepared,
                },
                "context_association": {
                    "enabled": self.classification.context_association.enabled,
                    "preserve_catalog_immutability": self.classification.context_association.preserve_catalog_immutability,
                    "preserve_context_immutability": self.classification.context_association.preserve_context_immutability,
                    "max_associations_per_process": self.classification.context_association.max_associations_per_process,
                    "uniform_group_context_associator_enabled": self.classification.context_association.uniform_group_context_associator_enabled,
                    "comparative_domain_model_prepared": self.classification.context_association.comparative_domain_model_prepared,
                },
                "comparative_domain_model_builder": {
                    "enabled": self.classification.comparative_domain_model_builder.enabled,
                    "preserve_catalog_immutability": self.classification.comparative_domain_model_builder.preserve_catalog_immutability,
                    "max_models_per_process": self.classification.comparative_domain_model_builder.max_models_per_process,
                    "group_context_aggregation_builder_enabled": self.classification.comparative_domain_model_builder.group_context_aggregation_builder_enabled,
                    "model_id_prefix": self.classification.comparative_domain_model_builder.model_id_prefix,
                    "model_id_padding": self.classification.comparative_domain_model_builder.model_id_padding,
                    "model_id_immutable": self.classification.comparative_domain_model_builder.model_id_immutable,
                    "default_confidence_level": self.classification.comparative_domain_model_builder.default_confidence_level,
                    "pm6_output_contract": self.classification.comparative_domain_model_builder.pm6_output_contract,
                },
                "classification_quality_framework": {
                    "enabled": self.classification.classification_quality_framework.enabled,
                    "preserve_catalog_immutability": self.classification.classification_quality_framework.preserve_catalog_immutability,
                    "model_consistency_validator_enabled": self.classification.classification_quality_framework.model_consistency_validator_enabled,
                    "data_integrity_validator_enabled": self.classification.classification_quality_framework.data_integrity_validator_enabled,
                    "identifier_uniqueness_validator_enabled": self.classification.classification_quality_framework.identifier_uniqueness_validator_enabled,
                    "traceability_chain_validator_enabled": self.classification.classification_quality_framework.traceability_chain_validator_enabled,
                    "pipeline_flow_validator_enabled": self.classification.classification_quality_framework.pipeline_flow_validator_enabled,
                    "require_related_context": self.classification.classification_quality_framework.require_related_context,
                    "require_pipeline_snapshot": self.classification.classification_quality_framework.require_pipeline_snapshot,
                    "certification_prepared": self.classification.classification_quality_framework.certification_prepared,
                },
            },
            "future": {
                "ocr_enabled": self.future.ocr.enabled,
                "ai_enabled": self.future.ai.enabled,
                "api_enabled": self.future.api.enabled,
                "storage_enabled": self.future.storage.enabled,
                "monitoring_enabled": self.future.monitoring.enabled,
            },
        }
