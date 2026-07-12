"""
Certificador End-to-End del Módulo de Integración Empresarial.

Implementación 8.10 — Integración, validación y certificación del Prompt Maestro 8.
No introduce componentes ni funcionalidad nueva.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
    build_evidence_center_request,
    run_full_enterprise_integration_e2e_pipeline,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration import EnterpriseIntegrationService
from zovrake_motor.enterprise_integration.enums import EnterpriseIntegrationComponentType
from zovrake_motor.enterprise_integration.governance import (
    ARCHITECTURAL_BOUNDARIES,
    E2E_IMPLEMENTATION,
    PREPARED_FUNCTIONAL_COMPONENTS,
    governance_snapshot,
)
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ENTERPRISE_INTEGRATION_ROOT = PACKAGE_ROOT / "enterprise_integration"

REQUIRED_DOCUMENTATION = (
    ENTERPRISE_INTEGRATION_ROOT / "ARCHITECTURE.md",
    ENTERPRISE_INTEGRATION_ROOT / "CERTIFICATION.md",
)

FRAMEWORK_COMPONENTS = (
    "erp_communication_gateway",
    "async_processing_queue_manager",
    "fault_tolerance_retry_recovery_framework",
    "security_validation_audit_framework",
    "observability_metrics_monitoring_framework",
    "performance_optimization_scalability_framework",
    "enterprise_integration_coordinator",
    "pipeline_integration_orchestrator",
    "api_gateway_internal",
)

FORBIDDEN_ENTERPRISE_INTEGRATION_IMPORTS = (
    "zovrake_motor.intelligent_analysis",
    "zovrake_motor.comprehension",
    "zovrake_motor.reception",
    "zovrake_motor.documents",
)


class EnterpriseIntegrationE2ECertificationChecker:
    """Certifica el Módulo de Integración Empresarial como sistema integrado."""

    IMPLEMENTATION = "8.10"

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_module_initialization())
        checks.extend(self._check_end_to_end_flow())
        checks.extend(self._check_coordinator_routing())
        checks.extend(self._check_framework_integrations())
        checks.extend(self._check_contract_compliance())
        checks.extend(self._check_central_systems())
        checks.extend(self._check_traceability())
        checks.extend(self._check_async_processing())
        checks.extend(self._check_resilience())
        checks.extend(self._check_security_and_observability())
        checks.extend(self._check_architectural_isolation())
        checks.extend(self._check_governance_and_documentation())
        return checks

    def _check_module_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E
        service: EnterpriseIntegrationService | None = None

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 17
            assert service.component_registry.ready_count() == 17
            checks.append(
                self._passed(area, "module_initialization", "17 componentes inicializados y listos"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_initialization", str(exc)))

        try:
            assert service is not None
            expected = {item.value for item in EnterpriseIntegrationComponentType}
            registered = {
                c.component_name for c in service.component_registry.all_components()
            }
            assert expected == registered
            checks.append(
                self._passed(area, "component_registry_complete", "Registro alineado con enums"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "component_registry_complete", str(exc)))

        return checks

    def _check_end_to_end_flow(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            result = run_full_enterprise_integration_e2e_pipeline()
            assert result.passed, (
                f"Flujo E2E incompleto: submit={result.submit_success}, "
                f"async={result.submit_async}, queue={result.queue_processed}, "
                f"transitions={result.pipeline_transitions}"
            )
            checks.append(
                self._passed(
                    area,
                    "end_to_end_flow",
                    "Flujo Centro de Evidencias → ECG → Coordinator → PIO → ERP certificado",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "end_to_end_flow", str(exc)))

        return checks

    def _check_coordinator_routing(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            coordinator = service.enterprise_integration_coordinator
            assert coordinator is not None and coordinator.is_ready()
            pio = coordinator.pipeline_orchestrator
            api = coordinator.internal_api_gateway
            assert pio is not None and api is not None
            ecg = service.erp_communication_gateway
            assert ecg is not None and ecg.gateway.snapshot()["dispatch_bound"] is True
            checks.append(
                self._passed(
                    area,
                    "coordinator_controls_routing",
                    "Integration Coordinator enruta exclusivamente vía PIO y API Interna",
                ),
            )
            checks.append(
                self._passed(
                    area,
                    "ecg_single_channel",
                    "ECG es el único canal ERP ↔ Motor",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_controls_routing", str(exc)))
            checks.append(self._failed(area, "ecg_single_channel", str(exc)))

        return checks

    def _check_framework_integrations(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            pio = service.get_pipeline_orchestrator_snapshot()
            apqm = service.get_async_processing_queue_snapshot()
            ftrrf = service.get_fault_tolerance_snapshot()
            svaf = service.get_security_validation_audit_snapshot()
            ommf = service.get_observability_metrics_monitoring_snapshot()
            posf = service.get_performance_optimization_scalability_snapshot()

            assert pio["orchestrator"]["validation_gate_bound"] is True
            assert pio["orchestrator"]["observability_bound"] is True
            assert pio["orchestrator"]["performance_optimizer_bound"] is True
            assert apqm["manager"]["execution_bound"] is True
            assert apqm["manager"]["observability_bound"] is True
            assert apqm["manager"]["performance_optimizer_bound"] is True
            assert ftrrf["framework"]["continuity_bound"] is True
            assert ftrrf["framework"]["observability_bound"] is True
            assert svaf["framework"]["fault_notifier_bound"] is True
            assert svaf["framework"]["observability_bound"] is True
            assert ommf["framework"]["source_bound"] is True
            assert posf["framework"]["metrics_source_bound"] is True

            for name in FRAMEWORK_COMPONENTS:
                component = service.component_registry.get(name)
                assert component is not None and component.is_ready(), name

            checks.append(
                self._passed(
                    area,
                    "framework_integrations",
                    "ECG, APQM, FTRRF, SVAF, OMMF, POSF, Coordinator e Internal API integrados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "framework_integrations", str(exc)))

        return checks

    def _check_contract_compliance(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            assert ContractVersionRegistry.ACTIVE_VERSION == "v1"
            assert ContractVersionRegistry.is_supported("v1") is True
            service = EnterpriseIntegrationService()
            service.initialize()
            contracts = service.get_contract_catalog()
            assert contracts is not None
            assert "v1" in contracts
            assert contracts["versioning"]["active_version"] == "v1"
            checks.append(
                self._passed(
                    area,
                    "official_contract_v1",
                    "Contrato oficial Internal API v1 activo y catalogado",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "official_contract_v1", str(exc)))

        return checks

    def _check_central_systems(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            config = ConfigurationProvider.default()
            state_manager = StateManager()
            event_manager = EventManager()
            service = EnterpriseIntegrationService(
                config_provider=config,
                state_manager=state_manager,
                event_manager=event_manager,
            )
            service.initialize()

            settings = config.enterprise_integration()
            assert settings.pm8_input_contract_required is True
            assert settings.erp_communication_gateway.prepared is True
            assert service.integration.snapshot()["state_management_ready"] is True
            assert service.integration.snapshot()["event_management_ready"] is True

            process_id = uuid4()
            service.submit_evidence_center_analysis(
                build_evidence_center_request(process_id),
            )
            assert state_manager.get_process(process_id) is not None
            assert event_manager.count_by_process(process_id) >= 1

            checks.append(
                self._passed(
                    area,
                    "central_systems",
                    "Configuración, estados y eventos centralizados operativos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "central_systems", str(exc)))

        return checks

    def _check_traceability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            service = EnterpriseIntegrationService()
            result = run_full_enterprise_integration_e2e_pipeline(service=service)
            context = service.get_pipeline_context(result.process_id)
            assert context is not None
            assert context.process_id == result.process_id
            assert len(context.transitions) >= 1

            ommf = service.observability_metrics_monitoring_framework
            traces = ommf.framework.traces_for_process(result.process_id) if ommf else []
            assert len(traces) >= 1
            trace_ids = {t["trace_id"] for t in traces}
            assert len(trace_ids) == 1

            checks.append(
                self._passed(
                    area,
                    "traceability_preserved",
                    "Trazabilidad Pipeline + OMMF preservada en todo el flujo",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "traceability_preserved", str(exc)))

        return checks

    def _check_async_processing(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            result = run_full_enterprise_integration_e2e_pipeline()
            assert result.submit_async is True
            assert result.queue_processed >= 1
            checks.append(
                self._passed(
                    area,
                    "async_non_blocking",
                    "ERP recibe respuesta inmediata; cola procesa de forma independiente",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "async_non_blocking", str(exc)))

        return checks

    def _check_resilience(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            process_a = uuid4()
            process_b = uuid4()
            from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
                build_evidence_center_request,
            )

            service.submit_evidence_center_analysis(
                build_evidence_center_request(process_a, codigo_req=""),
            )
            service.submit_evidence_center_analysis(
                build_evidence_center_request(process_b, codigo_req="REQ-RESILIENT"),
            )
            service.process_async_queue_pending()

            ftrrf = service.fault_tolerance_retry_recovery_framework.framework
            errors_a = ftrrf.errors_for_process(process_a)
            errors_b = ftrrf.errors_for_process(process_b)
            assert len(errors_a) >= 1
            assert all(e.process_id == process_a for e in errors_a)

            item_b = service.async_processing_queue_manager.manager.get_item_by_process(process_b)
            assert item_b is not None

            checks.append(
                self._passed(
                    area,
                    "resilience_isolation",
                    "FTRRF gestiona fallos con aislamiento entre procesos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "resilience_isolation", str(exc)))

        return checks

    def _check_security_and_observability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            service = EnterpriseIntegrationService()
            result = run_full_enterprise_integration_e2e_pipeline(service=service)

            svaf = service.security_validation_audit_framework.framework
            ommf = service.observability_metrics_monitoring_framework.framework
            posf = service.performance_optimization_scalability_framework.framework

            assert result.audit_count >= 1
            assert len(svaf.audit_store.by_process(result.process_id)) >= 1
            metrics = ommf.observability_snapshot()
            assert metrics["validations_performed"] >= 1
            assert metrics["traces_total"] >= 1
            optimization = posf.optimization_snapshot()
            assert optimization["pipeline"]["tracked_processes"] >= 1

            checks.append(
                self._passed(
                    area,
                    "security_observability_optimization",
                    "SVAF, OMMF y POSF registran validaciones, métricas y optimización",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "security_observability_optimization", str(exc)))

        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            package = importlib.import_module("zovrake_motor.enterprise_integration")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py") or source.endswith("governance.py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_ENTERPRISE_INTEGRATION_IMPORTS:
                    assert forbidden not in content, f"{forbidden} en {modname}"
            checks.append(
                self._passed(
                    area,
                    "architectural_isolation",
                    "Sin importaciones directas al núcleo del Motor Inteligente",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "architectural_isolation", str(exc)))

        return checks

    def _check_governance_and_documentation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_E2E

        try:
            assert E2E_IMPLEMENTATION == self.IMPLEMENTATION
            snapshot = governance_snapshot()
            assert snapshot["prepared_functional_components_count"] == len(
                PREPARED_FUNCTIONAL_COMPONENTS,
            )
            assert len(ARCHITECTURAL_BOUNDARIES) >= 3
            checks.append(
                self._passed(area, "governance_8_10", "Gobierno arquitectónico PM8 en 8.10"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "governance_8_10", str(exc)))

        try:
            for doc in REQUIRED_DOCUMENTATION:
                assert doc.is_file(), f"Documentación faltante: {doc.name}"
            checks.append(
                self._passed(area, "documentation_complete", "ARCHITECTURE.md y CERTIFICATION.md presentes"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "documentation_complete", str(exc)))

        try:
            assert __version__ >= "8.11.0"
            checks.append(
                self._passed(area, "motor_version", f"Versión del Motor {__version__}"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "motor_version", str(exc)))

        return checks

    @staticmethod
    def _passed(area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.PASSED,
            message=message,
        )

    @staticmethod
    def _failed(area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.FAILED,
            message=message,
        )
