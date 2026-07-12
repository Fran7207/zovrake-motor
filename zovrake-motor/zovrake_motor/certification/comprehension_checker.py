"""
Certificador integral del Módulo de Comprensión Documental.

Implementación 2.10 — Cierre oficial del Prompt Maestro 4.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.comprehension.service import ComprehensionService
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.certification.comprehension_pipeline import run_full_comprehension_pipeline
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_COMPREHENSION_IMPORTS = (
    "zovrake_motor.reception",
    "zovrake_motor.documents",
    "zovrake_motor.context",
    "zovrake_motor.communication",
)

PIPELINE_ENGINE_COMPONENTS = (
    ("document_validator", "Document Validation Framework"),
    ("document_adapters", "Document Adapter Framework"),
    ("format_identifier", "Document Recognition Engine"),
    ("extractors", "Content Extraction Engine"),
    ("normalizer", "Canonical Representation Engine"),
    ("internal_model_builder", "Internal Document Model Builder"),
    ("document_index", "Document Knowledge Index"),
    ("context_manager", "Context Integration Engine"),
)

EXPECTED_PIPELINE_PHASES = (
    ComprehensionPhase.PREPARACION,
    ComprehensionPhase.VALIDACION,
    ComprehensionPhase.ADAPTACION,
    ComprehensionPhase.IDENTIFICACION,
    ComprehensionPhase.EXTRACCION,
    ComprehensionPhase.NORMALIZACION,
    ComprehensionPhase.MODELADO,
    ComprehensionPhase.INDEXACION,
    ComprehensionPhase.INTEGRACION_CONTEXTO,
    ComprehensionPhase.FINALIZACION,
)


class ComprehensionModuleCertificationChecker:
    """Certifica el Módulo de Comprensión Documental como sistema integrado."""

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
        return checks

    def _check_module_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            service = ComprehensionService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 11
            checks.append(
                self._passed(area, "module_initialization", "Módulo inicializado con 11 componentes"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_initialization", str(exc)))
            return checks

        try:
            ready = service.component_registry.ready_count()
            assert ready == 9
            checks.append(
                self._passed(area, "components_ready", f"9 componentes operativos del pipeline ({ready})"),
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
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            phases = DocumentComprehensionPipeline.ordered_phases()
            assert phases == EXPECTED_PIPELINE_PHASES
            checks.append(
                self._passed(area, "pipeline_phases", "10 etapas del Pipeline documental certificadas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_phases", str(exc)))

        try:
            service = ComprehensionService()
            service.initialize()
            snapshot = DocumentComprehensionPipeline.build_snapshot(service.component_registry)
            engine_stages = [s for s in snapshot if s.get("component_name")]
            assert len(engine_stages) == 8
            checks.append(
                self._passed(area, "pipeline_stages_registered", "8 etapas con componente registrado"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_stages_registered", str(exc)))

        return checks

    def _check_full_pipeline_execution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            service = ComprehensionService()
            service.initialize()
            process_id = uuid4()
            result = run_full_comprehension_pipeline(
                service,
                process_id=process_id,
                document_id="DOC-FULL-CERT",
            )
            assert result.complete
            assert result.stages_executed == 7
            checks.append(
                self._passed(
                    area,
                    "full_pipeline_execution",
                    "Pipeline completo ejecutado sin interrupciones (7 etapas funcionales)",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "full_pipeline_execution", str(exc)))

        return checks

    def _check_traceability_and_immutability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            service = ComprehensionService()
            service.initialize()
            process_id = uuid4()
            result = run_full_comprehension_pipeline(service, process_id=process_id)
            assert result.traceability_intact
            checks.append(
                self._passed(area, "traceability_chain", "Cadena de trazabilidad intacta en todo el flujo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "traceability_chain", str(exc)))

        try:
            service = ComprehensionService()
            service.initialize()
            process_id = uuid4()
            result = run_full_comprehension_pipeline(service, process_id=process_id)
            assert result.document_unmodified
            checks.append(
                self._passed(area, "document_immutability", "Información documental no modificada por el contexto"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "document_immutability", str(exc)))

        try:
            service = ComprehensionService()
            service.initialize()
            process_id = uuid4()
            result = run_full_comprehension_pipeline(service, process_id=process_id)
            assert result.context_associated
            checks.append(
                self._passed(area, "context_association", "Contexto correctamente asociado al índice documental"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "context_association", str(exc)))

        return checks

    def _check_coordinator_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            config = ConfigurationProvider.default()
            coordinator = MotorCoordinator(config_provider=config)
            service = ComprehensionService(config_provider=config)
            service.initialize()
            coordinator.register_module(service)
            coordinator.initialize_modules()
            coordinator.prepare_modules()
            assert coordinator.is_module_available("comprehension")
            checks.append(
                self._passed(area, "coordinator_registration", "Coordinator administra el módulo de Comprensión"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_registration", str(exc)))

        return checks

    def _check_state_and_event_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = ComprehensionService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            service.initialize()
            process_id = uuid4()
            run_full_comprehension_pipeline(service, process_id=process_id)

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
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            provider = ConfigurationProvider.default()
            comprehension = provider.comprehension()
            required = (
                "adapters",
                "validation",
                "recognition",
                "extraction",
                "canonical",
                "internal_model",
                "knowledge_index",
                "context_integration",
            )
            for attr in required:
                assert hasattr(comprehension, attr)
            checks.append(
                self._passed(area, "central_configuration", "Configuración central unificada para todos los motores"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "central_configuration", str(exc)))

        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            package = importlib.import_module("zovrake_motor.comprehension")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_COMPREHENSION_IMPORTS:
                    assert forbidden not in content, f"{modname} importa {forbidden}"
            checks.append(
                self._passed(area, "module_isolation", "Sin dependencias directas entre módulos del Motor"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_isolation", str(exc)))

        return checks

    def _check_extensibility(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.COMPREHENSION_MODULE

        try:
            from zovrake_motor.comprehension.adapters import DocumentAdapterFramework
            from zovrake_motor.comprehension.validation import DocumentValidationFramework
            from zovrake_motor.comprehension.recognition import DocumentRecognitionEngine
            from zovrake_motor.comprehension.extraction import ContentExtractionEngine
            from zovrake_motor.comprehension.canonical import CanonicalRepresentationEngine
            from zovrake_motor.comprehension.internal_model import InternalDocumentModelBuilder

            engines = (
                DocumentAdapterFramework(),
                DocumentValidationFramework(),
                DocumentRecognitionEngine(),
                ContentExtractionEngine(),
                CanonicalRepresentationEngine(),
                InternalDocumentModelBuilder(),
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
