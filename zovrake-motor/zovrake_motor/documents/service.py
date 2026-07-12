"""Servicio del módulo de Gestión de Documentos."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.documents.models import DocumentCollection, DocumentReference
from zovrake_motor.documents.port import DocumentsPort
from zovrake_motor.models.ports import ModulePort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentService(ConfigurationAccessible, ModulePort, DocumentsPort):
    """
    Módulo de Gestión de Documentos.

    Responsabilidad única: administrar referencias a documentos recibidos.
    Sin lectura, OCR ni almacenamiento en esta etapa.
    """

    MODULE_NAME = "documents"

    def __init__(self, *, config_provider: ConfigurationProvider | None = None) -> None:
        super().__init__(config_provider=config_provider)
        self._initialized = False
        self._collections: dict[UUID, DocumentCollection] = {}

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True

    def register(self, document: DocumentReference) -> None:
        pass

    def organize(self, *, process_id: UUID, codigo_req: str, documents: list[DocumentReference]) -> DocumentCollection:
        collection = DocumentCollection(
            process_id=process_id,
            codigo_req=codigo_req,
            documents=list(documents),
        )
        self._collections[process_id] = collection
        return collection

    def get_collection(self, process_id: UUID) -> DocumentCollection:
        return self._collections.get(
            process_id,
            DocumentCollection(process_id=process_id, codigo_req=""),
        )
