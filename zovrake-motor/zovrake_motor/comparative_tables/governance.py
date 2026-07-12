"""
Gobierno arquitectónico del Módulo de Generación de Cuadros Comparativos.

Implementación 4.11 — Certificación integral del Prompt Maestro 6.
"""

from __future__ import annotations

from typing import Any

PROMPT_MAESTRO_6_STATUS = "CERTIFIED"
IMPLEMENTATION_CERTIFICATION = "4.11"
PROMPT_MAESTRO_REFERENCE = "6"
NEXT_PROMPT_MAESTRO = "7"
NEXT_IMPLEMENTATION = "4.12"

FROZEN_FUNCTIONAL_COMPONENTS: tuple[tuple[str, str, str], ...] = (
    ("comparative_structure_engine", "Comparative Structure Engine", "4.2"),
    ("dynamic_column_builder", "Dynamic Column Builder", "4.3"),
    ("dynamic_row_builder", "Dynamic Row Builder", "4.4"),
    ("provider_organization_engine", "Provider Organization Engine", "4.5"),
    ("group_integrity_engine", "Group Integrity Engine", "4.6"),
    ("traceability_metadata_engine", "Traceability & Metadata Engine", "4.7"),
    ("comparative_model_builder", "Comparative Model Builder", "4.8"),
    ("comparative_validation_framework", "Comparative Validation Framework", "4.9"),
    ("comparative_quality_framework", "Comparative Quality Framework", "4.10"),
)

ARCHITECTURAL_BOUNDARIES: tuple[dict[str, str], ...] = (
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
        "output": "DefinitiveComparativeModelCatalog",
    },
    {
        "module": "intelligent_analysis",
        "label": "Resultado del Análisis Inteligente",
        "prompt_maestro": "7",
        "input": "DefinitiveComparativeModelCatalog",
    },
)

OUTPUT_CONTRACT_NAME = "DefinitiveComparativeModelCatalog"
OUTPUT_CONTRACT_VERSION = "1.0"

CERTIFICATION_DOCUMENTS: tuple[str, ...] = (
    "ARCHITECTURE.md",
    "CERTIFICATION.md",
    "OUTPUT_CONTRACT.md",
)


def certification_snapshot() -> dict[str, Any]:
    return {
        "prompt_maestro": PROMPT_MAESTRO_REFERENCE,
        "status": PROMPT_MAESTRO_6_STATUS,
        "implementation": IMPLEMENTATION_CERTIFICATION,
        "next_prompt_maestro": NEXT_PROMPT_MAESTRO,
        "next_implementation": NEXT_IMPLEMENTATION,
        "frozen_functional_components": [
            {"id": item[0], "label": item[1], "implementation": item[2]}
            for item in FROZEN_FUNCTIONAL_COMPONENTS
        ],
        "frozen_functional_components_count": len(FROZEN_FUNCTIONAL_COMPONENTS),
        "output_contract": {
            "name": OUTPUT_CONTRACT_NAME,
            "version": OUTPUT_CONTRACT_VERSION,
        },
        "architectural_boundaries": list(ARCHITECTURAL_BOUNDARIES),
        "certification_documents": list(CERTIFICATION_DOCUMENTS),
    }
