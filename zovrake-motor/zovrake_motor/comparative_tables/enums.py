"""Enumeraciones del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from enum import Enum


class ComparativeTablesComponentType(str, Enum):
    """Componentes internos del módulo de Generación de Cuadros Comparativos."""

    COMPARATIVE_TABLES_COORDINATOR = "comparative_tables_coordinator"
    COMPARATIVE_STRUCTURE_ENGINE = "comparative_structure_engine"
    DYNAMIC_COLUMN_BUILDER = "dynamic_column_builder"
    DYNAMIC_ROW_BUILDER = "dynamic_row_builder"
    PROVIDER_ORGANIZATION_ENGINE = "provider_organization_engine"
    GROUP_INTEGRITY_ENGINE = "group_integrity_engine"
    TRACEABILITY_METADATA_ENGINE = "traceability_metadata_engine"
    COMPARATIVE_MODEL_BUILDER = "comparative_model_builder"
    COMPARATIVE_VALIDATION_FRAMEWORK = "comparative_validation_framework"
    COMPARATIVE_QUALITY_FRAMEWORK = "comparative_quality_framework"


class ComparativeTablesPhase(str, Enum):
    """Fases preparadas del flujo de generación de cuadros comparativos."""

    PREPARACION = "preparacion"
    CONSUMO_MODELO_DOMINIO = "consumo_modelo_dominio"
    ESTRUCTURA_COMPARATIVA = "estructura_comparativa"
    CONSTRUCCION_COLUMNAS = "construccion_columnas"
    CONSTRUCCION_FILAS = "construccion_filas"
    ORGANIZACION_PROVEEDORES = "organizacion_proveedores"
    INTEGRIDAD_GRUPOS = "integridad_grupos"
    TRAZABILIDAD_METADATOS = "trazabilidad_metadatos"
    MODELO_COMPARATIVO = "modelo_comparativo"
    VALIDACION_COMPARATIVA = "validacion_comparativa"
    VALIDACION_CALIDAD = "validacion_calidad"
    FINALIZACION = "finalizacion"
