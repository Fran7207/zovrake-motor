"""
Gobierno arquitectónico del Módulo de Razonamiento y Resultado del Análisis Inteligente.

Implementación 7.10 — Cierre formal del Prompt Maestro 7.

Este módulo declara metadatos de congelamiento y contratos.
No modifica el comportamiento de los motores funcionales.
"""

from __future__ import annotations

from typing import Any

PROMPT_MAESTRO_7_STATUS = "CLOSED"
IMPLEMENTATION = "7.10"
IMPLEMENTATION_CLOSURE = "7.10"
PROMPT_MAESTRO_REFERENCE = "7"
NEXT_PROMPT_MAESTRO = "8"
NEXT_IMPLEMENTATION = None

OUTPUT_CONTRACT_NAME = "IntelligentAnalysisResultCatalog"
OUTPUT_CONTRACT_VERSION = "1.0"
OUTPUT_GROUP_CONTRACT_NAME = "IntelligentAnalysisGroupResult"
OUTPUT_GROUP_CONTRACT_VERSION = "1.0"

FROZEN_FUNCTIONAL_COMPONENTS: tuple[tuple[str, str, str], ...] = (
    ("evidence_analysis_engine", "Evidence Analysis Engine", "7.2"),
    ("consistency_evaluation_engine", "Consistency Evaluation Engine", "7.3"),
    ("risk_analysis_engine", "Risk Analysis Engine", "7.4"),
    ("context_evaluation_engine", "Context Evaluation Engine", "7.5"),
    ("explanation_generation_engine", "Explanation Generation Engine", "7.6"),
    ("recommendation_generation_engine", "Recommendation Generation Engine", "7.7"),
    ("reasoning_result_builder", "Reasoning Result Builder", "7.8"),
)

OPERATIVE_FUNCTIONAL_COMPONENTS = FROZEN_FUNCTIONAL_COMPONENTS

RESERVED_FUTURE_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("conclusion_generation_engine", "Generación de conclusiones estructuradas"),
    ("confidence_management_engine", "Gestión centralizada de confianza"),
    ("traceability_management_engine", "Gestión centralizada de trazabilidad"),
)

PREPARED_FUNCTIONAL_COMPONENTS: tuple[tuple[str, str, str], ...] = (
    *FROZEN_FUNCTIONAL_COMPONENTS,
    ("conclusion_generation_engine", "Conclusion Generation Engine", "7.1"),
    ("confidence_management_engine", "Confidence Management Engine", "7.1"),
    ("traceability_management_engine", "Traceability Management Engine", "7.10"),
)

INPUT_CONTRACT_NAME = "DefinitiveComparativeModelCatalog"
INPUT_CONTRACT_VERSION = "1.0"

ARCHITECTURAL_BOUNDARIES: tuple[dict[str, str], ...] = (
    {
        "module": "comparative_tables",
        "label": "Generación de Cuadros Comparativos",
        "prompt_maestro": "6",
        "output": "DefinitiveComparativeModelCatalog",
    },
    {
        "module": "intelligent_analysis",
        "label": "Resultado del Análisis Inteligente",
        "prompt_maestro": "7",
        "input": "DefinitiveComparativeModelCatalog",
        "output": "IntelligentAnalysisResultCatalog",
    },
    {
        "module": "processing",
        "label": "Orquestación del Motor",
        "prompt_maestro": "3",
        "input": "IntelligentAnalysisResultCatalog",
    },
)

OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_evidence_catalog_id",
    "source_consistency_catalog_id",
    "source_risk_catalog_id",
    "source_context_catalog_id",
    "source_explanation_catalog_id",
    "source_recommendation_catalog_id",
    "source_definitive_catalog_id",
    "results",
    "source_data_preserved",
)

OUTPUT_CONTRACT_REQUIRED_RESULT_FIELDS: tuple[str, ...] = (
    "result_id",
    "group_id",
    "definitive_model_id",
    "comparative_table_id",
    "executive_summary",
    "structured_explanation",
    "recommendation",
    "confidence_level",
    "document_traceability",
    "source_data_preserved",
)

OUTPUT_CONTRACT_FORBIDDEN_DOWNSTREAM_ACCESSES: tuple[str, ...] = (
    "definitive_comparative_model_catalog",
    "evidence_catalog",
    "consistency_catalog",
    "risk_catalog",
    "context_catalog",
    "explanation_catalog",
    "recommendation_catalog",
    "evidence_analysis_engine",
    "recommendation_generation_engine",
)

EVOLUTION_EXTENSION_POINTS: tuple[str, ...] = (
    "evidence_analysis_engine.registry",
    "consistency_evaluation_engine.registry",
    "risk_analysis_engine.registry",
    "context_evaluation_engine.registry",
    "explanation_generation_engine.registry",
    "recommendation_generation_engine.registry",
    "reasoning_result_builder.registry",
    "component_registry.register",
    "intelligent_analysis_pipeline.extend",
)

XAI_REQUIRED_RESULT_ATTRIBUTES: tuple[str, ...] = (
    "structured_explanation",
    "recommendation",
    "confidence_level",
    "document_traceability",
)


def frozen_component_names() -> tuple[str, ...]:
    return tuple(component_id for component_id, _, _ in FROZEN_FUNCTIONAL_COMPONENTS)


def closure_snapshot() -> dict[str, Any]:
    """Instantánea del estado de cierre arquitectónico del PM7."""
    return {
        "prompt_maestro": PROMPT_MAESTRO_REFERENCE,
        "status": PROMPT_MAESTRO_7_STATUS,
        "implementation_closure": IMPLEMENTATION_CLOSURE,
        "next_prompt_maestro": NEXT_PROMPT_MAESTRO,
        "frozen_components": [
            {
                "component_id": component_id,
                "label": label,
                "implementation": implementation,
                "frozen": True,
            }
            for component_id, label, implementation in FROZEN_FUNCTIONAL_COMPONENTS
        ],
        "reserved_components": [
            {"component_id": component_id, "label": label, "frozen": False}
            for component_id, label in RESERVED_FUTURE_COMPONENTS
        ],
        "architectural_boundaries": list(ARCHITECTURAL_BOUNDARIES),
        "input_contract": {
            "name": INPUT_CONTRACT_NAME,
            "version": INPUT_CONTRACT_VERSION,
        },
        "output_contract": {
            "name": OUTPUT_CONTRACT_NAME,
            "version": OUTPUT_CONTRACT_VERSION,
            "group_contract_name": OUTPUT_GROUP_CONTRACT_NAME,
            "group_contract_version": OUTPUT_GROUP_CONTRACT_VERSION,
            "required_catalog_fields": list(OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS),
            "required_result_fields": list(OUTPUT_CONTRACT_REQUIRED_RESULT_FIELDS),
            "forbidden_downstream_direct_accesses": list(OUTPUT_CONTRACT_FORBIDDEN_DOWNSTREAM_ACCESSES),
        },
        "xai_principles": {
            "explainable_recommendations": True,
            "traceable_explanations": True,
            "evidence_backed_conclusions": True,
            "documented_justification_required": True,
        },
        "evolution_extension_points": list(EVOLUTION_EXTENSION_POINTS),
    }


def governance_snapshot() -> dict[str, Any]:
    """Instantánea de gobierno operativo — compatible con integraciones previas."""
    return {
        **closure_snapshot(),
        "implementation": IMPLEMENTATION,
        "next_implementation": NEXT_IMPLEMENTATION,
        "prepared_functional_components": [
            {"id": item[0], "label": item[1], "implementation": item[2]}
            for item in PREPARED_FUNCTIONAL_COMPONENTS
        ],
        "prepared_functional_components_count": len(PREPARED_FUNCTIONAL_COMPONENTS),
        "operative_functional_components": [
            {"id": item[0], "label": item[1], "implementation": item[2]}
            for item in OPERATIVE_FUNCTIONAL_COMPONENTS
        ],
        "operative_functional_components_count": len(OPERATIVE_FUNCTIONAL_COMPONENTS),
    }
