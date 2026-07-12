"""
Gobierno arquitectónico del Módulo de Clasificación Inteligente.

Implementación 3.12 — Cierre formal del Prompt Maestro 5.

Este módulo declara metadatos de congelamiento y contratos.
No modifica el comportamiento de los motores funcionales.
"""

from __future__ import annotations

from typing import Any

PROMPT_MAESTRO_5_STATUS = "CLOSED"
IMPLEMENTATION_CLOSURE = "3.12"
PROMPT_MAESTRO_REFERENCE = "5"
NEXT_PROMPT_MAESTRO = "6"

FROZEN_FUNCTIONAL_COMPONENTS: tuple[tuple[str, str, str], ...] = (
    ("concept_analysis_engine", "Concept Analysis Engine", "3.2"),
    ("material_classification_engine", "Material Classification Engine", "3.3"),
    ("service_classification_engine", "Service Classification Engine", "3.4"),
    ("concept_normalization_engine", "Concept Normalization Engine", "3.5"),
    ("equivalence_detection_engine", "Equivalence Detection Engine", "3.6"),
    ("comparable_group_builder", "Comparable Group Builder", "3.7"),
    ("context_association_engine", "Context Association Engine", "3.8"),
    ("comparative_domain_model_builder", "Comparative Domain Model Builder", "3.9"),
    ("classification_quality_framework", "Classification Quality Framework", "3.10"),
)

RESERVED_FUTURE_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("group_identifier_generator", "Identificación avanzada de grupos"),
    ("traceability_manager", "Gestión centralizada de trazabilidad"),
    ("confidence_evaluation_engine", "Evaluación de confianza"),
)

ARCHITECTURAL_BOUNDARIES: tuple[dict[str, str], ...] = (
    {
        "module": "comprehension",
        "label": "Comprensión Documental",
        "prompt_maestro": "4",
        "output": "IDMB, DKI, Contexto Integrado",
    },
    {
        "module": "classification",
        "label": "Clasificación Inteligente",
        "prompt_maestro": "5",
        "output": "ComparativeDomainModelCatalog",
    },
    {
        "module": "comparative_tables",
        "label": "Generación de Cuadros Comparativos",
        "prompt_maestro": "6",
        "input": "ComparativeDomainModelCatalog",
    },
)

OUTPUT_CONTRACT_NAME = "ComparativeDomainModelCatalog"
OUTPUT_CONTRACT_VERSION = "1.0"
OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "source_context_association_catalog_id",
    "models",
    "pm6_output_contract",
    "source_data_preserved",
)

OUTPUT_CONTRACT_REQUIRED_MODEL_FIELDS: tuple[str, ...] = (
    "comparative_model_id",
    "internal_model_id",
    "group_id",
    "group_type",
    "primary_item",
    "equivalent_concepts",
    "providers",
    "commercial_information",
    "technical_information",
    "related_context",
    "traceability",
)

OUTPUT_CONTRACT_FORBIDDEN_PM6_ACCESSES: tuple[str, ...] = (
    "internal_model",
    "canonical_representation",
    "extraction_result",
    "original_document",
    "concept_catalog",
    "material_catalog",
    "service_catalog",
    "normalized_catalog",
    "equivalence_catalog",
    "comparable_group_catalog",
    "context_association_catalog",
)

EVOLUTION_EXTENSION_POINTS: tuple[str, ...] = (
    "concept_analysis.registry",
    "material_classification.registry",
    "service_classification.registry",
    "concept_normalization.registry",
    "equivalence_detection.registry",
    "comparable_group_builder.registry",
    "context_association.registry",
    "comparative_domain_model.registry",
    "classification_quality.registry",
)


def frozen_component_names() -> tuple[str, ...]:
    return tuple(component_id for component_id, _, _ in FROZEN_FUNCTIONAL_COMPONENTS)


def closure_snapshot() -> dict[str, Any]:
    """Instantánea del estado de cierre arquitectónico del PM5."""
    return {
        "prompt_maestro": PROMPT_MAESTRO_REFERENCE,
        "status": PROMPT_MAESTRO_5_STATUS,
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
        "output_contract": {
            "name": OUTPUT_CONTRACT_NAME,
            "version": OUTPUT_CONTRACT_VERSION,
            "required_catalog_fields": list(OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS),
            "required_model_fields": list(OUTPUT_CONTRACT_REQUIRED_MODEL_FIELDS),
            "forbidden_pm6_direct_accesses": list(OUTPUT_CONTRACT_FORBIDDEN_PM6_ACCESSES),
        },
        "evolution_extension_points": list(EVOLUTION_EXTENSION_POINTS),
    }
