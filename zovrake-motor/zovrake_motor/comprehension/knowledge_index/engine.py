"""Motor central del Document Knowledge Index (DKI)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.knowledge_index.entry_builder import IndexEntryBuilder
from zovrake_motor.comprehension.knowledge_index.gateway import InternalModelGateway
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest, DocumentIndexResult
from zovrake_motor.comprehension.knowledge_index.query_hook import QueryIntegrationPoint
from zovrake_motor.comprehension.knowledge_index.reuse_hook import ReuseIntegrationPoint
from zovrake_motor.comprehension.knowledge_index.store import KnowledgeIndexStore
from zovrake_motor.config.categories.comprehension import DocumentKnowledgeIndexSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentKnowledgeIndex:
    """
    Document Knowledge Index (DKI).

    Administra el índice documental interno para localización, reutilización
    y trazabilidad de Modelos Documentales Internos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        store: KnowledgeIndexStore | None = None,
        gateway: InternalModelGateway | None = None,
        entry_builder: IndexEntryBuilder | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._store = store or KnowledgeIndexStore()
        self._gateway = gateway or InternalModelGateway()
        self._entry_builder = entry_builder or IndexEntryBuilder()
        self._query_hook: QueryIntegrationPoint | None = None
        self._reuse_hook: ReuseIntegrationPoint | None = None
        self._initialized = False

    @property
    def store(self) -> KnowledgeIndexStore:
        return self._store

    @property
    def query_integration(self) -> QueryIntegrationPoint:
        if self._query_hook is None:
            self._query_hook = QueryIntegrationPoint(settings=self._index_settings())
        return self._query_hook

    @property
    def reuse_integration(self) -> ReuseIntegrationPoint:
        if self._reuse_hook is None:
            self._reuse_hook = ReuseIntegrationPoint(settings=self._index_settings())
        return self._reuse_hook

    def is_ready(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._query_hook = QueryIntegrationPoint(settings=self._index_settings())
        self._reuse_hook = ReuseIntegrationPoint(settings=self._index_settings())
        self._initialized = True

    def register(self, request: DocumentIndexRequest) -> DocumentIndexResult:
        model_result = self._gateway.validate(request)
        model = self._gateway.model(model_result)
        index_id = f"dki://{model.model_id}"
        entry = self._entry_builder.build(
            model_result,
            index_id=index_id,
            validation_reference=request.validation_reference,
            project_id=request.project_id,
            metadata=request.metadata,
            reuse_prepared=self.reuse_integration.is_prepared,
            query_integration_prepared=self.query_integration.is_prepared,
        )
        self._store.register(entry)
        query_status = self.query_integration.prepare_for_future_queries(query_keys=entry.query_keys)
        reuse_status = self.reuse_integration.prepare_for_future_reuse(entry)
        observations = (
            *entry.technical_observations,
            f"query_status={query_status['status']}",
            f"reuse_status={reuse_status['status']}",
            "internal_model_unmodified=True",
        )
        return DocumentIndexResult(
            process_id=model_result.process_id,
            document_id=model_result.document_id,
            index_id=index_id,
            entry=entry,
            incidents=(),
            original_preserved=model_result.original_preserved,
            duplicate_prevented=True,
            entries_count=self._store.count(),
            technical_observations=observations,
        )

    def _index_settings(self) -> DocumentKnowledgeIndexSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().knowledge_index
        return DocumentKnowledgeIndexSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._index_settings()
        return {
            "initialized": self._initialized,
            "entries_count": self._store.count(),
            "entries": self._store.snapshot(),
            "query_integration": self.query_integration.snapshot(),
            "reuse_integration": self.reuse_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "prevent_duplicates": settings.prevent_duplicates,
                "query_integration_prepared": settings.query_integration_prepared,
                "reuse_integration_prepared": settings.reuse_integration_prepared,
                "max_entries_in_memory": settings.max_entries_in_memory,
            },
        }
