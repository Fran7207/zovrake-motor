"""Enumeraciones del Módulo de Comprensión Documental."""

from __future__ import annotations

from enum import Enum


class ComprehensionComponentType(str, Enum):
    """Componentes internos del módulo de Comprensión Documental."""

    DOCUMENT_COORDINATOR = "document_coordinator"
    DOCUMENT_VALIDATOR = "document_validator"
    DOCUMENT_ADAPTERS = "document_adapters"
    FORMAT_IDENTIFIER = "format_identifier"
    EXTRACTORS = "extractors"
    NORMALIZER = "normalizer"
    INTERNAL_MODEL_BUILDER = "internal_model_builder"
    DOCUMENT_INDEX = "document_index"
    CONTEXT_MANAGER = "context_manager"
    QUALITY_MANAGER = "quality_manager"
    TRACEABILITY_MANAGER = "traceability_manager"


class ComprehensionPhase(str, Enum):
    """Fases preparadas del flujo de comprensión documental."""

    PREPARACION = "preparacion"
    VALIDACION = "validacion"
    ADAPTACION = "adaptacion"
    IDENTIFICACION = "identificacion"
    EXTRACCION = "extraccion"
    NORMALIZACION = "normalizacion"
    MODELADO = "modelado"
    INDEXACION = "indexacion"
    INTEGRACION_CONTEXTO = "integracion_contexto"
    FINALIZACION = "finalizacion"
