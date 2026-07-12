"""Pipeline interno del Módulo de Integración Empresarial."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.enterprise_integration.enums import EnterpriseIntegrationPhase
from zovrake_motor.enterprise_integration.registry import ComponentRegistry


@dataclass(frozen=True)
class EnterpriseIntegrationPipelineStage:
    """Etapa del flujo de integración — referencia arquitectónica."""

    phase: EnterpriseIntegrationPhase
    label: str
    order: int
    component_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "label": self.label,
            "order": self.order,
            "component_name": self.component_name,
        }


class EnterpriseIntegrationPipeline:
    """
    Pipeline de integración empresarial del módulo.

    El consumo del Resultado del Análisis Inteligente es la primera etapa funcional
    preparada del flujo ERP ↔ Motor.
    """

    DEFAULT_STAGES: tuple[EnterpriseIntegrationPipelineStage, ...] = (
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.PREPARACION,
            "Preparación",
            1,
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.CONSUMO_RESULTADO_ANALISIS_INTELIGENTE,
            "Consumo del Resultado del Análisis Inteligente",
            2,
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.API_INTERNA,
            "API Interna",
            3,
            "api_gateway_internal",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.ENVIO_SOLICITUD,
            "Envío de Solicitud",
            4,
            "request_dispatcher",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.RECEPCION_RESPUESTA,
            "Recepción de Respuesta",
            5,
            "response_dispatcher",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_ESTADO_PROCESO,
            "Gestión de Estado de Proceso",
            6,
            "process_status_manager",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_ERRORES,
            "Gestión de Errores",
            7,
            "error_management_framework",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_CONTRATOS,
            "Gestión de Contratos",
            8,
            "communication_contracts",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_EVENTOS_INTEGRACION,
            "Gestión de Eventos de Integración",
            9,
            "integration_event_manager",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_TRAZABILIDAD_INTEGRACION,
            "Gestión de Trazabilidad de Integración",
            10,
            "integration_traceability_manager",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.GESTION_CONFIGURACION_INTEGRACION,
            "Gestión de Configuración de Integración",
            11,
            "integration_configuration_manager",
        ),
        EnterpriseIntegrationPipelineStage(
            EnterpriseIntegrationPhase.FINALIZACION,
            "Finalización",
            12,
            "enterprise_integration_coordinator",
        ),
    )

    @classmethod
    def ordered_phases(cls) -> tuple[EnterpriseIntegrationPhase, ...]:
        return tuple(stage.phase for stage in cls.DEFAULT_STAGES)

    @classmethod
    def build_snapshot(cls, registry: ComponentRegistry) -> list[dict[str, Any]]:
        snapshot: list[dict[str, Any]] = []
        for stage in cls.DEFAULT_STAGES:
            component_ready = None
            if stage.component_name is not None:
                component = registry.get(stage.component_name)
                component_ready = component.is_ready() if component is not None else False
            snapshot.append(
                {
                    **stage.to_dict(),
                    "component_ready": component_ready,
                }
            )
        return snapshot
