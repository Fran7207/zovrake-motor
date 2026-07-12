"""Enumeraciones del Observability, Metrics & Monitoring Framework."""

from __future__ import annotations

from enum import Enum


class ComponentHealthStatus(str, Enum):
    """Estado operativo de un componente de integración."""

    AVAILABLE = "disponible"
    BUSY = "ocupado"
    DEGRADED = "degradado"
    RECOVERING = "recuperandose"
    STOPPED = "detenido"


class PerformanceMetricKind(str, Enum):
    """Indicadores de rendimiento recopilados por el OMMF."""

    VALIDATION_TIME = "tiempo_validacion"
    QUEUE_WAIT_TIME = "tiempo_espera_cola"
    PROCESSING_TIME = "tiempo_procesamiento"
    RECOVERY_TIME = "tiempo_recuperacion"
    TOTAL_ANALYSIS_TIME = "tiempo_total_analisis"
    COMPONENT_UTILIZATION = "utilizacion_componente"


class ObservabilityEventKind(str, Enum):
    """Tipos de eventos operativos registrados."""

    METRIC_RECORDED = "metrica_registrada"
    TRACE_RECORDED = "traza_registrada"
    HEALTH_UPDATED = "salud_actualizada"
    CONSOLIDATION = "consolidacion"
