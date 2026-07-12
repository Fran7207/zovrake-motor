"""Configuración del Módulo de Comprensión Documental."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentAdapterSettings:
    """
    Configuración del Document Adapter Framework — fuente centralizada.

    Sin activar lectura ni procesamiento de documentos en esta etapa.
    """

    enabled: bool = False
    auto_resolution_enabled: bool = False
    pdf_enabled: bool = False
    word_enabled: bool = False
    excel_enabled: bool = False
    image_enabled: bool = False

    @classmethod
    def default(cls) -> DocumentAdapterSettings:
        return cls()


@dataclass(frozen=True)
class DocumentValidationSettings:
    """
    Configuración del Document Validation Framework — fuente centralizada.

    Sin activar lectura ni evaluación de archivos en esta etapa.
    """

    enabled: bool = False
    strict_mode: bool = False
    max_file_size_bytes: int = 50_000_000
    min_file_size_bytes: int = 1
    supported_formats: tuple[str, ...] = ("pdf", "docx", "xlsx", "image")

    @classmethod
    def default(cls) -> DocumentValidationSettings:
        return cls()


@dataclass(frozen=True)
class DocumentRecognitionSettings:
    """
    Configuración del Document Recognition Engine — fuente centralizada.

    Sin activar lectura de contenido ni OCR en esta etapa.
    """

    enabled: bool = False
    min_confidence_threshold: float = 0.5
    extension_strategy_enabled: bool = True
    mime_type_strategy_enabled: bool = True
    metadata_strategy_enabled: bool = True
    magic_number_strategy_enabled: bool = False
    supported_formats: tuple[str, ...] = ("pdf", "docx", "xlsx", "image")

    @classmethod
    def default(cls) -> DocumentRecognitionSettings:
        return cls()


@dataclass(frozen=True)
class DocumentExtractionSettings:
    """
    Configuración del Content Extraction Engine — fuente centralizada.

    Sin activar lectura de contenido ni OCR en esta etapa.
    """

    enabled: bool = False
    preserve_original: bool = True
    ocr_integration_prepared: bool = True
    ocr_enabled: bool = False
    text_extractor_enabled: bool = True
    tables_extractor_enabled: bool = True
    metadata_extractor_enabled: bool = True
    headers_extractor_enabled: bool = True
    footers_extractor_enabled: bool = True
    lists_extractor_enabled: bool = True
    embedded_images_extractor_enabled: bool = True
    structural_elements_extractor_enabled: bool = True

    @classmethod
    def default(cls) -> DocumentExtractionSettings:
        return cls()


@dataclass(frozen=True)
class DocumentCanonicalSettings:
    """
    Configuración del Canonical Representation Engine — fuente centralizada.

    Sin activar clasificación ni interpretación semántica en esta etapa.
    """

    enabled: bool = False
    preserve_immutability: bool = True
    classification_integration_prepared: bool = True
    classification_enabled: bool = False
    provider_transformer_enabled: bool = True
    commercial_transformer_enabled: bool = True
    technical_transformer_enabled: bool = True
    items_transformer_enabled: bool = True
    conditions_transformer_enabled: bool = True
    observations_transformer_enabled: bool = True
    metadata_transformer_enabled: bool = True

    @classmethod
    def default(cls) -> DocumentCanonicalSettings:
        return cls()


@dataclass(frozen=True)
class DocumentInternalModelSettings:
    """
    Configuración del Internal Document Model Builder — fuente centralizada.

    Sin activar clasificación ni interpretación semántica en esta etapa.
    """

    enabled: bool = False
    preserve_immutability: bool = True
    classification_integration_prepared: bool = True
    classification_enabled: bool = False
    document_builder_enabled: bool = True
    provider_builder_enabled: bool = True
    commercial_builder_enabled: bool = True
    technical_builder_enabled: bool = True
    items_builder_enabled: bool = True
    conditions_builder_enabled: bool = True
    observations_builder_enabled: bool = True
    metadata_builder_enabled: bool = True
    requirement_context_builder_enabled: bool = True
    original_references_builder_enabled: bool = True

    @classmethod
    def default(cls) -> DocumentInternalModelSettings:
        return cls()


@dataclass(frozen=True)
class DocumentKnowledgeIndexSettings:
    """
    Configuración del Document Knowledge Index — fuente centralizada.

    Sin motor de búsqueda ni almacenamiento persistente en esta etapa.
    """

    enabled: bool = False
    prevent_duplicates: bool = True
    query_integration_prepared: bool = True
    reuse_integration_prepared: bool = True
    query_enabled: bool = False
    reuse_enabled: bool = False
    max_entries_in_memory: int = 10_000

    @classmethod
    def default(cls) -> DocumentKnowledgeIndexSettings:
        return cls()


@dataclass(frozen=True)
class DocumentContextIntegrationSettings:
    """
    Configuración del Context Integration Engine — fuente centralizada.

    Sin interpretación de contexto ni razonamiento en esta etapa.
    """

    enabled: bool = False
    preserve_document_immutability: bool = True
    dki_association_prepared: bool = True
    classification_integration_prepared: bool = True
    reasoning_integration_prepared: bool = True
    classification_enabled: bool = False
    reasoning_enabled: bool = False
    max_associations_in_memory: int = 10_000

    @classmethod
    def default(cls) -> DocumentContextIntegrationSettings:
        return cls()


@dataclass(frozen=True)
class ComprehensionSettings:
    """
    Configuración de Comprensión Documental — fuente centralizada.

    Sin activar OCR, extracción ni procesamiento en esta etapa.
    """

    enabled: bool = False
    max_documents_per_process: int = 100
    supported_formats: tuple[str, ...] = ("pdf", "docx", "xlsx", "image")
    adapters: DocumentAdapterSettings = field(default_factory=DocumentAdapterSettings.default)
    validation: DocumentValidationSettings = field(default_factory=DocumentValidationSettings.default)
    recognition: DocumentRecognitionSettings = field(default_factory=DocumentRecognitionSettings.default)
    extraction: DocumentExtractionSettings = field(default_factory=DocumentExtractionSettings.default)
    canonical: DocumentCanonicalSettings = field(default_factory=DocumentCanonicalSettings.default)
    internal_model: DocumentInternalModelSettings = field(default_factory=DocumentInternalModelSettings.default)
    knowledge_index: DocumentKnowledgeIndexSettings = field(default_factory=DocumentKnowledgeIndexSettings.default)
    context_integration: DocumentContextIntegrationSettings = field(
        default_factory=DocumentContextIntegrationSettings.default,
    )

    @classmethod
    def default(cls) -> ComprehensionSettings:
        return cls()
