"""Enumeraciones del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from enum import Enum


class ClassificationComponentType(str, Enum):
    """Componentes internos del módulo de Clasificación Inteligente."""

    CLASSIFICATION_COORDINATOR = "classification_coordinator"
    CONCEPT_ANALYSIS_ENGINE = "concept_analysis_engine"
    MATERIAL_CLASSIFICATION_ENGINE = "material_classification_engine"
    SERVICE_CLASSIFICATION_ENGINE = "service_classification_engine"
    CONCEPT_NORMALIZATION_ENGINE = "concept_normalization_engine"
    EQUIVALENCE_DETECTION_ENGINE = "equivalence_detection_engine"
    COMPARABLE_GROUP_BUILDER = "comparable_group_builder"
    GROUP_IDENTIFIER_GENERATOR = "group_identifier_generator"
    CONTEXT_ASSOCIATION_ENGINE = "context_association_engine"
    TRACEABILITY_MANAGER = "traceability_manager"
    CONFIDENCE_EVALUATION_ENGINE = "confidence_evaluation_engine"
    COMPARATIVE_DOMAIN_MODEL_BUILDER = "comparative_domain_model_builder"
    CLASSIFICATION_QUALITY_FRAMEWORK = "classification_quality_framework"


class ClassificationPhase(str, Enum):
    """Fases preparadas del flujo de clasificación inteligente."""

    PREPARACION = "preparacion"
    ANALISIS_CONCEPTOS = "analisis_conceptos"
    CLASIFICACION_MATERIALES = "clasificacion_materiales"
    CLASIFICACION_SERVICIOS = "clasificacion_servicios"
    NORMALIZACION_CONCEPTOS = "normalizacion_conceptos"
    DETECCION_EQUIVALENCIAS = "deteccion_equivalencias"
    CONSTRUCCION_GRUPOS = "construccion_grupos"
    IDENTIFICACION_GRUPOS = "identificacion_grupos"
    ASOCIACION_CONTEXTO = "asociacion_contexto"
    TRAZABILIDAD = "trazabilidad"
    EVALUACION_CONFIANZA = "evaluacion_confianza"
    MODELO_DOMINIO = "modelo_dominio"
    VALIDACION_CALIDAD = "validacion_calidad"
    FINALIZACION = "finalizacion"
