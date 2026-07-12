"""Motor central del Context Integration Engine (CIE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.context_integration.association_builder import ContextAssociationBuilder
from zovrake_motor.comprehension.context_integration.classification_hook import ClassificationContextPoint
from zovrake_motor.comprehension.context_integration.context_builder import RequirementContextBuilder
from zovrake_motor.comprehension.context_integration.dki_hook import DkiAssociationPoint
from zovrake_motor.comprehension.context_integration.gateway import ContextInputGateway
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest, ContextIntegrationResult
from zovrake_motor.comprehension.context_integration.reasoning_hook import ReasoningContextPoint
from zovrake_motor.comprehension.context_integration.store import ContextIntegrationStore
from zovrake_motor.config.categories.comprehension import DocumentContextIntegrationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextIntegrationEngine:
    """
    Context Integration Engine (CIE).

    Administra el contexto del requerimiento y su asociación con el
    Modelo Documental Interno sin modificar la información documental.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        store: ContextIntegrationStore | None = None,
        gateway: ContextInputGateway | None = None,
        context_builder: RequirementContextBuilder | None = None,
        association_builder: ContextAssociationBuilder | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._store = store or ContextIntegrationStore()
        self._gateway = gateway or ContextInputGateway()
        self._context_builder = context_builder or RequirementContextBuilder()
        self._association_builder = association_builder or ContextAssociationBuilder()
        self._dki_hook: DkiAssociationPoint | None = None
        self._classification_hook: ClassificationContextPoint | None = None
        self._reasoning_hook: ReasoningContextPoint | None = None
        self._initialized = False

    @property
    def store(self) -> ContextIntegrationStore:
        return self._store

    @property
    def dki_association(self) -> DkiAssociationPoint:
        if self._dki_hook is None:
            self._dki_hook = DkiAssociationPoint(settings=self._context_settings())
        return self._dki_hook

    @property
    def classification_integration(self) -> ClassificationContextPoint:
        if self._classification_hook is None:
            self._classification_hook = ClassificationContextPoint(settings=self._context_settings())
        return self._classification_hook

    @property
    def reasoning_integration(self) -> ReasoningContextPoint:
        if self._reasoning_hook is None:
            self._reasoning_hook = ReasoningContextPoint(settings=self._context_settings())
        return self._reasoning_hook

    def is_ready(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        settings = self._context_settings()
        self._dki_hook = DkiAssociationPoint(settings=settings)
        self._classification_hook = ClassificationContextPoint(settings=settings)
        self._reasoning_hook = ReasoningContextPoint(settings=settings)
        self._initialized = True

    def integrate(self, request: ContextIntegrationRequest) -> ContextIntegrationResult:
        validated = self._gateway.validate(request)
        model_result = self._gateway.model_result(validated)
        index_result = self._gateway.index_result(validated)
        model = model_result.model
        context = self._context_builder.build(
            validated.detalles_requerimiento,
            process_id=validated.process_id,
            document_id=model_result.document_id,
            requirement_code=validated.requirement_code,
            metadata=validated.metadata,
        )
        association = self._association_builder.build(
            context,
            model_result=model_result,
            index_result=index_result,
            requirement_code=validated.requirement_code,
            classification_prepared=self.classification_integration.is_prepared,
            reasoning_prepared=self.reasoning_integration.is_prepared,
        )
        self._store.register(association)
        dki_status = self.dki_association.register_association(association)
        classification_status = self.classification_integration.prepare_for_future_classification(
            association,
        )
        reasoning_status = self.reasoning_integration.prepare_for_future_reasoning(association)
        observations = (
            *association.technical_observations,
            f"dki_association_status={dki_status['status']}",
            f"classification_status={classification_status['status']}",
            f"reasoning_status={reasoning_status['status']}",
            "document_information_unmodified=True",
        )
        return ContextIntegrationResult(
            process_id=validated.process_id,
            document_id=model_result.document_id,
            context_id=context.context_id,
            association=association,
            incidents=(),
            document_unmodified=True,
            original_preserved=model_result.original_preserved,
            associations_count=self._store.count(),
            technical_observations=observations,
        )

    def _context_settings(self) -> DocumentContextIntegrationSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().context_integration
        return DocumentContextIntegrationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._context_settings()
        return {
            "initialized": self._initialized,
            "associations_count": self._store.count(),
            "associations": self._store.snapshot(),
            "index_context_map": self._store.index_associations_snapshot(),
            "dki_association": self.dki_association.snapshot(),
            "classification_integration": self.classification_integration.snapshot(),
            "reasoning_integration": self.reasoning_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_document_immutability": settings.preserve_document_immutability,
                "dki_association_prepared": settings.dki_association_prepared,
                "classification_integration_prepared": settings.classification_integration_prepared,
                "reasoning_integration_prepared": settings.reasoning_integration_prepared,
                "max_associations_in_memory": settings.max_associations_in_memory,
            },
        }
