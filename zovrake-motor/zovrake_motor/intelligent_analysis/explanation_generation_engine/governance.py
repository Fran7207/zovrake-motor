"""
Contrato de entrada del Explanation Generation Engine.

Consume exclusivamente salidas del EAE, CEE, RAE, CxEE y Modelo Comparativo Definitivo.
"""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationSectionType,
)

PM7_EXPLANATION_INPUT_CONTRACT_NAME = "ExplanationGenerationInputBundle"
PM7_EXPLANATION_INPUT_CONTRACT_VERSION = "1.0"
CONCLUSION_GENERATION_ENGINE_PREPARED = True

PM7_CONTEXT_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "source_consistency_catalog_id",
    "source_risk_catalog_id",
    "source_definitive_catalog_id",
    "profiles",
    "explanation_generation_engine_prepared",
    "evidence_catalog_preserved",
    "consistency_catalog_preserved",
    "risk_catalog_preserved",
    "definitive_catalog_preserved",
    "requirement_context_preserved",
    "source_data_preserved",
)

EXPECTED_EXPLANATION_SECTION_TYPES: tuple[str, ...] = tuple(
    section.value for section in ExplanationSectionType
)
