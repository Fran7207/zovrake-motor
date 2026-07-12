"""
Contrato de entrada del Evidence Analysis Engine.

Consume exclusivamente el Modelo Comparativo Definitivo (PM6).
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import EvidenceCategory

PM7_DEFINITIVE_INPUT_CONTRACT_NAME = "DefinitiveComparativeModelCatalog"
PM7_DEFINITIVE_INPUT_CONTRACT_VERSION = "1.0"
CONSISTENCY_EVALUATION_ENGINE_PREPARED = True

PM7_DEFINITIVE_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "models",
    "pm6_definitive_output_contract",
    "pm7_input_contract_prepared",
    "source_data_preserved",
)

PM7_DEFINITIVE_MODEL_REQUIRED_FIELDS: tuple[str, ...] = (
    "definitive_model_id",
    "comparative_table_id",
    "group_id",
    "group_type",
    "dynamic_columns",
    "dynamic_rows",
    "provider_organization",
    "commercial_information",
    "technical_information",
    "inherited_context",
    "confidence_level_available",
    "metadata",
    "traceability",
    "motor_internal_references",
)

EXPECTED_EVIDENCE_CATEGORIES: tuple[str, ...] = tuple(
    category.value for category in EvidenceCategory
)
