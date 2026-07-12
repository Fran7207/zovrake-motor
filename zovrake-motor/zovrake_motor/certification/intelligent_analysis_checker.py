"""
Certificador integral del Módulo de Razonamiento y Resultado del Análisis Inteligente.

Implementación 7.9 — Integración y certificación del Prompt Maestro 7.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.certification.intelligent_analysis_fixtures import (
    build_definitive_catalog_for_certification,
)
from zovrake_motor.certification.intelligent_analysis_pipeline import (
    run_full_intelligent_analysis_pipeline,
)
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.governance import (
    INPUT_CONTRACT_NAME,
    OPERATIVE_FUNCTIONAL_COMPONENTS,
    OUTPUT_CONTRACT_NAME,
    OUTPUT_GROUP_CONTRACT_NAME,
)
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.intelligent_analysis.reasoning_result_builder.governance import (
    INTEGRATION_CERTIFICATION_FRAMEWORK_PREPARED,
    PM7_OUTPUT_CATALOG_CONTRACT_NAME,
    PM7_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.intelligent_analysis.service import IntelligentAnalysisService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager

FORBIDDEN_INTELLIGENT_ANALYSIS_IMPORTS = (
    "zovrake_motor.reception",
    "zovrake_motor.documents",
    "zovrake_motor.context",
    "zovrake_motor.communication",
    "zovrake_motor.comprehension",
    "zovrake_motor.classification",
    "zovrake_motor.comparative_tables",
)

PIPELINE_ENGINE_COMPONENTS = (
    ("evidence_analysis_engine", "Evidence Analysis Engine"),
    ("consistency_evaluation_engine", "Consistency Evaluation Engine"),
    ("risk_analysis_engine", "Risk Analysis Engine"),
    ("context_evaluation_engine", "Context Evaluation Engine"),
    ("explanation_generation_engine", "Explanation Generation Engine"),
    ("recommendation_generation_engine", "Recommendation Generation Engine"),
    ("reasoning_result_builder", "Reasoning Result Builder"),
)

EXPECTED_PIPELINE_PHASES = (
    IntelligentAnalysisPhase.PREPARACION,
    IntelligentAnalysisPhase.CONSUMO_MODELO_COMPARATIVO_DEFINITIVO,
    IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS,
    IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA,
    IntelligentAnalysisPhase.ANALISIS_RIESGOS,
    IntelligentAnalysisPhase.EVALUACION_CONTEXTO,
    IntelligentAnalysisPhase.GENERACION_EXPLICACIONES,
    IntelligentAnalysisPhase.GENERACION_CONCLUSIONES,
    IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES,
    IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE,
    IntelligentAnalysisPhase.GESTION_CONFIANZA,
    IntelligentAnalysisPhase.GESTION_TRAZABILIDAD,
    IntelligentAnalysisPhase.FINALIZACION,
)


class IntelligentAnalysisModuleCertificationChecker:
    """Certifica el Módulo de Razonamiento Inteligente como sistema integrado."""

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
        checks.extend(self._check_output_contract_consistency())
        checks.extend(self._check_governance_and_contract())
        return checks

    def _check_module_initialization(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            service = IntelligentAnalysisService()
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
            assert ready == 11
            checks.append(
                self._passed(area, "components_ready", f"11 componentes operativos del pipeline ({ready})"),
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
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            phases = IntelligentAnalysisPipeline.ordered_phases()
            assert phases == EXPECTED_PIPELINE_PHASES
            checks.append(
                self._passed(area, "pipeline_phases", "13 etapas del Pipeline PM7 certificadas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_phases", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            snapshot = IntelligentAnalysisPipeline.build_snapshot(service.component_registry)
            functional_stages = [
                stage
                for stage in snapshot
                if stage.get("component_name") in {name for name, _ in PIPELINE_ENGINE_COMPONENTS}
            ]
            assert len(functional_stages) == 7
            assert all(stage["component_ready"] for stage in functional_stages)
            checks.append(
                self._passed(area, "pipeline_stages_registered", "7 etapas funcionales registradas y listas"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_stages_registered", str(exc)))

        return checks

    def _check_full_pipeline_execution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(
                process_id=process_id,
                document_id="DOC-FULL-PM7-CERT",
            )
            result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
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
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )
            assert result.traceability_intact
            checks.append(
                self._passed(area, "traceability_chain", "Cadena de trazabilidad intacta en todo el flujo"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "traceability_chain", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )
            assert result.definitive_catalog_preserved
            assert result.source_catalogs_preserved
            checks.append(
                self._passed(
                    area,
                    "source_immutability",
                    "Modelo Comparativo Definitivo y catálogos fuente preservados sin modificación",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "source_immutability", str(exc)))

        return checks

    def _check_coordinator_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            config = ConfigurationProvider.default()
            coordinator = MotorCoordinator(config_provider=config)
            service = IntelligentAnalysisService(config_provider=config)
            service.initialize()
            coordinator.register_module(service)
            coordinator.initialize_modules()
            coordinator.prepare_modules()
            assert coordinator.is_module_available("intelligent_analysis")
            checks.append(
                self._passed(
                    area,
                    "coordinator_registration",
                    "Coordinator administra el módulo de Razonamiento Inteligente",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_registration", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            coordinator = service.intelligent_analysis_coordinator
            assert coordinator is not None
            assert coordinator.is_ready()
            assert coordinator.component_name == "intelligent_analysis_coordinator"
            checks.append(
                self._passed(
                    area,
                    "internal_coordinator",
                    "Coordinator interno administra la estructura de componentes PM7",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "internal_coordinator", str(exc)))

        return checks

    def _check_state_and_event_integration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            state_manager = StateManager()
            event_manager = EventManager()
            service = IntelligentAnalysisService(
                state_manager=state_manager,
                event_manager=event_manager,
            )
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )

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
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            provider = ConfigurationProvider.default()
            intelligent_analysis = provider.intelligent_analysis()
            required = (
                "evidence_analysis_engine",
                "consistency_evaluation_engine",
                "risk_analysis_engine",
                "context_evaluation_engine",
                "explanation_generation_engine",
                "recommendation_generation_engine",
                "reasoning_result_builder",
            )
            for attr in required:
                assert hasattr(intelligent_analysis, attr)
            checks.append(
                self._passed(
                    area,
                    "central_configuration",
                    "Configuración central unificada para todos los motores PM7",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "central_configuration", str(exc)))

        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            package = importlib.import_module("zovrake_motor.intelligent_analysis")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__,
                prefix=package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_INTELLIGENT_ANALYSIS_IMPORTS:
                    assert forbidden not in content, f"{modname} importa {forbidden}"
            checks.append(
                self._passed(area, "module_isolation", "Sin dependencias directas entre módulos del Motor"),
            )
        except Exception as exc:
            checks.append(self._failed(area, "module_isolation", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            gateway_snapshot = service.comparative_tables_gateway.snapshot()
            assert gateway_snapshot.get("accesses_source_files") is False
            checks.append(
                self._passed(
                    area,
                    "comparative_tables_gateway_isolation",
                    "Gateway de consumo sin acceso a documentos originales",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "comparative_tables_gateway_isolation", str(exc)))

        return checks

    def _check_extensibility(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.engine import (
                ConsistencyEvaluationBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.context_evaluation_engine.engine import (
                ContextEvaluationBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.evidence_analysis_engine.engine import (
                EvidenceAnalysisBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.explanation_generation_engine.engine import (
                ExplanationGenerationBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.reasoning_result_builder.engine import (
                ReasoningResultBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.recommendation_generation_engine.engine import (
                RecommendationGenerationBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.risk_analysis_engine.engine import (
                RiskAnalysisBuilderEngine,
            )

            engines = (
                EvidenceAnalysisBuilderEngine(),
                ConsistencyEvaluationBuilderEngine(),
                RiskAnalysisBuilderEngine(),
                ContextEvaluationBuilderEngine(),
                ExplanationGenerationBuilderEngine(),
                RecommendationGenerationBuilderEngine(),
                ReasoningResultBuilderEngine(),
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

    def _check_output_contract_consistency(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )
            assert result.pm7_output_contract_valid
            assert result.results_count >= 1
            checks.append(
                self._passed(
                    area,
                    "output_contract_consistency",
                    "Resultado del Análisis Inteligente consistente y estable",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_consistency", str(exc)))

        return checks

    def _check_governance_and_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE

        try:
            assert len(OPERATIVE_FUNCTIONAL_COMPONENTS) == 7
            assert INPUT_CONTRACT_NAME == "DefinitiveComparativeModelCatalog"
            assert OUTPUT_CONTRACT_NAME == PM7_OUTPUT_CATALOG_CONTRACT_NAME
            assert OUTPUT_GROUP_CONTRACT_NAME == PM7_OUTPUT_CONTRACT_NAME
            assert INTEGRATION_CERTIFICATION_FRAMEWORK_PREPARED is True
            checks.append(
                self._passed(
                    area,
                    "governance_contract",
                    "Gobierno arquitectónico y contrato oficial PM7 declarados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "governance_contract", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )
            assert result.integration_certification_framework_prepared
            checks.append(
                self._passed(
                    area,
                    "integration_certification_prepared",
                    "Módulo certificado y preparado para cierre oficial (7.10)",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "integration_certification_prepared", str(exc)))

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
