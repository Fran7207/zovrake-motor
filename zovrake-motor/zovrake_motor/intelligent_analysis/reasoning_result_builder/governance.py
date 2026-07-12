"""
Contrato oficial de salida del Prompt Maestro 7.

El Resultado del Análisis Inteligente es el único contrato de salida del PM7.
"""

from __future__ import annotations

PM7_OUTPUT_CONTRACT_NAME = "IntelligentAnalysisGroupResult"
PM7_OUTPUT_CONTRACT_VERSION = "1.0"
PM7_OUTPUT_CATALOG_CONTRACT_NAME = "IntelligentAnalysisResultCatalog"
PM7_OUTPUT_CATALOG_CONTRACT_VERSION = "1.0"
PM7_REASONING_RESULT_INPUT_CONTRACT_NAME = "ReasoningResultBuildInputBundle"
PM7_REASONING_RESULT_INPUT_CONTRACT_VERSION = "1.0"
INTEGRATION_CERTIFICATION_FRAMEWORK_PREPARED = True

PM7_RECOMMENDATION_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "source_consistency_catalog_id",
    "source_risk_catalog_id",
    "source_context_catalog_id",
    "source_explanation_catalog_id",
    "source_definitive_catalog_id",
    "profiles",
    "reasoning_result_builder_prepared",
    "evidence_catalog_preserved",
    "consistency_catalog_preserved",
    "risk_catalog_preserved",
    "context_catalog_preserved",
    "explanation_catalog_preserved",
    "definitive_catalog_preserved",
    "source_data_preserved",
)
