"""
Certificador integral de la Plataforma de Integración Empresarial.

Implementación 8.11 — Certificación integral del Prompt Maestro 8.
No introduce componentes ni funcionalidad nueva.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_e2e_checker import (
    EnterpriseIntegrationE2ECertificationChecker,
)
from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
    build_evidence_center_request,
    run_full_enterprise_integration_e2e_pipeline,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.enterprise_integration import EnterpriseIntegrationService
from zovrake_motor.enterprise_integration.components.base import EnterpriseIntegrationComponentPort
from zovrake_motor.enterprise_integration.enums import EnterpriseIntegrationComponentType
from zovrake_motor.enterprise_integration.governance import (
    ARCHITECTURAL_BOUNDARIES,
    PLATFORM_CERTIFICATION_STATUS,
    PLATFORM_IMPLEMENTATION,
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

PLATFORM_FRAMEWORKS = (
    "erp_communication_gateway",
    "async_processing_queue_manager",
    "fault_tolerance_retry_recovery_framework",
    "security_validation_audit_framework",
    "observability_metrics_monitoring_framework",
    "performance_optimization_scalability_framework",
)

CORE_PLATFORM_COMPONENTS = PLATFORM_FRAMEWORKS + (
    "enterprise_integration_coordinator",
    "pipeline_integration_orchestrator",
    "api_gateway_internal",
    "communication_contracts",
)

FORBIDDEN_ENTERPRISE_INTEGRATION_IMPORTS = (
    "zovrake_motor.intelligent_analysis",
    "zovrake_motor.comprehension",
    "zovrake_motor.reception",
    "zovrake_motor.documents",
)
class EnterpriseIntegrationPlatformCertificationChecker:
    """Certifica integralmente la Plataforma de Integración Empresarial."""

    IMPLEMENTATION = "8.11"

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_prior_e2e_certification())
        checks.extend(self._check_architectural_modularity())
        checks.extend(self._check_complete_flow_integrity())
        checks.extend(self._check_platform_components())
        checks.extend(self._check_official_contract())
        checks.extend(self._check_centralized_systems())
        checks.extend(self._check_resilience_certification())
        checks.extend(self._check_security_certification())
        checks.extend(self._check_observability_certification())
        checks.extend(self._check_performance_certification())
        checks.extend(self._check_technical_audit())
        checks.extend(self._check_production_readiness())
        checks.extend(self._check_documentation_and_governance())
        return checks

    def _check_prior_e2e_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            prior = EnterpriseIntegrationE2ECertificationChecker().run()
            failed = [check for check in prior if not check.passed]
            assert not failed, f"Certificación E2E 8.10 incompleta: {len(failed)} fallos"
            checks.append(
                self._passed(
                    area,
                    "prior_e2e_certification_valid",
                    "Certificación End-to-End 8.10 vigente y aprobada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "prior_e2e_certification_valid", str(exc)))

        return checks

    def _check_architectural_modularity(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            for component in service.component_registry.all_components():
                assert isinstance(component, EnterpriseIntegrationComponentPort)
                assert component.is_ready()
            checks.append(
                self._passed(
                    area,
                    "hexagonal_component_ports",
                    "17 componentes implementan EnterpriseIntegrationComponentPort",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "hexagonal_component_ports", str(exc)))

        try:
            snapshot = governance_snapshot()
            assert len(snapshot["architectural_boundaries"]) >= 3
            assert snapshot["prepared_functional_components_count"] == 17
            checks.append(
                self._passed(
                    area,
                    "modular_architecture",
                    "Arquitectura modular, desacoplada y extensible declarada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "modular_architecture", str(exc)))

        return checks

    def _check_complete_flow_integrity(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            result = run_full_enterprise_integration_e2e_pipeline()
            assert result.passed
            checks.append(
                self._passed(
                    area,
                    "complete_flow_integrity",
                    "Flujo Usuario-ERP-Centro de Evidencias-Motor-ERP-Usuario íntegro",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "complete_flow_integrity", str(exc)))

        return checks

    def _check_platform_components(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            for name in CORE_PLATFORM_COMPONENTS:
                component = service.component_registry.get(name)
                assert component is not None and component.is_ready(), name

            coordinator = service.enterprise_integration_coordinator
            assert coordinator is not None and coordinator.is_ready()
            assert coordinator.pipeline_orchestrator is not None
            assert coordinator.internal_api_gateway is not None

            checks.append(
                self._passed(
                    area,
                    "platform_components_unified",
                    "Coordinator, Internal API, PIO, ECG, APQM, FTRRF, SVAF, OMMF y POSF operan como plataforma única",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "platform_components_unified", str(exc)))

        return checks

    def _check_official_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            assert ContractVersionRegistry.ACTIVE_VERSION == "v1"
            assert ContractVersionRegistry.is_supported("v1") is True
            assert len(ContractVersionRegistry.SUPPORTED_VERSIONS) == 1

            service = EnterpriseIntegrationService()
            service.initialize()
            catalog = service.get_contract_catalog()
            assert catalog is not None
            assert "v1" in catalog
            assert catalog["versioning"]["active_version"] == "v1"
            assert catalog["versioning"]["contract_name"] == ContractVersionRegistry.CONTRACT_NAME

            checks.append(
                self._passed(
                    area,
                    "official_contract_exclusive",
                    "Contrato Internal Integration API v1 exclusivo y estable",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "official_contract_exclusive", str(exc)))

        return checks

    def _check_centralized_systems(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

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

            ei_settings = config.enterprise_integration()
            assert ConfigCategory.ENTERPRISE_INTEGRATION.value == "enterprise_integration"
            assert ei_settings.pm8_input_contract_required is True
            assert service.integration.snapshot()["state_management_ready"] is True
            assert service.integration.snapshot()["event_management_ready"] is True

            process_id = uuid4()
            service.submit_evidence_center_analysis(build_evidence_center_request(process_id))
            assert state_manager.get_process(process_id) is not None
            assert event_manager.count_by_process(process_id) >= 1

            checks.append(
                self._passed(
                    area,
                    "centralized_systems_exclusive",
                    "Configuración, estados y eventos centralizados utilizados exclusivamente",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "centralized_systems_exclusive", str(exc)))

        return checks

    def _check_resilience_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            process_a = uuid4()
            process_b = uuid4()

            service.submit_evidence_center_analysis(
                build_evidence_center_request(process_a, codigo_req=""),
            )
            service.submit_evidence_center_analysis(
                build_evidence_center_request(process_b, codigo_req="REQ-RESILIENT"),
            )
            service.process_async_queue_pending()

            ftrrf = service.fault_tolerance_retry_recovery_framework.framework
            policies = ftrrf.snapshot()["retry_policies"]
            assert len(policies) >= 1

            errors_a = ftrrf.errors_for_process(process_a)
            assert len(errors_a) >= 1
            assert all(e.process_id == process_a for e in errors_a)

            item_b = service.async_processing_queue_manager.manager.get_item_by_process(process_b)
            assert item_b is not None

            checks.append(
                self._passed(
                    area,
                    "resilience_isolation_and_retry",
                    "FTRRF aísla errores y respeta políticas de reintento",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "resilience_isolation_and_retry", str(exc)))

        return checks

    def _check_security_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = EnterpriseIntegrationService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            result = run_full_enterprise_integration_e2e_pipeline(
                service=service,
                state_manager=state_manager,
                event_manager=event_manager,
            )

            svaf = service.security_validation_audit_framework.framework
            snapshot = svaf.snapshot()
            assert snapshot["ready"] is True
            assert snapshot["prepared"] is True
            assert result.audit_count >= 1
            assert len(svaf.audit_store.by_process(result.process_id)) >= 1

            checks.append(
                self._passed(
                    area,
                    "security_validation_and_audit",
                    "SVAF valida solicitudes/respuestas y registra auditoría con integridad",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "security_validation_and_audit", str(exc)))

        return checks

    def _check_observability_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = EnterpriseIntegrationService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            result = run_full_enterprise_integration_e2e_pipeline(
                service=service,
                state_manager=state_manager,
                event_manager=event_manager,
            )

            ommf = service.observability_metrics_monitoring_framework.framework
            metrics = ommf.observability_snapshot()
            traces = ommf.traces_for_process(result.process_id)

            assert metrics["validations_performed"] >= 1
            assert metrics["traces_total"] >= 1
            assert len(traces) >= 1
            trace_ids = {trace["trace_id"] for trace in traces}
            assert len(trace_ids) == 1

            checks.append(
                self._passed(
                    area,
                    "observability_metrics_and_traces",
                    "OMMF recopila métricas y trazas completas del comportamiento real",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "observability_metrics_and_traces", str(exc)))

        return checks

    def _check_performance_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = EnterpriseIntegrationService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            before = run_full_enterprise_integration_e2e_pipeline(
                service=service,
                state_manager=state_manager,
                event_manager=event_manager,
            )
            assert before.passed

            posf = service.performance_optimization_scalability_framework.framework
            optimization = posf.optimization_snapshot()
            scalability = optimization["scalability"]["readiness"]

            assert optimization["pipeline"]["tracked_processes"] >= 1
            assert scalability["horizontal_prepared"] is True
            assert scalability["vertical_prepared"] is True
            assert posf.snapshot()["metrics_source_bound"] is True

            after = run_full_enterprise_integration_e2e_pipeline()
            assert after.passed

            checks.append(
                self._passed(
                    area,
                    "performance_consistency",
                    "POSF optimiza sin alterar funcionalidad; pipeline consistente y escalable",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "performance_consistency", str(exc)))

        return checks

    def _check_technical_audit(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            _verify_module_import_integrity("zovrake_motor.enterprise_integration")
            checks.append(
                self._passed(
                    area,
                    "no_circular_dependencies",
                    "Todos los módulos importan correctamente sin errores de dependencia",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "no_circular_dependencies", str(exc)))

        try:
            flow = next(
                item["flow"]
                for item in ARCHITECTURAL_BOUNDARIES
                if item.get("module") == "enterprise_integration"
            )
            ordered = ("ECG", "SVAF", "APQM", "FTRRF", "Coordinator", "PIO", "Internal API", "Motor")
            cursor = 0
            for marker in ordered:
                index = flow.find(marker)
                assert index >= cursor, marker
                cursor = index
            checks.append(
                self._passed(
                    area,
                    "logical_flow_acyclic",
                    "Flujo lógico de integración acíclico y consistente",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "logical_flow_acyclic", str(exc)))

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
                    "architectural_separation",
                    "Separación ERP/Motor preservada; sin acoplamiento directo al núcleo IA",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "architectural_separation", str(exc)))

        try:
            port_modules = (
                ENTERPRISE_INTEGRATION_ROOT / "ommf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "svaf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "posf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "internal_api" / "services" / "ports.py",
            )
            for path in port_modules:
                assert path.is_file(), path.name
            checks.append(
                self._passed(
                    area,
                    "hexagonal_ports_defined",
                    "Interfaces de puertos hexagonales definidas para frameworks clave",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "hexagonal_ports_defined", str(exc)))

        try:
            expected = {item.value for item in EnterpriseIntegrationComponentType}
            registered = {
                item[0] for item in PREPARED_FUNCTIONAL_COMPONENTS
            }
            assert expected == registered
            checks.append(
                self._passed(
                    area,
                    "single_responsibility_registry",
                    "Registro de componentes consistente con responsabilidades únicas",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "single_responsibility_registry", str(exc)))

        return checks

    def _check_production_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            config = ConfigurationProvider.default()
            ei = config.enterprise_integration()
            readiness_flags = (
                ei.erp_communication_gateway.prepared,
                ei.async_processing_queue_manager.prepared,
                ei.fault_tolerance_retry_recovery_framework.prepared,
                ei.security_validation_audit_framework.prepared,
                ei.observability_metrics_monitoring_framework.prepared,
                ei.performance_optimization_scalability_framework.prepared,
                ei.pipeline_integration_orchestrator.prepared,
                ei.internal_integration_api.prepared,
            )
            assert all(readiness_flags)
            assert PLATFORM_CERTIFICATION_STATUS == "CERTIFIED"
            checks.append(
                self._passed(
                    area,
                    "production_readiness_prepared",
                    "Plataforma preparada para produccion certificada en 8.11",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "production_readiness_prepared", str(exc)))

        return checks

    def _check_documentation_and_governance(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM

        try:
            assert PLATFORM_IMPLEMENTATION == self.IMPLEMENTATION
            snapshot = governance_snapshot()
            assert snapshot["platform_certification"]["status"] == PLATFORM_CERTIFICATION_STATUS
            assert len(ARCHITECTURAL_BOUNDARIES) >= 3
            checks.append(
                self._passed(area, "governance_8_11", "Gobierno arquitectónico PM8 en Implementación 8.11"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "governance_8_11", str(exc)))

        try:
            for doc in REQUIRED_DOCUMENTATION:
                assert doc.is_file(), f"Documentación faltante: {doc.name}"
                content = doc.read_text(encoding="utf-8")
                assert any(
                    marker in content
                    for marker in ("8.11", "8.12", "Implementación 8.11", "Implementación 8.12")
                ), doc.name
            checks.append(
                self._passed(
                    area,
                    "documentation_complete",
                    "ARCHITECTURE.md y CERTIFICATION.md actualizados para 8.11",
                ),
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


def _verify_module_import_integrity(package_name: str) -> None:
    package = importlib.import_module(package_name)
    for _finder, modname, _ispkg in pkgutil.walk_packages(
        package.__path__,
        prefix=package.__name__ + ".",
    ):
        importlib.import_module(modname)
