"""Enumeraciones del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from enum import Enum


class IntelligentAnalysisComponentType(str, Enum):
    """Componentes internos del módulo de Razonamiento Inteligente."""

    INTELLIGENT_ANALYSIS_COORDINATOR = "intelligent_analysis_coordinator"
    EVIDENCE_ANALYSIS_ENGINE = "evidence_analysis_engine"
    CONSISTENCY_EVALUATION_ENGINE = "consistency_evaluation_engine"
    RISK_ANALYSIS_ENGINE = "risk_analysis_engine"
    CONTEXT_EVALUATION_ENGINE = "context_evaluation_engine"
    EXPLANATION_GENERATION_ENGINE = "explanation_generation_engine"
    CONCLUSION_GENERATION_ENGINE = "conclusion_generation_engine"
    RECOMMENDATION_GENERATION_ENGINE = "recommendation_generation_engine"
    REASONING_RESULT_BUILDER = "reasoning_result_builder"
    CONFIDENCE_MANAGEMENT_ENGINE = "confidence_management_engine"
    TRACEABILITY_MANAGEMENT_ENGINE = "traceability_management_engine"


class IntelligentAnalysisPhase(str, Enum):
    """Fases preparadas del flujo de razonamiento inteligente."""

    PREPARACION = "preparacion"
    CONSUMO_MODELO_COMPARATIVO_DEFINITIVO = "consumo_modelo_comparativo_definitivo"
    ANALISIS_EVIDENCIAS = "analisis_evidencias"
    EVALUACION_CONSISTENCIA = "evaluacion_consistencia"
    ANALISIS_RIESGOS = "analisis_riesgos"
    EVALUACION_CONTEXTO = "evaluacion_contexto"
    GENERACION_EXPLICACIONES = "generacion_explicaciones"
    GENERACION_CONCLUSIONES = "generacion_conclusiones"
    GENERACION_RECOMENDACIONES = "generacion_recomendaciones"
    CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE = "construccion_resultado_analisis_inteligente"
    GESTION_CONFIANZA = "gestion_confianza"
    GESTION_TRAZABILIDAD = "gestion_trazabilidad"
    FINALIZACION = "finalizacion"
