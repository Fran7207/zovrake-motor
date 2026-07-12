"""
Contrato oficial de salida del Prompt Maestro 6.

El Modelo Comparativo Definitivo es la única representación que podrá
consumir el Prompt Maestro 7.
"""

from __future__ import annotations

PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME = "DefinitiveComparativeModelCatalog"
PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION = "1.0"
PM7_INPUT_CONTRACT_PREPARED = True

PM6_DEFINITIVE_CATALOG_REQUIRED_FIELDS: tuple[str, ...] = (
    "catalog_id",
    "process_id",
    "model_id",
    "document_id",
    "models",
    "pm6_definitive_output_contract",
    "pm7_input_contract_prepared",
    "source_data_preserved",
)

PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS: tuple[str, ...] = (
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
