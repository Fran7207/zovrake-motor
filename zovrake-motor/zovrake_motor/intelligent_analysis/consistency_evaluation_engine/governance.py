"""
Contrato de entrada del Consistency Evaluation Engine.

Consume exclusivamente el catálogo de evidencias del EAE.
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyCriterionType,
)

PM7_EVIDENCE_INPUT_CONTRACT_NAME = "EvidenceAnalysisCatalog"
PM7_EVIDENCE_INPUT_CONTRACT_VERSION = "1.0"
RISK_ANALYSIS_ENGINE_PREPARED = True

PM7_EVIDENCE_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_definitive_catalog_id",
    "profiles",
    "consistency_evaluation_engine_prepared",
    "definitive_catalog_preserved",
    "source_data_preserved",
)

PM7_EVIDENCE_PROFILE_REQUIRED_FIELDS: tuple[str, ...] = (
    "definitive_model_id",
    "comparative_table_id",
    "group_id",
    "group_type",
    "evidence_records",
    "missing_evidence_records",
    "categories_present",
    "categories_missing",
    "confidence_level_available",
    "source_data_preserved",
)

EXPECTED_CONSISTENCY_CRITERIA: tuple[str, ...] = tuple(
    criterion.value for criterion in ConsistencyCriterionType
)
