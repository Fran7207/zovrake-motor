"""Document Knowledge Index — Implementación 2.8."""

from zovrake_motor.comprehension.knowledge_index.engine import DocumentKnowledgeIndex
from zovrake_motor.comprehension.knowledge_index.entry_builder import IndexEntryBuilder
from zovrake_motor.comprehension.knowledge_index.enums import IndexEntryStatus, IndexingIncidentSeverity
from zovrake_motor.comprehension.knowledge_index.exceptions import (
    DuplicateIndexEntryError,
    InternalModelInputError,
    KnowledgeIndexError,
    TraceabilityError,
)
from zovrake_motor.comprehension.knowledge_index.gateway import InternalModelGateway
from zovrake_motor.comprehension.knowledge_index.integration import KnowledgeIndexMotorIntegration
from zovrake_motor.comprehension.knowledge_index.models import (
    DocumentIndexEntry,
    DocumentIndexRequest,
    DocumentIndexResult,
    DocumentIndexTraceability,
)
from zovrake_motor.comprehension.knowledge_index.query_hook import QueryIntegrationPoint
from zovrake_motor.comprehension.knowledge_index.reuse_hook import ReuseIntegrationPoint
from zovrake_motor.comprehension.knowledge_index.store import KnowledgeIndexStore

__all__ = [
    "DocumentIndexEntry",
    "DocumentIndexRequest",
    "DocumentIndexResult",
    "DocumentIndexTraceability",
    "DocumentKnowledgeIndex",
    "DuplicateIndexEntryError",
    "IndexEntryBuilder",
    "IndexEntryStatus",
    "IndexingIncidentSeverity",
    "InternalModelGateway",
    "InternalModelInputError",
    "KnowledgeIndexError",
    "KnowledgeIndexMotorIntegration",
    "KnowledgeIndexStore",
    "QueryIntegrationPoint",
    "ReuseIntegrationPoint",
    "TraceabilityError",
]
