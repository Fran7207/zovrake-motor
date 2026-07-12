"""Contrato base de constructores de entidad del IDMB."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalTraceability


class InternalEntityBuilderPort(ABC):
    """
    Contrato común para constructores de entidad del Modelo Documental Interno.

    Cada constructor tiene una única responsabilidad y no interpreta el contenido.
    """

    @property
    @abstractmethod
    def builder_name(self) -> str:
        """Identificador único del constructor."""

    @property
    @abstractmethod
    def builder_label(self) -> str:
        """Etiqueta descriptiva del constructor."""

    @property
    @abstractmethod
    def entity_type(self) -> InternalEntityType:
        """Tipo de entidad que construye."""

    @abstractmethod
    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        """Construye la entidad — sin interpretación en esta etapa."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "builder_label": self.builder_label,
            "entity_type": self.entity_type.value,
        }
