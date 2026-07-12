"""Contrato del módulo de Gestión de Documentos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from zovrake_motor.documents.models import DocumentCollection, DocumentReference


class DocumentsPort(ABC):
    """Punto de entrada para administración de documentos."""

    @abstractmethod
    def register(self, document: DocumentReference) -> None:
        """Registrará documentos — sin lectura ni almacenamiento en esta etapa."""

    @abstractmethod
    def get_collection(self, process_id: UUID) -> DocumentCollection:
        """Obtendrá la colección de documentos de un proceso."""
