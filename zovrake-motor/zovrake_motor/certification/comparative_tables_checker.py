"""
Certificador integral del Módulo de Generación de Cuadros Comparativos.

Implementación 4.11 — Integración y certificación del Prompt Maestro 6.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.certification.comparative_tables_pipeline import (
    run_full_comparative_tables_pipeline,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_CATALOG_REQUIRED_FIELDS,
    PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS,
    PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.governance import (
    FROZEN_FUNCTIONAL_COMPONENTS,
    OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.service import ComparativeTablesService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager

FORBIDDEN_COMPARATIVE_TABLES_IMPORTS = (
    "zovrake_motor.reception",
    "zovrake_motor.documents",
    "zovrake_motor.context",
    "zovrake_motor.communication",
    "zovrake_motor.comprehension",
    "zovrake_motor.classification",
)

PIPELINE_ENGINE_COMPONENTS = (
    ("comparative_structure_engine", "Comparative Structure Engine"),
    ("dynamic_column_builder", "Dynamic Column Builder"),
    ("dynamic_row_builder", "Dynamic Row Builder"),
    ("provider_organization_engine", "Provider Organization Engine"),
    ("group_integrity_engine", "Group Integrity Engine"),
    ("traceability_metadata_engine", "Traceability & Metadata Engine"),
    ("comparative_model_builder", "Comparative Model Builder"),
    ("comparative_validation_framework", "Comparative Validation Framework"),
    ("comparative_quality_framework", "Comparative Quality Framework"),
)

EXPECTED_PIPELINE_PHASES = (
    ComparativeTablesPhase.PREPARACION,
    ComparativeTablesPhase.CONSUMO_MODELO_DOMINIO,
    ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA,
    ComparativeTablesPhase.CONSTRUCCION_COLUMNAS,
    ComparativeTablesPhase.CONSTRUCCION_FILAS,
    ComparativeTablesPhase.ORGANIZACION_PROVEEDORES,
    ComparativeTablesPhase.INTEGRIDAD_GRUPOS,
    ComparativeTablesPhase.TRAZABILIDAD_METADATOS,
    ComparativeTablesPhase.MODELO_COMPARATIVO,
    ComparativeTablesPhase.VALIDACION_COMPARATIVA,
    ComparativeTablesPhase.VALIDACION_CALIDAD,
    ComparativeTablesPhase.FINALIZACION,
)


class ComparativeTablesModuleCertificationChecker:
    """Certifica el Módulo de Generación de Cuadros Comparativos como sistema integrado."""

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_module_initialization())
        checks.extend(self._check_pipeline_structure())
        checks.extend(self._check_full_pipeline_execution())
        checks.extend(self._check_traceability_and_immutability())
        checks.extend(self._check_coordinator_integration())
        checks.extend(self._check_state_and_event_integration())
        checks.extend(self._check_central_configuration())
        checks.extend(self._check_architectural_isolation())
        checks.extend(self._check_extensibility())
        checks.extend(self._check_definitive_model_consistency())
        checks.extend(self._check_governance_and_contract())
        return checks

    def _check_module_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            service = ComparativeTablesService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 10
            checks.append(
                self._passed(area, "module_initialization", "Módulo inicializado con 10 componentes"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_initialization", str(exc)))
            return checks

        try:
            ready = service.component_registry.ready_count()
            assert ready == 10
            checks.append(
                self._passed(area, "components_ready", f"10 componentes operativos del pipeline ({ready})"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "components_ready", str(exc)))

        for component_name, label in PIPELINE_ENGINE_COMPONENTS:
            try:
                component = service.component_registry.get(component_name)
                assert component is not None
                assert component.is_ready()
                checks.append(self._passed(area, f"engine_{component_name}", f"{label} operativo"))
            except Exception as exc:
                checks.append(self._failed(area, f"engine_{component_name}", str(exc)))

        return checks

    def _check_pipeline_structure(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            phases = ComparativeTablesPipeline.ordered_phases()
            assert phases == EXPECTED_PIPELINE_PHASES
            checks.append(
                self._passed(area, "pipeline_phases", "12 etapas del Pipeline PM6 certificadas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_phases", str(exc)))

        try:
            service = ComparativeTablesService()
            service.initialize()
            snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
            functional_stages = [
                stage
                for stage in snapshot
                if stage.get("component_name") in {name for name, _ in PIPELINE_ENGINE_COMPONENTS}
            ]
            assert len(functional_stages) == 9
            assert all(stage["component_ready"] for stage in functional_stages)
            checks.append(
                self._passed(area, "pipeline_stages_registered", "9 etapas funcionales registradas y listas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_stages_registered", str(exc)))

        return checks

    def _check_full_pipeline_execution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            service = ComparativeTablesService()
            service.initialize()
            process_id = uuid4()
            result = run_full_comparative_tables_pipeline(
                service,
                process_id=process_id,
                document_id="DOC-FULL-PM6-CERT",
            )
            assert result.complete
            assert result.stages_executed == 9
            checks.append(
                self._passed(
                    area,
                    "full_pipeline_execution",
                    "Pipeline completo ejecutado sin interrupciones (9 etapas funcionales)",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "full_pipeline_execution", str(exc)))

        return checks

    def _check_traceability_and_immutability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            service = ComparativeTablesService()
            service.initialize()
            result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
            assert result.traceability_intact
            checks.append(
                self._passed(area, "traceability_chain", "Cadena de trazabilidad intacta en todo el flujo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "traceability_chain", str(exc)))

        try:
            service = ComparativeTablesService()
            service.initialize()
            result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
            assert result.domain_model_preserved
            assert result.definitive_catalog_preserved
            checks.append(
                self._passed(
                    area,
                    "source_immutability",
                    "Modelo de dominio y catálogo definitivo preservados sin modificación",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "source_immutability", str(exc)))

        return checks

    def _check_coordinator_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            config = ConfigurationProvider.default()
            coordinator = MotorCoordinator(config_provider=config)
            service = ComparativeTablesService(config_provider=config)
            service.initialize()
            coordinator.register_module(service)
            coordinator.initialize_modules()
            coordinator.prepare_modules()
            assert coordinator.is_module_available("comparative_tables")
            checks.append(
                self._passed(
                    area,
                    "coordinator_registration",
                    "Coordinator administra el módulo de Cuadros Comparativos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_registration", str(exc)))

        return checks

    def _check_state_and_event_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = ComparativeTablesService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            service.initialize()
            process_id = uuid4()
            run_full_comparative_tables_pipeline(service, process_id=process_id)

            state = state_manager.get_process(process_id)
            assert state is not None
            assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
            assert event_manager.count() >= 2
            checks.append(
                self._passed(area, "state_event_integration", "Estados y eventos registrados durante el Pipeline"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "state_event_integration", str(exc)))

        return checks

    def _check_central_configuration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            provider = ConfigurationProvider.default()
            comparative_tables = provider.comparative_tables()
            required = (
                "comparative_structure_engine",
                "dynamic_column_builder",
                "dynamic_row_builder",
                "provider_organization_engine",
                "group_integrity_engine",
                "traceability_metadata_engine",
                "comparative_model_builder",
                "comparative_validation_framework",
                "comparative_quality_framework",
            )
            for attr in required:
                assert hasattr(comparative_tables, attr)
            checks.append(
                self._passed(
                    area,
                    "central_configuration",
                    "Configuración central unificada para todos los motores PM6",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "central_configuration", str(exc)))

        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            package = importlib.import_module("zovrake_motor.comparative_tables")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_COMPARATIVE_TABLES_IMPORTS:
                    assert forbidden not in content, f"{modname} importa {forbidden}"
            checks.append(
                self._passed(area, "module_isolation", "Sin dependencias directas entre módulos del Motor"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_isolation", str(exc)))

        try:
            service = ComparativeTablesService()
            service.initialize()
            gateway_snapshot = service.classification_gateway.snapshot()
            assert gateway_snapshot.get("accesses_source_files") is False
            checks.append(
                self._passed(
                    area,
                    "classification_gateway_isolation",
                    "Gateway de consumo sin acceso a documentos originales",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "classification_gateway_isolation", str(exc)))

        return checks

    def _check_extensibility(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            from zovrake_motor.comparative_tables.comparative_model_builder.engine import (
                ComparativeModelBuilderEngine,
            )
            from zovrake_motor.comparative_tables.comparative_quality_framework.engine import (
                ComparativeQualityFrameworkCore,
            )
            from zovrake_motor.comparative_tables.comparative_structure_engine.engine import (
                ComparativeStructureBuilderEngine,
            )
            from zovrake_motor.comparative_tables.comparative_validation_framework.engine import (
                ComparativeValidationFrameworkCore,
            )
            from zovrake_motor.comparative_tables.dynamic_column_builder.engine import (
                DynamicColumnBuilderEngine,
            )
            from zovrake_motor.comparative_tables.dynamic_row_builder.engine import (
                DynamicRowBuilderEngine,
            )
            from zovrake_motor.comparative_tables.group_integrity_engine.engine import (
                GroupIntegrityEngineCore,
            )
            from zovrake_motor.comparative_tables.provider_organization_engine.engine import (
                ProviderOrganizationEngineCore,
            )
            from zovrake_motor.comparative_tables.traceability_metadata_engine.engine import (
                TraceabilityMetadataEngineCore,
            )

            engines = (
                ComparativeStructureBuilderEngine(),
                DynamicColumnBuilderEngine(),
                DynamicRowBuilderEngine(),
                ProviderOrganizationEngineCore(),
                GroupIntegrityEngineCore(),
                TraceabilityMetadataEngineCore(),
                ComparativeModelBuilderEngine(),
                ComparativeValidationFrameworkCore(),
                ComparativeQualityFrameworkCore(),
            )
            for engine in engines:
                engine.initialize()
                assert hasattr(engine, "registry")
                assert hasattr(engine.registry, "register") or hasattr(engine, "extend")
            checks.append(
                self._passed(area, "extensibility", "Registros extensibles sin modificar el núcleo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "extensibility", str(exc)))

        return checks

    def _check_definitive_model_consistency(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            service = ComparativeTablesService()
            service.initialize()
            result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
            assert result.comparative_model_build_passed
            assert result.validation_passed
            assert result.quality_audit_passed
            assert result.pm7_input_contract_prepared
            checks.append(
                self._passed(
                    area,
                    "definitive_model_consistency",
                    "Modelo Comparativo Definitivo consistente y preparado para PM7",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "definitive_model_consistency", str(exc)))

        return checks

    def _check_governance_and_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPARATIVE_TABLES_MODULE

        try:
            assert len(FROZEN_FUNCTIONAL_COMPONENTS) == 9
            assert OUTPUT_CONTRACT_NAME == PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME
            assert PM6_DEFINITIVE_CATALOG_REQUIRED_FIELDS
            assert PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS
            checks.append(
                self._passed(
                    area,
                    "governance_contract",
                    "Gobierno arquitectónico y contrato de salida PM6 declarados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "governance_contract", str(exc)))

        try:
            service = ComparativeTablesService()
            service.initialize()
            result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
            assert result.module_certification_prepared
            checks.append(
                self._passed(
                    area,
                    "module_certification_prepared",
                    "Módulo certificado y preparado para cierre oficial (4.12)",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_certification_prepared", str(exc)))

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
