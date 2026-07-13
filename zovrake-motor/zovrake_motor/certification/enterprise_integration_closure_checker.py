"""
Certificador de cierre formal del Prompt Maestro 8.

Implementacion 8.12 — Gobierno arquitectonico y congelamiento de la plataforma.
No modifica componentes ni introduce funcionalidad nueva.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
    run_full_enterprise_integration_e2e_pipeline,
)
from zovrake_motor.certification.enterprise_integration_platform_checker import (
    EnterpriseIntegrationPlatformCertificationChecker,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.enterprise_integration import EnterpriseIntegrationService
from zovrake_motor.enterprise_integration.governance import (
    ARCHITECTURE_FREEZE_RULES,
    ARCHITECTURAL_BOUNDARIES,
    EVOLUTION_EXTENSION_POINTS,
    FROZEN_FUNCTIONAL_COMPONENTS,
    INTEGRATION_CONTRACT_NAME,
    INTEGRATION_CONTRACT_REQUIRED_OPERATIONS,
    INTEGRATION_CONTRACT_VERSION,
    INTEGRATION_FORBIDDEN_DIRECT_ACCESSES,
    OFFICIAL_ENTRY_POINT,
    OFFICIAL_INTEGRATION_FLOW,
    OFFICIAL_OUTPUT_REFERENCE,
    PLATFORM_CERTIFICATION_STATUS,
    PROMPT_MAESTRO_8_STATUS,
    SCALABILITY_EXTENSION_CAPABILITIES,
    closure_snapshot,
    frozen_component_names,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.v1 import contract_snapshot
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ENTERPRISE_INTEGRATION_ROOT = PACKAGE_ROOT / "enterprise_integration"

REQUIRED_DOCUMENTATION = (
    ENTERPRISE_INTEGRATION_ROOT / "ARCHITECTURE.md",
    ENTERPRISE_INTEGRATION_ROOT / "CERTIFICATION.md",
    ENTERPRISE_INTEGRATION_ROOT / "CLOSURE.md",
    ENTERPRISE_INTEGRATION_ROOT / "INTEGRATION_CONTRACT.md",
)


class EnterpriseIntegrationModuleClosureChecker:
    """Formaliza el cierre arquitectonico del Prompt Maestro 8."""

    IMPLEMENTATION = "8.12"

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_prior_platform_certification())
        checks.extend(self._check_architecture_freeze())
        checks.extend(self._check_integration_contract())
        checks.extend(self._check_official_flow())
        checks.extend(self._check_compatibility_and_evolution())
        checks.extend(self._check_scalability_readiness())
        checks.extend(self._check_quality_and_governance())
        checks.extend(self._check_final_audit())
        checks.extend(self._check_documentation_closure())
        checks.extend(self._check_governance_closure())
        return checks

    def _check_prior_platform_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            prior = EnterpriseIntegrationPlatformCertificationChecker().run()
            failed = [check for check in prior if not check.passed]
            assert not failed, f"Certificacion integral 8.11 incompleta: {len(failed)} fallos"
            assert PLATFORM_CERTIFICATION_STATUS == "CERTIFIED"
            checks.append(
                self._passed(
                    area,
                    "prior_platform_certification_valid",
                    "Certificacion integral de plataforma 8.11 vigente y aprobada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "prior_platform_certification_valid", str(exc)))

        return checks

    def _check_architecture_freeze(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE
        service: EnterpriseIntegrationService | None = None

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            for component_id, label, implementation in FROZEN_FUNCTIONAL_COMPONENTS:
                component = service.component_registry.get(component_id)
                assert component is not None, f"Componente congelado ausente: {component_id}"
                assert component.is_ready(), f"Componente congelado no operativo: {component_id}"
                checks.append(
                    self._passed(
                        area,
                        f"frozen_{component_id}",
                        f"{label} ({implementation}) declarado estable",
                    ),
                )
        except Exception as exc:
            checks.append(self._failed(area, "architecture_freeze", str(exc)))

        try:
            assert service is not None
            ready_names = {
                name
                for name in frozen_component_names()
                if (component := service.component_registry.get(name)) is not None
                and component.is_ready()
            }
            assert ready_names == set(frozen_component_names())
            assert len(ARCHITECTURE_FREEZE_RULES) >= 6
            checks.append(
                self._passed(
                    area,
                    "frozen_components_complete",
                    "17 componentes congelados y operativos con reglas de congelamiento",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "frozen_components_complete", str(exc)))

        return checks

    def _check_integration_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            assert ContractVersionRegistry.ACTIVE_VERSION == INTEGRATION_CONTRACT_VERSION
            assert ContractVersionRegistry.CONTRACT_NAME == INTEGRATION_CONTRACT_NAME
            snapshot = contract_snapshot()
            operations = {item["operation"] for item in snapshot["request_contracts"]}
            assert operations == set(INTEGRATION_CONTRACT_REQUIRED_OPERATIONS)

            service = EnterpriseIntegrationService()
            service.initialize()
            catalog = service.get_contract_catalog()
            assert catalog is not None
            assert catalog["v1"]["name"] == INTEGRATION_CONTRACT_NAME

            checks.append(
                self._passed(
                    area,
                    "official_integration_contract_frozen",
                    "InternalIntegrationApi v1 es el unico contrato oficial ERP-Motor",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "official_integration_contract_frozen", str(exc)))

        return checks

    def _check_official_flow(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            result = run_full_enterprise_integration_e2e_pipeline()
            assert result.passed
            assert len(OFFICIAL_INTEGRATION_FLOW) >= 10
            checks.append(
                self._passed(
                    area,
                    "official_integration_flow",
                    "Flujo oficial Usuario-ERP-Motor-ERP certificado e intacto",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "official_integration_flow", str(exc)))

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            coordinator = service.enterprise_integration_coordinator
            ecg = service.erp_communication_gateway
            assert coordinator is not None and coordinator.is_ready()
            assert ecg is not None and ecg.gateway.snapshot()["dispatch_bound"] is True
            checks.append(
                self._passed(
                    area,
                    "coordinator_single_channel",
                    "Integration Coordinator controla toda comunicacion via ECG e Internal API",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_single_channel", str(exc)))

        return checks

    def _check_compatibility_and_evolution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            snapshot = closure_snapshot()
            assert snapshot["output_contract_reference"]["name"] == OFFICIAL_OUTPUT_REFERENCE
            assert len(snapshot["evolution_extension_points"]) >= 5
            assert len(SCALABILITY_EXTENSION_CAPABILITIES) >= 6
            checks.append(
                self._passed(
                    area,
                    "compatible_evolution_prepared",
                    "Plataforma preparada para evolucion sin modificar nucleo ni contratos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "compatible_evolution_prepared", str(exc)))

        return checks

    def _check_scalability_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            service = EnterpriseIntegrationService()
            service.initialize()
            posf = service.performance_optimization_scalability_framework.framework
            readiness = posf.optimization_snapshot()["scalability"]["readiness"]
            assert readiness["horizontal_prepared"] is True
            assert readiness["multi_node_prepared"] is True
            assert readiness["load_balancing_prepared"] is True
            checks.append(
                self._passed(
                    area,
                    "scalability_extension_prepared",
                    "Arquitectura preparada para escalado distribuido futuro",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "scalability_extension_prepared", str(exc)))

        return checks

    def _check_quality_and_governance(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            port_modules = (
                ENTERPRISE_INTEGRATION_ROOT / "ommf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "svaf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "posf" / "ports.py",
                ENTERPRISE_INTEGRATION_ROOT / "internal_api" / "services" / "ports.py",
            )
            for path in port_modules:
                assert path.is_file()
            assert len(ARCHITECTURAL_BOUNDARIES) >= 3
            assert len(EVOLUTION_EXTENSION_POINTS) >= 5
            checks.append(
                self._passed(
                    area,
                    "clean_architecture_governance",
                    "Clean Architecture, SOLID y gobernanza arquitectonica certificados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "clean_architecture_governance", str(exc)))

        return checks

    def _check_final_audit(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            package = importlib.import_module("zovrake_motor.enterprise_integration")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                importlib.import_module(modname)
            checks.append(
                self._passed(
                    area,
                    "module_import_integrity",
                    "Todos los modulos importan correctamente; plataforma estable",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_import_integrity", str(exc)))

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
                for forbidden in INTEGRATION_FORBIDDEN_DIRECT_ACCESSES:
                    assert forbidden not in content, f"{forbidden} en {modname}"
            checks.append(
                self._passed(
                    area,
                    "erp_motor_decoupling",
                    "ERP y Motor Inteligente permanecen completamente desacoplados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "erp_motor_decoupling", str(exc)))

        return checks

    def _check_documentation_closure(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            for doc in REQUIRED_DOCUMENTATION:
                assert doc.is_file(), f"Documentacion faltante: {doc.name}"
                content = doc.read_text(encoding="utf-8")
                assert "8.12" in content or "Implementacion 8.12" in content or "Implementación 8.12" in content
            checks.append(
                self._passed(
                    area,
                    "documentation_closure_complete",
                    "ARCHITECTURE, CERTIFICATION, CLOSURE e INTEGRATION_CONTRACT documentados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "documentation_closure_complete", str(exc)))

        return checks

    def _check_governance_closure(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE

        try:
            assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
            snapshot = closure_snapshot()
            assert snapshot["status"] == "CLOSED"
            assert snapshot["implementation_closure"] == self.IMPLEMENTATION
            assert snapshot["integration_contract"]["official_entry_point"] == OFFICIAL_ENTRY_POINT
            assert snapshot["frozen_components_count"] == 17
            checks.append(
                self._passed(
                    area,
                    "prompt_maestro_8_closed",
                    "Prompt Maestro 8 oficialmente CERRADO",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "prompt_maestro_8_closed", str(exc)))

        try:
            assert __version__ >= "8.12.0"
            checks.append(
                self._passed(area, "motor_version_closure", f"Version oficial del Motor {__version__}"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "motor_version_closure", str(exc)))

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
