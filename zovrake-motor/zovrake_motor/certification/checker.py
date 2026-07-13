"""
Certificador arquitectónico del núcleo del Motor Inteligente.

Evalúa la arquitectura construida en las Implementaciones 1.1–1.9
sin modificar su comportamiento.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor import __version__
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck, CertificationReport
from zovrake_motor.certification.stack import build_certified_stack
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import BASE_MODULES, PLANNED_MODULES, MotorCoordinator
from zovrake_motor.events import EventManager, EventType, MotorEvent
from zovrake_motor.processing import InternalPipeline, PipelineStageType
from zovrake_motor.states import MotorState, StateManager

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

BASE_SERVICES = {
    "reception": "zovrake_motor.reception.service",
    "documents": "zovrake_motor.documents.service",
    "context": "zovrake_motor.context.service",
    "states": "zovrake_motor.states.service",
    "events": "zovrake_motor.events.service",
    "communication": "zovrake_motor.communication.service",
}

PM4_FUTURE_MODULES = (
    "comprehension",
    "classification",
    "comparative_tables",
    "intelligent_analysis",
)

PM4_CONFIG_CATEGORIES = ("ocr", "ai", "storage")


class CoreCertificationChecker:
    """Ejecuta la certificación integral del Prompt Maestro 3."""

    def run(self) -> CertificationReport:
        report = CertificationReport(motor_version=__version__)
        report.checks.extend(self._check_initialization())
        report.checks.extend(self._check_architecture())
        report.checks.extend(self._check_coordinator())
        report.checks.extend(self._check_modules())
        report.checks.extend(self._check_pipeline())
        report.checks.extend(self._check_state_management())
        report.checks.extend(self._check_event_management())
        report.checks.extend(self._check_configuration())
        report.checks.extend(self._check_prompt_maestro_4_readiness())
        report.checks.extend(self._check_comprehension_module())
        report.checks.extend(self._check_prompt_maestro_5_readiness())
        report.checks.extend(self._check_classification_module())
        report.checks.extend(self._check_classification_module_closure())
        report.checks.extend(self._check_prompt_maestro_6_readiness())
        report.checks.extend(self._check_comparative_tables_module())
        report.checks.extend(self._check_prompt_maestro_7_readiness())
        report.checks.extend(self._check_intelligent_analysis_module())
        report.checks.extend(self._check_intelligent_analysis_module_closure())
        report.checks.extend(self._check_prompt_maestro_8_readiness())
        report.checks.extend(self._check_enterprise_integration_e2e())
        report.checks.extend(self._check_enterprise_integration_platform())
        report.checks.extend(self._check_enterprise_integration_closure())
        report.checks.extend(self._check_integration_api_e2e())
        return report

    def _check_integration_api_e2e(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.integration_api_e2e_checker import (
            IntegrationApiE2ECertificationChecker,
        )

        return IntegrationApiE2ECertificationChecker().run()

    def _check_enterprise_integration_closure(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.enterprise_integration_closure_checker import (
            EnterpriseIntegrationModuleClosureChecker,
        )

        return EnterpriseIntegrationModuleClosureChecker().run()

    def _check_enterprise_integration_platform(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.enterprise_integration_platform_checker import (
            EnterpriseIntegrationPlatformCertificationChecker,
        )

        return EnterpriseIntegrationPlatformCertificationChecker().run()

    def _check_enterprise_integration_e2e(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.enterprise_integration_e2e_checker import (
            EnterpriseIntegrationE2ECertificationChecker,
        )

        return EnterpriseIntegrationE2ECertificationChecker().run()

    def _check_prompt_maestro_8_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PROMPT_MAESTRO_8

        try:
            from zovrake_motor.enterprise_integration import EnterpriseIntegrationService

            service = EnterpriseIntegrationService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 17
            assert service.component_registry.ready_count() == 17
            checks.append(
                self._passed(
                    area,
                    "enterprise_integration_architecture",
                    "Arquitectura base de Integración Empresarial disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "enterprise_integration_architecture", str(exc)))

        try:
            from zovrake_motor.enterprise_integration.governance import (
                IMPLEMENTATION,
                PROMPT_MAESTRO_8_STATUS,
                governance_snapshot,
            )

            snapshot = governance_snapshot()
            assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
            assert IMPLEMENTATION == "8.12"
            assert snapshot["prepared_functional_components_count"] == 17
            checks.append(
                self._passed(
                    area,
                    "enterprise_integration_governance",
                    "Gobierno arquitectonico PM8 cerrado en Implementacion 8.12",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "enterprise_integration_governance", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            enterprise_integration = provider.enterprise_integration()
            assert hasattr(enterprise_integration, "erp_communication_gateway")
            assert hasattr(enterprise_integration, "async_processing_queue_manager")
            assert hasattr(enterprise_integration, "pipeline_integration_orchestrator")
            checks.append(
                self._passed(
                    area,
                    "enterprise_integration_config",
                    "Configuración central de Integración Empresarial disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "enterprise_integration_config", str(exc)))

        try:
            from zovrake_motor.coordinator.pipeline import CoordinationPipeline

            assert "enterprise_integration" in CoordinationPipeline.INTEGRATION_MODULES
            checks.append(
                self._passed(
                    area,
                    "integration_module_registered",
                    "Módulo de integración registrado en el Coordinator",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "integration_module_registered", str(exc)))

        return checks

    def _check_intelligent_analysis_module_closure(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.intelligent_analysis_closure_checker import (
            IntelligentAnalysisModuleClosureChecker,
        )

        return IntelligentAnalysisModuleClosureChecker().run()

    def _check_intelligent_analysis_module(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.intelligent_analysis_checker import (
            IntelligentAnalysisModuleCertificationChecker,
        )

        return IntelligentAnalysisModuleCertificationChecker().run()

    def _check_comparative_tables_module(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.comparative_tables_checker import (
            ComparativeTablesModuleCertificationChecker,
        )

        return ComparativeTablesModuleCertificationChecker().run()

    def _check_classification_module_closure(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.classification_closure_checker import ClassificationModuleClosureChecker

        return ClassificationModuleClosureChecker().run()

    def _check_classification_module(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.classification_checker import ClassificationModuleCertificationChecker

        return ClassificationModuleCertificationChecker().run()

    def _check_comprehension_module(self) -> list[CertificationCheck]:
        from zovrake_motor.certification.comprehension_checker import ComprehensionModuleCertificationChecker

        return ComprehensionModuleCertificationChecker().run()

    def _check_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INITIALIZATION

        try:
            config = ConfigurationProvider.default()
            checks.append(self._passed(area, "configuration_provider", "ConfigurationProvider disponible"))
        except Exception as exc:
            checks.append(self._failed(area, "configuration_provider", str(exc)))
            return checks

        try:
            state_manager = StateManager()
            checks.append(self._passed(area, "state_manager", "StateManager disponible"))
        except Exception as exc:
            checks.append(self._failed(area, "state_manager", str(exc)))

        try:
            event_manager = EventManager()
            checks.append(self._passed(area, "event_manager", "EventManager disponible"))
        except Exception as exc:
            checks.append(self._failed(area, "event_manager", str(exc)))

        try:
            pipeline = InternalPipeline()
            checks.append(self._passed(area, "internal_pipeline", "InternalPipeline construido"))
            assert len(pipeline.stages) == 7
        except Exception as exc:
            checks.append(self._failed(area, "internal_pipeline", str(exc)))

        try:
            coordinator, _, _, _ = build_certified_stack()
            checks.append(self._passed(area, "coordinator_ready", "Coordinator preparado"))
            assert coordinator.is_ready()
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_ready", str(exc)))

        try:
            coordinator, _, _, _ = build_certified_stack()
            result = coordinator.coordinate(metadata={"codigo_req": "CERT-001"})
            assert result.success
            checks.append(self._passed(area, "full_cycle", "Ciclo de coordinación exitoso"))
        except Exception as exc:
            checks.append(self._failed(area, "full_cycle", str(exc)))

        return checks

    def _check_architecture(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.ARCHITECTURE

        try:
            import zovrake_motor.coordinator.coordinator
            import zovrake_motor.coordinator.registry
            import zovrake_motor.coordinator.module_administrator
            import zovrake_motor.processing.controller
            import zovrake_motor.states.manager
            import zovrake_motor.events.manager
            import zovrake_motor.config.provider
            checks.append(self._passed(area, "core_imports", "Componentes principales importables"))
        except Exception as exc:
            checks.append(self._failed(area, "core_imports", str(exc)))

        try:
            independent = True
            for name in BASE_MODULES:
                package = importlib.import_module(f"zovrake_motor.{name}")
                for _finder, modname, _ispkg in pkgutil.walk_packages(
                    package.__path__, prefix=package.__name__ + "."
                ):
                    module = importlib.import_module(modname)
                    source = getattr(module, "__file__", "") or ""
                    if not source.endswith(".py"):
                        continue
                    with open(source, encoding="utf-8") as fh:
                        content = fh.read()
                    for other in BASE_MODULES:
                        if other == name:
                            continue
                        if f"zovrake_motor.{other}" in content:
                            independent = False
                            break
            assert independent
            checks.append(self._passed(area, "module_independence", "Módulos base independientes"))
        except Exception as exc:
            checks.append(self._failed(area, "module_independence", str(exc)))

        try:
            coordinator_source = (
                PACKAGE_ROOT / "coordinator" / "coordinator.py"
            ).read_text(encoding="utf-8")
            forbidden = ("zovrake_web", "zovrake-web", "openai", "tensorflow", "sklearn")
            for term in forbidden:
                assert term not in coordinator_source.lower()
            checks.append(self._passed(area, "erp_decoupling", "Coordinator desacoplado del ERP"))
        except Exception as exc:
            checks.append(self._failed(area, "erp_decoupling", str(exc)))

        try:
            names = [p.name for p in PACKAGE_ROOT.iterdir() if p.is_dir() and not p.name.startswith("_")]
            assert len(names) == len(set(names))
            checks.append(self._passed(area, "no_duplicate_modules", "Sin módulos duplicados"))
        except Exception as exc:
            checks.append(self._failed(area, "no_duplicate_modules", str(exc)))

        return checks

    def _check_coordinator(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COORDINATOR

        try:
            coordinator, _, _, _ = build_certified_stack()
            assert coordinator.MODULE_NAME == "MotorCoordinator"
            assert coordinator.validate_base_modules()
            checks.append(self._passed(area, "single_coordinator", "Coordinator como único núcleo"))
        except Exception as exc:
            checks.append(self._failed(area, "single_coordinator", str(exc)))

        try:
            source = (PACKAGE_ROOT / "coordinator" / "coordinator.py").read_text(encoding="utf-8")
            business_terms = ("classify", "ocr", "extract_text", "compare_prices", "openai")
            found = [term for term in business_terms if term in source.lower()]
            assert not found
            checks.append(self._passed(area, "no_business_logic", "Coordinator sin lógica de negocio"))
        except Exception as exc:
            checks.append(self._failed(area, "no_business_logic", str(exc)))

        try:
            coordinator, _, state_manager, event_manager = build_certified_stack()
            assert coordinator.state_manager is state_manager
            assert coordinator.event_manager is event_manager
            checks.append(self._passed(area, "composition", "Coordinator usa composición e inyección"))
        except Exception as exc:
            checks.append(self._failed(area, "composition", str(exc)))

        return checks

    def _check_modules(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.MODULES

        for module_name, service_path in BASE_SERVICES.items():
            try:
                service_module = importlib.import_module(service_path)
                service_cls = [
                    obj for name, obj in vars(service_module).items()
                    if isinstance(obj, type) and name.endswith("Service")
                ][0]
                service = service_cls()
                assert not service.is_available()
                service.initialize()
                assert service.is_available()
                assert service.module_name == module_name
                checks.append(self._passed(area, f"module_{module_name}", f"Módulo {module_name} inicializable"))
            except Exception as exc:
                checks.append(self._failed(area, f"module_{module_name}", str(exc)))

        try:
            assert len(BASE_MODULES) == 6
            for name in BASE_MODULES:
                assert name in PLANNED_MODULES
            checks.append(self._passed(area, "base_module_registry", "Registro de módulos base consistente"))
        except Exception as exc:
            checks.append(self._failed(area, "base_module_registry", str(exc)))

        return checks

    def _check_pipeline(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PIPELINE

        try:
            pipeline = InternalPipeline()
            stages = pipeline.ordered_stage_types()
            expected = (
                PipelineStageType.RECEPCION,
                PipelineStageType.VALIDACION,
                PipelineStageType.PREPARACION,
                PipelineStageType.COORDINACION,
                PipelineStageType.PROCESAMIENTO,
                PipelineStageType.RESPUESTA,
                PipelineStageType.FINALIZACION,
            )
            assert stages == expected
            checks.append(self._passed(area, "stage_order", "Orden de etapas consistente"))
        except Exception as exc:
            checks.append(self._failed(area, "stage_order", str(exc)))

        try:
            coordinator, _, _, _ = build_certified_stack()
            process_id = uuid4()
            result = coordinator.run_internal_pipeline(process_id)
            assert result.success
            assert len(result.stages_completed) == 7
            checks.append(self._passed(area, "coordinator_control", "Coordinator controla el Pipeline"))
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_control", str(exc)))

        try:
            source = (PACKAGE_ROOT / "processing" / "controller.py").read_text(encoding="utf-8")
            assert "ocr" not in source.lower()
            assert "classify" not in source.lower()
            checks.append(self._passed(area, "no_processing_logic", "Pipeline sin procesamiento real"))
        except Exception as exc:
            checks.append(self._failed(area, "no_processing_logic", str(exc)))

        return checks

    def _check_state_management(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.STATE_MANAGEMENT

        try:
            assert len(MotorState.official_states()) == 11
            checks.append(self._passed(area, "official_states", "11 estados oficiales definidos"))
        except Exception as exc:
            checks.append(self._failed(area, "official_states", str(exc)))

        try:
            manager = StateManager()
            id_a, id_b = uuid4(), uuid4()
            manager.create_process(id_a, "A")
            manager.create_process(id_b, "B")
            manager.update_state(id_a, MotorState.VALIDANDO_INFORMACION, "test")
            assert manager.get_process(id_a).current_state == MotorState.VALIDANDO_INFORMACION
            assert manager.get_process(id_b).current_state == MotorState.INICIALIZADO
            checks.append(self._passed(area, "independent_states", "Estados independientes por proceso"))
        except Exception as exc:
            checks.append(self._failed(area, "independent_states", str(exc)))

        try:
            coordinator, _, state_manager, _ = build_certified_stack()
            process_id = uuid4()
            coordinator.create_process_state(process_id, "CERT-STATE")
            assert state_manager.get_process(process_id) is not None
            checks.append(self._passed(area, "coordinator_lifecycle", "Coordinator administra ciclo de vida"))
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_lifecycle", str(exc)))

        return checks

    def _check_event_management(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.EVENT_MANAGEMENT

        try:
            event = MotorEvent.create(
                process_id=uuid4(),
                module="test",
                event_type=EventType.SYSTEM,
                message="test",
                associated_state="inicializado",
                metadata={"key": "value"},
            )
            data = event.to_dict()
            required = {
                "event_id", "process_id", "module", "event_type",
                "occurred_at", "associated_state", "message", "metadata",
            }
            assert required.issubset(data.keys())
            checks.append(self._passed(area, "uniform_model", "Modelo de evento uniforme"))
        except Exception as exc:
            checks.append(self._failed(area, "uniform_model", str(exc)))

        try:
            manager = EventManager()
            id_a, id_b = uuid4(), uuid4()
            manager.create_and_register(
                process_id=id_a, module="a", event_type=EventType.SYSTEM, message="A"
            )
            manager.create_and_register(
                process_id=id_b, module="b", event_type=EventType.SYSTEM, message="B"
            )
            assert len(manager.get_process_history(id_a)) == 1
            assert len(manager.get_process_history(id_b)) == 1
            checks.append(self._passed(area, "independent_history", "Historial independiente por solicitud"))
        except Exception as exc:
            checks.append(self._failed(area, "independent_history", str(exc)))

        try:
            coordinator, _, _, event_manager = build_certified_stack()
            before = event_manager.count()
            coordinator.register_coordination_event(
                process_id=uuid4(),
                message="certificación",
            )
            assert event_manager.count() == before + 1
            checks.append(self._passed(area, "coordinator_registration", "Coordinator coordina registro"))
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_registration", str(exc)))

        return checks

    def _check_configuration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CONFIGURATION

        try:
            provider_a = ConfigurationProvider.default()
            provider_b = ConfigurationProvider.default()
            assert provider_a.service_name() == provider_b.service_name()
            checks.append(self._passed(area, "single_source", "Fuente única de configuración"))
        except Exception as exc:
            checks.append(self._failed(area, "single_source", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            snapshot = provider.snapshot()
            for key in ("general", "paths", "behavior", "communication", "processing",
                        "security", "events", "performance", "future"):
                assert key in snapshot
            checks.append(self._passed(area, "categories", "Categorías de configuración disponibles"))
        except Exception as exc:
            checks.append(self._failed(area, "categories", str(exc)))

        try:
            for module_name in BASE_MODULES:
                service_path = BASE_SERVICES[module_name]
                source = importlib.import_module(service_path).__file__
                assert source is not None
                content = Path(source).read_text(encoding="utf-8")
                assert "service_version" not in content
            checks.append(self._passed(area, "no_duplicate_config", "Sin configuraciones duplicadas en módulos"))
        except Exception as exc:
            checks.append(self._failed(area, "no_duplicate_config", str(exc)))

        return checks

    def _check_prompt_maestro_4_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PROMPT_MAESTRO_4

        try:
            for module_name in PM4_FUTURE_MODULES:
                path = PACKAGE_ROOT / module_name
                assert path.is_dir(), f"Falta módulo futuro: {module_name}"
                assert (path / "__init__.py").is_file()
            checks.append(self._passed(area, "future_modules", "Módulos futuros reservados"))
        except Exception as exc:
            checks.append(self._failed(area, "future_modules", str(exc)))

        try:
            assert "comprehension" in PLANNED_MODULES
            coordinator, _, _, _ = build_certified_stack()
            snapshot = coordinator.get_pipeline_snapshot()
            comprehension = next(
                (s for s in snapshot if s.get("module_name") == "comprehension"),
                None,
            )
            assert comprehension is not None
            assert comprehension["registered"] is False
            checks.append(self._passed(area, "pipeline_extension", "Pipeline preparado para extensión"))
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_extension", str(exc)))

        try:
            from zovrake_motor.comprehension import ComprehensionService

            service = ComprehensionService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 11
            checks.append(
                self._passed(
                    area,
                    "comprehension_architecture",
                    "Arquitectura base de Comprensión Documental disponible",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "comprehension_architecture", str(exc)))

        try:
            from zovrake_motor.comprehension.adapters import DocumentAdapterFramework

            framework = DocumentAdapterFramework()
            framework.initialize()
            assert framework.is_ready()
            assert framework.registry.count() == 4
            checks.append(
                self._passed(
                    area,
                    "adapter_framework",
                    "Document Adapter Framework disponible con 4 adaptadores",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "adapter_framework", str(exc)))

        try:
            from zovrake_motor.comprehension.validation import DocumentValidationFramework

            framework = DocumentValidationFramework()
            framework.initialize()
            assert framework.is_ready()
            assert framework.registry.count() == 8
            checks.append(
                self._passed(
                    area,
                    "validation_framework",
                    "Document Validation Framework disponible con 8 reglas",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "validation_framework", str(exc)))

        try:
            from zovrake_motor.comprehension.recognition import DocumentRecognitionEngine

            engine = DocumentRecognitionEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() >= 3
            checks.append(
                self._passed(
                    area,
                    "recognition_engine",
                    "Document Recognition Engine disponible con estrategias registradas",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "recognition_engine", str(exc)))

        try:
            from zovrake_motor.comprehension.extraction import ContentExtractionEngine

            engine = ContentExtractionEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 8
            checks.append(
                self._passed(
                    area,
                    "extraction_engine",
                    "Content Extraction Engine disponible con 8 extractores",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "extraction_engine", str(exc)))

        try:
            from zovrake_motor.comprehension.canonical import CanonicalRepresentationEngine

            engine = CanonicalRepresentationEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 7
            checks.append(
                self._passed(
                    area,
                    "canonical_engine",
                    "Canonical Representation Engine disponible con 7 transformadores",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "canonical_engine", str(exc)))

        try:
            from zovrake_motor.comprehension.internal_model import InternalDocumentModelBuilder

            engine = InternalDocumentModelBuilder()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 10
            checks.append(
                self._passed(
                    area,
                    "internal_model_builder",
                    "Internal Document Model Builder disponible con 10 constructores",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "internal_model_builder", str(exc)))

        try:
            from zovrake_motor.comprehension.knowledge_index import DocumentKnowledgeIndex

            engine = DocumentKnowledgeIndex()
            engine.initialize()
            assert engine.is_ready()
            assert engine.store.count() == 0
            checks.append(
                self._passed(
                    area,
                    "knowledge_index",
                    "Document Knowledge Index disponible con almacén en memoria",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "knowledge_index", str(exc)))

        try:
            from zovrake_motor.comprehension.context_integration import ContextIntegrationEngine

            engine = ContextIntegrationEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.store.count() == 0
            checks.append(
                self._passed(
                    area,
                    "context_integration",
                    "Context Integration Engine disponible con almacén de asociaciones",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "context_integration", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            comprehension = provider.comprehension()
            assert hasattr(comprehension, "enabled")
            assert hasattr(comprehension, "max_documents_per_process")
            assert hasattr(comprehension, "adapters")
            assert hasattr(comprehension.adapters, "pdf_enabled")
            assert hasattr(comprehension, "validation")
            assert hasattr(comprehension.validation, "max_file_size_bytes")
            assert hasattr(comprehension, "recognition")
            assert hasattr(comprehension.recognition, "min_confidence_threshold")
            assert hasattr(comprehension, "extraction")
            assert hasattr(comprehension.extraction, "preserve_original")
            assert hasattr(comprehension, "canonical")
            assert hasattr(comprehension.canonical, "preserve_immutability")
            assert hasattr(comprehension, "internal_model")
            assert hasattr(comprehension.internal_model, "preserve_immutability")
            assert hasattr(comprehension, "knowledge_index")
            assert hasattr(comprehension.knowledge_index, "prevent_duplicates")
            assert hasattr(comprehension, "context_integration")
            assert hasattr(comprehension.context_integration, "preserve_document_immutability")
            checks.append(
                self._passed(
                    area,
                    "comprehension_config",
                    "Configuración central de Comprensión Documental disponible",
                )
            )
        except Exception as exc:
            checks.append(self._failed(area, "comprehension_config", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            future = provider.future()
            assert hasattr(future, "ocr")
            assert hasattr(future, "ai")
            assert hasattr(future, "storage")
            for attr in PM4_CONFIG_CATEGORIES:
                assert hasattr(future, attr)
            checks.append(self._passed(area, "config_extension", "Configuración preparada para PM4"))
        except Exception as exc:
            checks.append(self._failed(area, "config_extension", str(exc)))

        try:
            coordinator, _, _, _ = build_certified_stack()
            assert coordinator.get_module("comprehension") is None
            checks.append(self._passed(area, "core_unchanged", "Núcleo sin dependencias de PM4"))
        except Exception as exc:
            checks.append(self._failed(area, "core_unchanged", str(exc)))

        return checks

    def _check_prompt_maestro_5_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PROMPT_MAESTRO_5

        try:
            from zovrake_motor.classification import ClassificationService

            service = ClassificationService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 13
            assert service.component_registry.ready_count() == 10
            checks.append(
                self._passed(
                    area,
                    "classification_architecture",
                    "Arquitectura base de Clasificación Inteligente disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "classification_architecture", str(exc)))

        try:
            from zovrake_motor.classification.concept_analysis import ConceptAnalysisEngine

            engine = ConceptAnalysisEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 5
            checks.append(
                self._passed(
                    area,
                    "concept_analysis_engine",
                    "Concept Analysis Engine disponible con 5 detectores",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "concept_analysis_engine", str(exc)))

        try:
            from zovrake_motor.classification.classification_quality import ClassificationQualityFrameworkEngine

            engine = ClassificationQualityFrameworkEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 5
            checks.append(
                self._passed(
                    area,
                    "classification_quality_framework",
                    "Classification Quality Framework disponible con 5 validadores",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "classification_quality_framework", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            classification = provider.classification()
            assert hasattr(classification, "concept_analysis")
            assert hasattr(classification, "comparative_domain_model_builder")
            assert hasattr(classification, "classification_quality_framework")
            checks.append(
                self._passed(
                    area,
                    "classification_config",
                    "Configuración central de Clasificación Inteligente disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "classification_config", str(exc)))

        try:
            coordinator, _, _, _ = build_certified_stack()
            snapshot = coordinator.get_pipeline_snapshot()
            classification = next(
                (s for s in snapshot if s.get("module_name") == "classification"),
                None,
            )
            assert classification is not None
            checks.append(
                self._passed(area, "pipeline_extension_pm6", "Pipeline preparado para Prompt Maestro 6"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_extension_pm6", str(exc)))

        return checks

    def _check_prompt_maestro_6_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PROMPT_MAESTRO_6

        try:
            from zovrake_motor.comparative_tables import ComparativeTablesService

            service = ComparativeTablesService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 10
            assert service.component_registry.ready_count() == 10
            checks.append(
                self._passed(
                    area,
                    "comparative_tables_architecture",
                    "Arquitectura base de Cuadros Comparativos disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_tables_architecture", str(exc)))

        try:
            from zovrake_motor.comparative_tables.comparative_structure_engine import (
                ComparativeStructureBuilderEngine,
            )

            engine = ComparativeStructureBuilderEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 1
            checks.append(
                self._passed(
                    area,
                    "comparative_structure_engine",
                    "Comparative Structure Engine disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_structure_engine", str(exc)))

        try:
            from zovrake_motor.comparative_tables.comparative_quality_framework import (
                ComparativeQualityFrameworkCore,
            )

            engine = ComparativeQualityFrameworkCore()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 6
            checks.append(
                self._passed(
                    area,
                    "comparative_quality_framework",
                    "Comparative Quality Framework disponible con 6 auditores",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_quality_framework", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            comparative_tables = provider.comparative_tables()
            assert hasattr(comparative_tables, "comparative_structure_engine")
            assert hasattr(comparative_tables, "comparative_model_builder")
            assert hasattr(comparative_tables, "comparative_quality_framework")
            checks.append(
                self._passed(
                    area,
                    "comparative_tables_config",
                    "Configuración central de Cuadros Comparativos disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_tables_config", str(exc)))

        return checks

    def _check_prompt_maestro_7_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.PROMPT_MAESTRO_7

        try:
            from zovrake_motor.intelligent_analysis import IntelligentAnalysisService

            service = IntelligentAnalysisService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 11
            assert service.component_registry.ready_count() == 11
            checks.append(
                self._passed(
                    area,
                    "intelligent_analysis_architecture",
                    "Arquitectura base de Razonamiento Inteligente disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "intelligent_analysis_architecture", str(exc)))

        try:
            from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
                EvidenceAnalysisBuilderEngine,
            )

            engine = EvidenceAnalysisBuilderEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 1
            checks.append(
                self._passed(
                    area,
                    "evidence_analysis_engine",
                    "Evidence Analysis Engine disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "evidence_analysis_engine", str(exc)))

        try:
            from zovrake_motor.intelligent_analysis.reasoning_result_builder import (
                ReasoningResultBuilderEngine,
            )

            engine = ReasoningResultBuilderEngine()
            engine.initialize()
            assert engine.is_ready()
            assert engine.registry.count() == 1
            checks.append(
                self._passed(
                    area,
                    "reasoning_result_builder",
                    "Reasoning Result Builder disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "reasoning_result_builder", str(exc)))

        try:
            provider = ConfigurationProvider.default()
            intelligent_analysis = provider.intelligent_analysis()
            assert hasattr(intelligent_analysis, "evidence_analysis_engine")
            assert hasattr(intelligent_analysis, "reasoning_result_builder")
            checks.append(
                self._passed(
                    area,
                    "intelligent_analysis_config",
                    "Configuración central de Razonamiento Inteligente disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "intelligent_analysis_config", str(exc)))

        return checks

    def _passed(self, area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.PASSED,
            message=message,
        )

    def _failed(self, area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.FAILED,
            message=message,
        )
