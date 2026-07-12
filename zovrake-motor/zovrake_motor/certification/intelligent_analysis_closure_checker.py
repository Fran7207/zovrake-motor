"""
Certificador de cierre formal del Prompt Maestro 7.

Implementación 7.10 — Gobierno arquitectónico y congelamiento del módulo.
No modifica motores ni introduce funcionalidad nueva.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.intelligent_analysis_checker import (
    IntelligentAnalysisModuleCertificationChecker,
)
from zovrake_motor.certification.intelligent_analysis_fixtures import (
    build_definitive_catalog_for_certification,
)
from zovrake_motor.certification.intelligent_analysis_pipeline import (
    run_full_intelligent_analysis_pipeline,
)
from zovrake_motor.certification.models import CertificationCheck
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.governance import (
    ARCHITECTURAL_BOUNDARIES,
    EVOLUTION_EXTENSION_POINTS,
    FROZEN_FUNCTIONAL_COMPONENTS,
    OUTPUT_CONTRACT_FORBIDDEN_DOWNSTREAM_ACCESSES,
    OUTPUT_CONTRACT_NAME,
    OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS,
    OUTPUT_CONTRACT_REQUIRED_RESULT_FIELDS,
    OUTPUT_GROUP_CONTRACT_NAME,
    PROMPT_MAESTRO_7_STATUS,
    XAI_REQUIRED_RESULT_ATTRIBUTES,
    closure_snapshot,
    frozen_component_names,
)
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    GroupIntelligentAnalysisResult,
    IntelligentAnalysisResultCatalog,
)
from zovrake_motor.intelligent_analysis.service import IntelligentAnalysisService

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
INTELLIGENT_ANALYSIS_ROOT = PACKAGE_ROOT / "intelligent_analysis"

REQUIRED_DOCUMENTATION = (
    INTELLIGENT_ANALYSIS_ROOT / "ARCHITECTURE.md",
    INTELLIGENT_ANALYSIS_ROOT / "CERTIFICATION.md",
    INTELLIGENT_ANALYSIS_ROOT / "CLOSURE.md",
    INTELLIGENT_ANALYSIS_ROOT / "OUTPUT_CONTRACT.md",
)

DOWNSTREAM_SCAN_PACKAGES = (
    "processing",
    "communication",
    "reception",
    "documents",
    "context",
)


class IntelligentAnalysisModuleClosureChecker:
    """Formaliza el cierre arquitectónico del Prompt Maestro 7."""

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_prior_certification())
        checks.extend(self._check_architecture_freeze())
        checks.extend(self._check_output_contract())
        checks.extend(self._check_architectural_boundaries())
        checks.extend(self._check_pipeline_stability())
        checks.extend(self._check_xai_principles())
        checks.extend(self._check_downstream_compatibility())
        checks.extend(self._check_extensibility_and_evolution())
        checks.extend(self._check_documentation_closure())
        checks.extend(self._check_governance_declaration())
        return checks

    def _check_prior_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            prior = IntelligentAnalysisModuleCertificationChecker().run()
            failed = [check for check in prior if not check.passed]
            assert not failed, f"Certificación 7.9 incompleta: {len(failed)} fallos"
            checks.append(
                self._passed(
                    area,
                    "prior_certification_valid",
                    "Certificación integral 7.9 vigente y aprobada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "prior_certification_valid", str(exc)))

        return checks

    def _check_architecture_freeze(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        service: IntelligentAnalysisService | None = None
        try:
            service = IntelligentAnalysisService()
            service.initialize()
            for component_id, label, implementation in FROZEN_FUNCTIONAL_COMPONENTS:
                component = service.component_registry.get(component_id)
                assert component is not None, f"Componente congelado ausente: {component_id}"
                assert component.is_ready(), f"Componente congelado no operativo: {component_id}"
                assert component.component_name == component_id
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
                if (component := service.component_registry.get(name)) is not None and component.is_ready()
            }
            assert ready_names == set(frozen_component_names())
            checks.append(
                self._passed(
                    area,
                    "frozen_components_complete",
                    "7 componentes funcionales congelados y operativos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "frozen_components_complete", str(exc)))

        return checks

    def _check_output_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            catalog_fields = {
                field.name for field in IntelligentAnalysisResultCatalog.__dataclass_fields__.values()
            }
            result_fields = {
                field.name for field in GroupIntelligentAnalysisResult.__dataclass_fields__.values()
            }
            for required in OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS:
                assert required in catalog_fields or required == "results"
            for required in OUTPUT_CONTRACT_REQUIRED_RESULT_FIELDS:
                assert required in result_fields
            checks.append(
                self._passed(
                    area,
                    "output_contract_schema",
                    f"{OUTPUT_CONTRACT_NAME} define el contrato oficial de salida",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_schema", str(exc)))

        try:
            service = IntelligentAnalysisService()
            service.initialize()
            process_id = uuid4()
            definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
            pipeline_result = run_full_intelligent_analysis_pipeline(
                service,
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            )
            assert pipeline_result.stages_executed == 7

            rrb = service.reasoning_result_builder
            assert rrb is not None
            catalogs = rrb.catalog_store.get_by_process(process_id)
            assert catalogs, "El pipeline debe persistir al menos un catálogo de resultados"
            catalog_dict = catalogs[-1].to_dict()

            for field in OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS:
                assert field in catalog_dict, f"Campo obligatorio ausente: {field}"
            assert catalog_dict.get("contract_name") == OUTPUT_CONTRACT_NAME
            assert catalog_dict.get("source_data_preserved") is True

            results = catalog_dict.get("results", [])
            assert results, "El contrato requiere al menos un resultado por grupo comparable"
            for field in OUTPUT_CONTRACT_REQUIRED_RESULT_FIELDS:
                assert field in results[0], f"Campo de resultado obligatorio ausente: {field}"
            assert results[0].get("contract_name") == OUTPUT_GROUP_CONTRACT_NAME

            checks.append(
                self._passed(
                    area,
                    "output_contract_runtime",
                    "Contrato de salida verificado en ejecución del pipeline",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_runtime", str(exc)))

        return checks

    def _check_architectural_boundaries(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            assert len(ARCHITECTURAL_BOUNDARIES) == 3
            modules = {boundary["module"] for boundary in ARCHITECTURAL_BOUNDARIES}
            assert modules == {"comparative_tables", "intelligent_analysis", "processing"}
            checks.append(
                self._passed(
                    area,
                    "boundary_definitions",
                    "Fronteras PM6 -> PM7 -> Orquestación definidas",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "boundary_definitions", str(exc)))

        try:
            intelligent_analysis_package = importlib.import_module("zovrake_motor.intelligent_analysis")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                intelligent_analysis_package.__path__,
                prefix=intelligent_analysis_package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                assert "zovrake_motor.comparative_tables" not in content
                assert "zovrake_motor.classification" not in content
                assert "zovrake_motor.comprehension" not in content
            checks.append(
                self._passed(
                    area,
                    "intelligent_analysis_boundary_isolation",
                    "Razonamiento Inteligente aislado de módulos previos del Motor",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "intelligent_analysis_boundary_isolation", str(exc)))

        try:
            coordinator_source = (PACKAGE_ROOT / "coordinator" / "pipeline.py").read_text(encoding="utf-8")
            assert '"comparative_tables"' in coordinator_source
            assert '"intelligent_analysis"' in coordinator_source
            tables_index = coordinator_source.index('"comparative_tables"')
            analysis_index = coordinator_source.index('"intelligent_analysis"')
            assert tables_index < analysis_index
            checks.append(
                self._passed(
                    area,
                    "coordinator_boundary_order",
                    "Coordinator preserva orden PM6 -> PM7",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_boundary_order", str(exc)))

        return checks

    def _check_pipeline_stability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            phases = IntelligentAnalysisPipeline.ordered_phases()
            assert phases.index(IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS) < phases.index(
                IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE,
            )
            checks.append(
                self._passed(
                    area,
                    "pipeline_phase_order",
                    "Orden oficial del Pipeline PM7 congelado",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_phase_order", str(exc)))

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
            assert result.complete
            assert result.traceability_intact
            assert result.definitive_catalog_preserved
            checks.append(
                self._passed(
                    area,
                    "pipeline_end_to_end_stability",
                    "Pipeline completo estable desde PM6 hasta Resultado del Análisis",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pipeline_end_to_end_stability", str(exc)))

        return checks

    def _check_xai_principles(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

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

            rrb = service.reasoning_result_builder
            assert rrb is not None
            catalogs = rrb.catalog_store.get_by_process(process_id)
            catalog = catalogs[-1]
            assert catalog.results

            for group_result in catalog.results:
                payload = group_result.to_dict()
                for attribute in XAI_REQUIRED_RESULT_ATTRIBUTES:
                    assert attribute in payload, f"Atributo XAI obligatorio ausente: {attribute}"

                recommendation = payload.get("recommendation", {})
                justification = recommendation.get("justification", {})
                assert justification or recommendation.get("scenario_type"), (
                    "Toda recomendación debe incluir justificación o escenario documentado"
                )

                traceability = payload.get("document_traceability", {})
                assert traceability.get("document_id")
                assert traceability.get("definitive_model_id")

                explanation = payload.get("structured_explanation", {})
                assert explanation.get("segment_ids") or explanation.get("segments"), (
                    "Toda explicación debe ser trazable mediante segmentos"
                )

            checks.append(
                self._passed(
                    area,
                    "xai_explainability",
                    "Recomendaciones explicables, trazables y respaldadas por evidencias",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "xai_explainability", str(exc)))

        return checks

    def _check_downstream_compatibility(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            for package_name in DOWNSTREAM_SCAN_PACKAGES:
                package_path = PACKAGE_ROOT / package_name
                if not package_path.is_dir():
                    continue
                for _finder, modname, _ispkg in pkgutil.walk_packages(
                    [str(package_path)],
                    prefix=f"zovrake_motor.{package_name}.",
                ):
                    module = importlib.import_module(modname)
                    source = getattr(module, "__file__", "") or ""
                    if not source.endswith(".py"):
                        continue
                    content = Path(source).read_text(encoding="utf-8").lower()
                    for forbidden in OUTPUT_CONTRACT_FORBIDDEN_DOWNSTREAM_ACCESSES:
                        assert forbidden not in content, (
                            f"Consumidor no autorizado de artefactos PM7: {forbidden} ({modname})"
                        )
            checks.append(
                self._passed(
                    area,
                    "downstream_contract_isolation",
                    "Consumidores externos reservados sin accesos directos a artefactos PM7",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "downstream_contract_isolation", str(exc)))

        try:
            snapshot = closure_snapshot()
            assert snapshot["output_contract"]["name"] == OUTPUT_CONTRACT_NAME
            assert snapshot["xai_principles"]["explainable_recommendations"] is True
            checks.append(
                self._passed(
                    area,
                    "erp_consumption_ready",
                    "Resultado del Análisis Inteligente listo para ERP y APIs futuras",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "erp_consumption_ready", str(exc)))

        return checks

    def _check_extensibility_and_evolution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            assert len(EVOLUTION_EXTENSION_POINTS) == 9
            checks.append(
                self._passed(
                    area,
                    "evolution_extension_points",
                    "9 puntos de extensión declarados para evolución controlada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "evolution_extension_points", str(exc)))

        try:
            from zovrake_motor.intelligent_analysis.evidence_analysis_engine.engine import (
                EvidenceAnalysisBuilderEngine,
            )
            from zovrake_motor.intelligent_analysis.reasoning_result_builder.engine import (
                ReasoningResultBuilderEngine,
            )

            for engine in (EvidenceAnalysisBuilderEngine(), ReasoningResultBuilderEngine()):
                engine.initialize()
                assert hasattr(engine.registry, "register") or hasattr(engine, "extend")
            checks.append(
                self._passed(
                    area,
                    "controlled_evolution_registries",
                    "Evolución futura mediante registros sin modificar el núcleo",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "controlled_evolution_registries", str(exc)))

        return checks

    def _check_documentation_closure(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            missing = [str(path) for path in REQUIRED_DOCUMENTATION if not path.is_file()]
            assert not missing, f"Documentación faltante: {', '.join(missing)}"
            checks.append(
                self._passed(
                    area,
                    "documentation_complete",
                    "Documentación final de cierre arquitectónico disponible",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "documentation_complete", str(exc)))

        return checks

    def _check_governance_declaration(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE

        try:
            snapshot = closure_snapshot()
            assert snapshot["status"] == PROMPT_MAESTRO_7_STATUS
            assert snapshot["prompt_maestro"] == "7"
            assert snapshot["next_prompt_maestro"] == "8"
            assert len(snapshot["frozen_components"]) == 7
            checks.append(
                self._passed(
                    area,
                    "governance_closure_declaration",
                    "Prompt Maestro 7 declarado oficialmente CERRADO",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "governance_closure_declaration", str(exc)))

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
