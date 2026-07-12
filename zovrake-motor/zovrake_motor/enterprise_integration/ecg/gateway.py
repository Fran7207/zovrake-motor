"""
ERP Communication Gateway — único canal ERP ↔ Motor Inteligente.

Punto de integración oficial con el Centro de Evidencias (Cotizaciones).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.ecg.contracts.v1 import contract_snapshot
from zovrake_motor.enterprise_integration.ecg.dispatch_port import EcgIntegrationDispatchPort
from zovrake_motor.enterprise_integration.ecg.enums import EcgChannelDirection, EcgMessageType
from zovrake_motor.enterprise_integration.ecg.events import EcgEventRecorder
from zovrake_motor.enterprise_integration.apqm.enqueue_port import EcgEnqueuePort
from zovrake_motor.enterprise_integration.apqm.models import QueueItemContext
from zovrake_motor.enterprise_integration.svaf.ports import EcgSecurityPort
from zovrake_motor.enterprise_integration.ecg.messages.models import EcgMessageEnvelope
from zovrake_motor.enterprise_integration.ecg.messages.store import EcgMessageStore
from zovrake_motor.enterprise_integration.ecg.transformation.delivery_builder import (
    ErpDeliveryBuilder,
)
from zovrake_motor.enterprise_integration.ecg.transformation.request_transformer import (
    ErpRequestTransformer,
)
from zovrake_motor.states.enums import MotorState

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ErpCommunicationGateway:
    """
    Gateway exclusivo de comunicación ERP ↔ Motor.

    Toda solicitud pasa por PIO y API Interna. Sin acceso directo al Motor.
    """

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        message_store: EcgMessageStore | None = None,
        request_transformer: ErpRequestTransformer | None = None,
        delivery_builder: ErpDeliveryBuilder | None = None,
        event_recorder: EcgEventRecorder | None = None,
    ) -> None:
        self._integration = integration
        self._messages = message_store or EcgMessageStore()
        self._transformer = request_transformer or ErpRequestTransformer()
        self._delivery_builder = delivery_builder or ErpDeliveryBuilder()
        self._event_recorder = event_recorder or EcgEventRecorder(integration)
        self._dispatch: EcgIntegrationDispatchPort | None = None
        self._enqueue: EcgEnqueuePort | None = None
        self._security: EcgSecurityPort | None = None
        self._initialized = False

    @property
    def message_store(self) -> EcgMessageStore:
        return self._messages

    def bind_dispatch(self, dispatch: EcgIntegrationDispatchPort) -> None:
        self._dispatch = dispatch

    def bind_enqueue(self, enqueue: EcgEnqueuePort) -> None:
        self._enqueue = enqueue

    def bind_security(self, security: EcgSecurityPort) -> None:
        self._security = security

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        settings = self._integration.enterprise_integration_settings().erp_communication_gateway
        return self._initialized and self._dispatch is not None and settings.prepared

    def _settings(self):
        return self._integration.enterprise_integration_settings().erp_communication_gateway

    def _use_async_queue(self) -> bool:
        apqm_settings = (
            self._integration.enterprise_integration_settings().async_processing_queue_manager
        )
        return (
            self._settings().queue_processing_prepared
            and apqm_settings.enabled
            and apqm_settings.prepared
            and self._enqueue is not None
        )

    def _build_queue_context(self, request: EvidenceCenterAnalysisRequest) -> QueueItemContext:
        return QueueItemContext(
            process_id=request.process_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
            codigo_req=request.requirement.codigo_req,
            document_ids=tuple(doc.document_id for doc in request.evidence_documents),
            requirement_metadata={
                "description": request.requirement.description,
                **request.requirement.metadata,
            },
            analysis_metadata=dict(request.analysis_metadata),
            source="ecg",
        )

    def _require_dispatch(self) -> EcgIntegrationDispatchPort:
        if self._dispatch is None:
            raise RuntimeError("ECG dispatch no vinculado — requiere Coordinator y PIO")
        return self._dispatch

    def _record_inbound(self, request: EvidenceCenterAnalysisRequest) -> None:
        envelope = EcgMessageEnvelope.create(
            process_id=request.process_id,
            message_type=EcgMessageType.REQUEST,
            direction=EcgChannelDirection.ERP_TO_MOTOR,
            payload=request.to_dict(),
        )
        self._messages.append(envelope)
        self._event_recorder.record_message(
            request.process_id,
            message_type=EcgMessageType.REQUEST,
            direction=EcgChannelDirection.ERP_TO_MOTOR,
            summary="Solicitud recibida desde Centro de Evidencias",
        )

    def _record_outbound(self, delivery: ErpAnalysisDelivery) -> None:
        envelope = EcgMessageEnvelope.create(
            process_id=delivery.process_id,
            message_type=EcgMessageType.RESPONSE if delivery.success else EcgMessageType.ERROR,
            direction=EcgChannelDirection.MOTOR_TO_ERP,
            payload=delivery.to_dict(),
        )
        self._messages.append(envelope)
        self._event_recorder.record_message(
            delivery.process_id,
            message_type=envelope.message_type,
            direction=EcgChannelDirection.MOTOR_TO_ERP,
            summary="Entrega al Centro de Evidencias",
        )

    def _ensure_process_state(self, request: EvidenceCenterAnalysisRequest) -> None:
        state_manager = self._integration.state_manager
        if state_manager.get_process(request.process_id) is None:
            state_manager.create_process(
                request.process_id,
                request.requirement.codigo_req,
                metadata={
                    "project_id": request.project_id,
                    "quotation_id": request.quotation_id,
                    "source": "evidence_center",
                },
                initial_state=MotorState.INICIALIZADO,
            )
            self._event_recorder.record_state_sync(
                request.process_id,
                motor_state=MotorState.INICIALIZADO.value,
            )

    def _use_security(self) -> bool:
        settings = self._integration.enterprise_integration_settings().security_validation_audit_framework
        return settings.enabled and settings.prepared and self._security is not None

    def _validate_and_deliver_outbound(
        self,
        delivery: ErpAnalysisDelivery,
        *,
        operation: str,
    ) -> ErpAnalysisDelivery:
        if self._use_security() and self._security is not None:
            outcome = self._security.validate_outbound_delivery(delivery, operation=operation)
            if not outcome.approved:
                return ErpAnalysisDelivery(
                    process_id=delivery.process_id,
                    project_id=delivery.project_id,
                    quotation_id=delivery.quotation_id,
                    success=False,
                    message="Entrega rechazada por validación de integridad",
                    analysis_status="error_validacion",
                    metadata={"outbound_validation_failed": True},
                )
        return delivery

    def submit_analysis_request(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> ErpAnalysisDelivery:
        if not self.is_ready():
            raise RuntimeError("ERP Communication Gateway no está listo")

        self._record_inbound(request)
        self._ensure_process_state(request)

        if self._use_security() and self._security is not None:
            security_outcome = self._security.validate_inbound_analysis_request(request)
            if not security_outcome.approved:
                delivery = self._delivery_builder.from_validation_rejection(
                    request,
                    outcome=security_outcome,
                )
                self._record_outbound(delivery)
                return delivery

        internal_request = self._transformer.to_start_analysis(request)

        if self._use_async_queue():
            enqueue = self._enqueue
            if enqueue is None:
                raise RuntimeError("ECG enqueue no vinculado — requiere APQM")
            enqueue_result = enqueue.enqueue_start_analysis(
                internal_request,
                source_context=self._build_queue_context(request),
            )
            delivery = self._delivery_builder.from_enqueue_acceptance(request, enqueue_result)
        else:
            motor_response = self._require_dispatch().dispatch_start_analysis(internal_request)
            pipeline_ctx = self._pipeline_context_dict(request.process_id)
            delivery = self._delivery_builder.from_start_analysis(
                request,
                motor_response,
                pipeline_context=pipeline_ctx,
            )

        self._record_outbound(delivery)
        return self._validate_and_deliver_outbound(
            delivery,
            operation="submit_analysis_request",
        )

    def query_analysis_status(
        self,
        request: EvidenceCenterStatusQuery,
    ) -> ErpAnalysisDelivery:
        if not self.is_ready():
            raise RuntimeError("ERP Communication Gateway no está listo")

        envelope = EcgMessageEnvelope.create(
            process_id=request.process_id,
            message_type=EcgMessageType.REQUEST,
            direction=EcgChannelDirection.ERP_TO_MOTOR,
            payload=request.to_dict(),
        )
        self._messages.append(envelope)

        if self._use_security() and self._security is not None:
            security_outcome = self._security.validate_inbound_status_query(request)
            if not security_outcome.approved:
                delivery = self._delivery_builder.from_security_rejection(
                    process_id=request.process_id,
                    project_id=request.project_id,
                    quotation_id=request.quotation_id,
                    outcome=security_outcome,
                )
                self._record_outbound(delivery)
                return delivery

        internal_request = self._transformer.to_status_query(request)
        motor_response = self._require_dispatch().dispatch_query_status(internal_request)

        pipeline_ctx = self._pipeline_context_dict(request.process_id)
        delivery = self._delivery_builder.from_status_query(
            request,
            motor_response,
            pipeline_context=pipeline_ctx,
        )
        self._record_outbound(delivery)
        return self._validate_and_deliver_outbound(
            delivery,
            operation="query_analysis_status",
        )

    def query_analysis_result(
        self,
        request: EvidenceCenterResultQuery,
    ) -> ErpAnalysisDelivery:
        if not self.is_ready():
            raise RuntimeError("ERP Communication Gateway no está listo")

        envelope = EcgMessageEnvelope.create(
            process_id=request.process_id,
            message_type=EcgMessageType.REQUEST,
            direction=EcgChannelDirection.ERP_TO_MOTOR,
            payload=request.to_dict(),
        )
        self._messages.append(envelope)

        if self._use_security() and self._security is not None:
            security_outcome = self._security.validate_inbound_result_query(request)
            if not security_outcome.approved:
                delivery = self._delivery_builder.from_security_rejection(
                    process_id=request.process_id,
                    project_id=request.project_id,
                    quotation_id=request.quotation_id,
                    outcome=security_outcome,
                )
                self._record_outbound(delivery)
                return delivery

        internal_request = self._transformer.to_result_query(request)
        motor_response = self._require_dispatch().dispatch_query_result(internal_request)

        pipeline_ctx = self._pipeline_context_dict(request.process_id)
        delivery = self._delivery_builder.from_result_query(
            request,
            motor_response,
            pipeline_context=pipeline_ctx,
        )
        self._record_outbound(delivery)
        return self._validate_and_deliver_outbound(
            delivery,
            operation="query_analysis_result",
        )

    def _pipeline_context_dict(self, process_id) -> dict[str, Any] | None:
        dispatch = self._dispatch
        if dispatch is None:
            return None
        context = dispatch.get_pipeline_context_dict(process_id)
        if context is None:
            return None
        return context.to_dict() if hasattr(context, "to_dict") else context

    def contract_catalog(self) -> dict[str, Any]:
        return {
            "ecg_v1": contract_snapshot(),
            "http_prepared": self._settings().http_transport_prepared,
            "queue_prepared": self._settings().queue_processing_prepared,
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "message_count": self._messages.count(),
            "dispatch_bound": self._dispatch is not None,
            "enqueue_bound": self._enqueue is not None,
            "security_bound": self._security is not None,
            "async_queue_enabled": self._use_async_queue(),
            "security_enabled": self._use_security(),
            "contract_catalog": self.contract_catalog(),
        }
