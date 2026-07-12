"""
Contrato de entrada del Recommendation Generation Engine.

Consume exclusivamente salidas del EAE, CEE, RAE, CxEE, EGE y Modelo Comparativo Definitivo.
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    ConfidenceLevel,
    RecommendationScenarioType,
)

PM7_RECOMMENDATION_INPUT_CONTRACT_NAME = "RecommendationGenerationInputBundle"
PM7_RECOMMENDATION_INPUT_CONTRACT_VERSION = "1.0"
REASONING_RESULT_BUILDER_PREPARED = True

PM7_EXPLANATION_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "source_consistency_catalog_id",
    "source_risk_catalog_id",
    "source_context_catalog_id",
    "source_definitive_catalog_id",
    "profiles",
    "recommendation_generation_engine_prepared",
    "evidence_catalog_preserved",
    "consistency_catalog_preserved",
    "risk_catalog_preserved",
    "context_catalog_preserved",
    "definitive_catalog_preserved",
    "source_data_preserved",
)

EXPECTED_RECOMMENDATION_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in RecommendationScenarioType
)
EXPECTED_CONFIDENCE_LEVELS: tuple[str, ...] = tuple(level.value for level in ConfidenceLevel)
