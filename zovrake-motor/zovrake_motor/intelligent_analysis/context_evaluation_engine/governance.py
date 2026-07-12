"""
Contrato de entrada del Context Evaluation Engine.

Consume exclusivamente salidas del EAE, CEE, RAE, Modelo Comparativo Definitivo
y contexto del requerimiento (PM4).
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextAssociationType,
    ContextElementType,
    ContextualGapType,
)

PM7_CONTEXT_INPUT_CONTRACT_NAME = "ContextEvaluationInputBundle"
PM7_CONTEXT_INPUT_CONTRACT_VERSION = "1.0"
EXPLANATION_GENERATION_ENGINE_PREPARED = True

PM7_RISK_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "source_consistency_catalog_id",
    "profiles",
    "context_evaluation_engine_prepared",
    "evidence_catalog_preserved",
    "consistency_catalog_preserved",
    "source_data_preserved",
)

PM7_REQUIREMENT_CONTEXT_REQUIRED_FIELDS: tuple[str, ...] = (
    "context_id",
    "codigo_req",
)

EXPECTED_CONTEXT_ELEMENT_TYPES: tuple[str, ...] = tuple(
    element.value for element in ContextElementType
)
EXPECTED_CONTEXT_ASSOCIATION_TYPES: tuple[str, ...] = tuple(
    association.value for association in ContextAssociationType
)
EXPECTED_CONTEXTUAL_GAP_TYPES: tuple[str, ...] = tuple(gap.value for gap in ContextualGapType)
