"""
Certificador integral del Módulo de Clasificación Inteligente.

Implementación 3.11 — Cierre oficial del Prompt Maestro 5.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.service import ClassificationService
from zovrake_motor.certification.classification_pipeline import run_full_classification_pipeline
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_CLASSIFICATION_IMPORTS = (
    "zovrake_motor.reception",
    "zovrake_motor.documents",
    "zovrake_motor.context",
    "zovrake_motor.communication",
    "zovrake_motor.comprehension",
)

PIPELINE_ENGINE_COMPONENTS = (
    ("concept_analysis_engine", "Concept Analysis Engine"),
    ("material_classification_engine", "Material Classification Engine"),
    ("service_classification_engine", "Service Classification Engine"),
    ("concept_normalization_engine", "Concept Normalization Engine"),
    ("equivalence_detection_engine", "Equivalence Detection Engine"),
    ("comparable_group_builder", "Comparable Group Builder"),
    ("context_association_engine", "Context Association Engine"),
    ("comparative_domain_model_builder", "Comparative Domain Model Builder"),
    ("classification_quality_framework", "Classification Quality Framework"),
)

EXPECTED_PIPELINE_PHASES = (
    ClassificationPhase.PREPARACION,
    ClassificationPhase.ANALISIS_CONCEPTOS,
    ClassificationPhase.CLASIFICACION_MATERIALES,
    ClassificationPhase.CLASIFICACION_SERVICIOS,
    ClassificationPhase.NORMALIZACION_CONCEPTOS,
    ClassificationPhase.DETECCION_EQUIVALENCIAS,
    ClassificationPhase.CONSTRUCCION_GRUPOS,
    ClassificationPhase.IDENTIFICACION_GRUPOS,
    ClassificationPhase.ASOCIACION_CONTEXTO,
    ClassificationPhase.TRAZABILIDAD,
    ClassificationPhase.EVALUACION_CONFIANZA,
    ClassificationPhase.MODELO_DOMINIO,
    ClassificationPhase.VALIDACION_CALIDAD,
    ClassificationPhase.FINALIZACION,
)


class ClassificationModuleCertificationChecker:
    """Certifica el Módulo de Clasificación Inteligente como sistema integrado."""

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
        checks.extend(self._check_comparative_domain_model_consistency())
        return checks

    def _check_module_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            service = ClassificationService()
            service.initialize()
            assert service.is_available()
            assert service.component_registry.count() == 13
            checks.append(
                self._passed(area, "module_initialization", "Módulo inicializado con 13 componentes"),
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
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            phases = ClassificationPipeline.ordered_phases()
            assert phases == EXPECTED_PIPELINE_PHASES
            checks.append(
                self._passed(area, "pipeline_phases", "14 etapas del Pipeline de clasificación certificadas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_phases", str(exc)))

        try:
            service = ClassificationService()
            service.initialize()
            snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
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
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            result = run_full_classification_pipeline(
                service,
                process_id=process_id,
                document_id="DOC-FULL-CLASS-CERT",
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
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            result = run_full_classification_pipeline(service, process_id=process_id)
            assert result.traceability_intact
            checks.append(
                self._passed(area, "traceability_chain", "Cadena de trazabilidad intacta en todo el flujo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "traceability_chain", str(exc)))

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            result = run_full_classification_pipeline(service, process_id=process_id)
            assert result.source_data_immutable
            checks.append(
                self._passed(area, "source_immutability", "Modelo documental interno no modificado por el flujo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "source_immutability", str(exc)))

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            result = run_full_classification_pipeline(service, process_id=process_id)
            assert result.materials_services_separated
            checks.append(
                self._passed(area, "materials_services_separation", "Materiales y servicios permanecen separados"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "materials_services_separation", str(exc)))

        return checks

    def _check_coordinator_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            config = ConfigurationProvider.default()
            coordinator = MotorCoordinator(config_provider=config)
            service = ClassificationService(config_provider=config)
            service.initialize()
            coordinator.register_module(service)
            coordinator.initialize_modules()
            coordinator.prepare_modules()
            assert coordinator.is_module_available("classification")
            checks.append(
                self._passed(area, "coordinator_registration", "Coordinator administra el módulo de Clasificación"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_registration", str(exc)))

        return checks

    def _check_state_and_event_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = ClassificationService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            service.initialize()
            process_id = uuid4()
            run_full_classification_pipeline(service, process_id=process_id)

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
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            provider = ConfigurationProvider.default()
            classification = provider.classification()
            required = (
                "concept_analysis",
                "material_classification",
                "service_classification",
                "concept_normalization",
                "equivalence_detection",
                "comparable_group_builder",
                "context_association",
                "comparative_domain_model_builder",
                "classification_quality_framework",
            )
            for attr in required:
                assert hasattr(classification, attr)
            checks.append(
                self._passed(area, "central_configuration", "Configuración central unificada para todos los motores"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "central_configuration", str(exc)))

        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            package = importlib.import_module("zovrake_motor.classification")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_CLASSIFICATION_IMPORTS:
                    assert forbidden not in content, f"{modname} importa {forbidden}"
            checks.append(
                self._passed(area, "module_isolation", "Sin dependencias directas entre módulos del Motor"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_isolation", str(exc)))

        try:
            service = ClassificationService()
            service.initialize()
            gateway_snapshot = service.comprehension_gateway.snapshot()
            assert gateway_snapshot.get("accesses_original_documents") is False
            checks.append(
                self._passed(
                    area,
                    "comprehension_gateway_isolation",
                    "Gateway de consumo sin acceso a documentos originales",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comprehension_gateway_isolation", str(exc)))

        return checks

    def _check_extensibility(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            from zovrake_motor.classification.classification_quality.engine import (
                ClassificationQualityFrameworkEngine,
            )
            from zovrake_motor.classification.comparable_group_builder.engine import ComparableGroupBuilderEngine
            from zovrake_motor.classification.comparative_domain_model.engine import (
                ComparativeDomainModelBuilderEngine,
            )
            from zovrake_motor.classification.concept_analysis.engine import ConceptAnalysisEngine
            from zovrake_motor.classification.concept_normalization.engine import ConceptNormalizationEngine
            from zovrake_motor.classification.context_association.engine import ContextAssociationEngine
            from zovrake_motor.classification.equivalence_detection.engine import EquivalenceDetectionEngine
            from zovrake_motor.classification.material_classification.engine import MaterialClassificationEngine
            from zovrake_motor.classification.service_classification.engine import ServiceClassificationEngine

            engines = (
                ConceptAnalysisEngine(),
                MaterialClassificationEngine(),
                ServiceClassificationEngine(),
                ConceptNormalizationEngine(),
                EquivalenceDetectionEngine(),
                ComparableGroupBuilderEngine(),
                ContextAssociationEngine(),
                ComparativeDomainModelBuilderEngine(),
                ClassificationQualityFrameworkEngine(),
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

    def _check_comparative_domain_model_consistency(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            result = run_full_classification_pipeline(service, process_id=process_id)
            assert result.comparative_domain_model_passed
            assert result.quality_validation_passed
            assert result.certification_prepared
            checks.append(
                self._passed(
                    area,
                    "comparative_domain_model_consistency",
                    "Modelo Comparativo de Dominio consistente y preparado para PM6",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_domain_model_consistency", str(exc)))

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
