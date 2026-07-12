"""
Contrato de entrada del Risk Analysis Engine.

Consume exclusivamente las salidas del EAE y del CEE.
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import RiskCategory

PM7_RISK_INPUT_CONTRACT_NAME = "EvidenceAndConsistencyAnalysisBundle"
PM7_RISK_INPUT_CONTRACT_VERSION = "1.0"
CONTEXT_EVALUATION_ENGINE_PREPARED = True

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

PM7_CONSISTENCY_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "profiles",
    "risk_analysis_engine_prepared",
    "evidence_catalog_preserved",
    "source_data_preserved",
)

EXPECTED_RISK_CATEGORIES: tuple[str, ...] = tuple(category.value for category in RiskCategory)
