"""Índice Documental — integración con el Document Knowledge Index."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.knowledge_index.engine import DocumentKnowledgeIndex
from zovrake_motor.comprehension.knowledge_index.integration import KnowledgeIndexMotorIntegration
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest, DocumentIndexResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentIndex(ComprehensionComponentPort):
    """
    Gestor del Document Knowledge Index (DKI).

    Responsabilidad única: indexar Modelos Documentales Internos para
    localización, reutilización y trazabilidad.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: DocumentKnowledgeIndex | None = None,
    ) -> None:
        self._engine = engine or DocumentKnowledgeIndex(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "document_index"

    @property
    def component_label(self) -> str:
        return "Índice Documental"

    @property
    def engine(self) -> DocumentKnowledgeIndex:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def register(
        self,
        request: DocumentIndexRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> DocumentIndexResult:
        if integration is not None and record_traceability:
            bridge = KnowledgeIndexMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_indexing(
                request.process_id,
                document_id=request.model_result.document_id,
            )

        result = self._engine.register(request)

        if integration is not None and record_traceability:
            bridge = KnowledgeIndexMotorIntegration.from_comprehension_integration(integration)
            bridge.complete_indexing(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
