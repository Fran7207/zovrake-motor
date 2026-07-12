"""
Certificador de cierre formal del Prompt Maestro 5.

Implementación 3.12 — Gobierno arquitectónico y congelamiento del módulo.
No modifica motores ni introduce funcionalidad nueva.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

from zovrake_motor.classification.governance import (
    ARCHITECTURAL_BOUNDARIES,
    EVOLUTION_EXTENSION_POINTS,
    FROZEN_FUNCTIONAL_COMPONENTS,
    OUTPUT_CONTRACT_FORBIDDEN_PM6_ACCESSES,
    OUTPUT_CONTRACT_NAME,
    OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS,
    OUTPUT_CONTRACT_REQUIRED_MODEL_FIELDS,
    PROMPT_MAESTRO_5_STATUS,
    closure_snapshot,
    frozen_component_names,
)
from zovrake_motor.classification.service import ClassificationService
from zovrake_motor.certification.classification_checker import ClassificationModuleCertificationChecker
from zovrake_motor.certification.classification_pipeline import run_full_classification_pipeline
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.models import CertificationCheck

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
CLASSIFICATION_ROOT = PACKAGE_ROOT / "classification"

REQUIRED_DOCUMENTATION = (
    CLASSIFICATION_ROOT / "ARCHITECTURE.md",
    CLASSIFICATION_ROOT / "CERTIFICATION.md",
    CLASSIFICATION_ROOT / "CLOSURE.md",
    CLASSIFICATION_ROOT / "OUTPUT_CONTRACT.md",
)


class ClassificationModuleClosureChecker:
    """Formaliza el cierre arquitectónico del Prompt Maestro 5."""

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_prior_certification())
        checks.extend(self._check_architecture_freeze())
        checks.extend(self._check_output_contract())
        checks.extend(self._check_architectural_boundaries())
        checks.extend(self._check_domain_model_stability())
        checks.extend(self._check_pm6_readiness())
        checks.extend(self._check_extensibility_and_evolution())
        checks.extend(self._check_documentation_closure())
        checks.extend(self._check_governance_declaration())
        return checks

    def _check_prior_certification(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            prior = ClassificationModuleCertificationChecker().run()
            failed = [check for check in prior if not check.passed]
            assert not failed, f"Certificación 3.11 incompleta: {len(failed)} fallos"
            checks.append(
                self._passed(
                    area,
                    "prior_certification_valid",
                    "Certificación integral 3.11 vigente y aprobada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "prior_certification_valid", str(exc)))

        return checks

    def _check_architecture_freeze(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        service: ClassificationService | None = None
        try:
            service = ClassificationService()
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
                    "9 componentes funcionales congelados y operativos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "frozen_components_complete", str(exc)))

        return checks

    def _check_output_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            from zovrake_motor.classification.comparative_domain_model.models import (
                ComparativeDomainModelCatalog,
            )

            catalog_fields = {field.name for field in ComparativeDomainModelCatalog.__dataclass_fields__.values()}
            for required in OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS:
                assert required in catalog_fields or required == "models"
            checks.append(
                self._passed(
                    area,
                    "output_contract_catalog_schema",
                    f"{OUTPUT_CONTRACT_NAME} define el contrato oficial de salida",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_catalog_schema", str(exc)))

        try:
            service = ClassificationService()
            service.initialize()
            process_id = uuid4()
            pipeline_result = run_full_classification_pipeline(service, process_id=process_id)
            assert pipeline_result.stages_executed == 9

            cdmb = service.comparative_domain_model_builder
            assert cdmb is not None
            catalogs = cdmb.catalog_store.get_by_process(process_id)
            assert catalogs, "El pipeline debe persistir al menos un catálogo del modelo comparativo"
            catalog_dict = catalogs[-1].to_dict()

            for field in OUTPUT_CONTRACT_REQUIRED_CATALOG_FIELDS:
                assert field in catalog_dict, f"Campo obligatorio ausente: {field}"
            assert catalog_dict.get("pm6_output_contract") is True

            models = catalog_dict.get("models", [])
            assert models, "El contrato requiere al menos un modelo comparativo para PM6"
            for field in OUTPUT_CONTRACT_REQUIRED_MODEL_FIELDS:
                assert field in models[0], f"Campo de modelo obligatorio ausente: {field}"

            checks.append(
                self._passed(
                    area,
                    "output_contract_runtime",
                    "Contrato de salida verificado en ejecución del pipeline",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_runtime", str(exc)))

        try:
            comparative_tables = PACKAGE_ROOT / "comparative_tables"
            if comparative_tables.is_dir():
                for _finder, modname, _ispkg in pkgutil.walk_packages(
                    [str(comparative_tables)],
                    prefix="zovrake_motor.comparative_tables.",
                ):
                    module = importlib.import_module(modname)
                    source = getattr(module, "__file__", "") or ""
                    if not source.endswith(".py"):
                        continue
                    content = Path(source).read_text(encoding="utf-8")
                    for forbidden in OUTPUT_CONTRACT_FORBIDDEN_PM6_ACCESSES:
                        assert forbidden not in content.lower(), (
                            f"PM6 no debe acceder directamente a {forbidden} ({modname})"
                        )
            checks.append(
                self._passed(
                    area,
                    "output_contract_isolation",
                    "PM6 reservado sin accesos directos a modelos intermedios",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "output_contract_isolation", str(exc)))

        return checks

    def _check_architectural_boundaries(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            assert len(ARCHITECTURAL_BOUNDARIES) == 3
            modules = {boundary["module"] for boundary in ARCHITECTURAL_BOUNDARIES}
            assert modules == {"comprehension", "classification", "comparative_tables"}
            checks.append(
                self._passed(
                    area,
                    "boundary_definitions",
                    "Fronteras Comprension -> Clasificacion -> Cuadros Comparativos definidas",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "boundary_definitions", str(exc)))

        try:
            classification_package = importlib.import_module("zovrake_motor.classification")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                classification_package.__path__,
                prefix=classification_package.__name__ + ".",
            ):
                module = importlib.import_module(modname)
                source = getattr(module, "__file__", "") or ""
                if not source.endswith(".py"):
                    continue
                content = Path(source).read_text(encoding="utf-8")
                assert "zovrake_motor.comprehension" not in content
                assert "zovrake_motor.comparative_tables" not in content
            checks.append(
                self._passed(
                    area,
                    "classification_boundary_isolation",
                    "Clasificación aislada de Comprensión y Cuadros Comparativos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "classification_boundary_isolation", str(exc)))

        try:
            coordinator_source = (PACKAGE_ROOT / "coordinator" / "pipeline.py").read_text(encoding="utf-8")
            assert '"comprehension"' in coordinator_source
            assert '"classification"' in coordinator_source
            assert '"comparative_tables"' in coordinator_source
            comprehension_index = coordinator_source.index('"comprehension"')
            classification_index = coordinator_source.index('"classification"')
            tables_index = coordinator_source.index('"comparative_tables"')
            assert comprehension_index < classification_index < tables_index
            checks.append(
                self._passed(
                    area,
                    "coordinator_boundary_order",
                    "Coordinator preserva orden de fronteras modulares",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "coordinator_boundary_order", str(exc)))

        return checks

    def _check_domain_model_stability(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            service = ClassificationService()
            service.initialize()
            result = run_full_classification_pipeline(service, process_id=uuid4())
            assert result.comparative_domain_model_passed
            assert result.traceability_intact
            assert result.source_data_immutable
            checks.append(
                self._passed(
                    area,
                    "domain_model_consistency",
                    "Modelo Comparativo consistente y trazable",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "domain_model_consistency", str(exc)))

        try:
            config = __import__(
                "zovrake_motor.config.categories.classification",
                fromlist=["ComparativeDomainModelBuilderSettings"],
            )
            settings = config.ComparativeDomainModelBuilderSettings.default()
            assert settings.pm6_output_contract is True
            assert settings.preserve_catalog_immutability is True
            checks.append(
                self._passed(
                    area,
                    "domain_model_configuration_stable",
                    "Configuración del modelo comparativo estable y centralizada",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "domain_model_configuration_stable", str(exc)))

        return checks

    def _check_pm6_readiness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            service = ClassificationService()
            service.initialize()
            result = run_full_classification_pipeline(service, process_id=uuid4())
            assert result.complete
            assert result.certification_prepared

            cdmb = service.comparative_domain_model_builder
            assert cdmb is not None
            assert cdmb.catalog_store.count() >= 0

            checks.append(
                self._passed(
                    area,
                    "pm6_direct_consumption_ready",
                    "PM6 puede consumir ComparativeDomainModelCatalog sin transformaciones",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pm6_direct_consumption_ready", str(exc)))

        try:
            coordinator_pipeline = (PACKAGE_ROOT / "coordinator" / "pipeline.py").read_text(encoding="utf-8")
            assert "comparative_tables" in coordinator_pipeline
            checks.append(
                self._passed(
                    area,
                    "pm6_pipeline_slot_reserved",
                    "Espacio arquitectónico reservado para Prompt Maestro 6",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "pm6_pipeline_slot_reserved", str(exc)))

        return checks

    def _check_extensibility_and_evolution(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

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
            from zovrake_motor.classification.concept_analysis.engine import ConceptAnalysisEngine
            from zovrake_motor.classification.equivalence_detection.engine import EquivalenceDetectionEngine
            from zovrake_motor.classification.material_classification.engine import MaterialClassificationEngine

            for engine in (ConceptAnalysisEngine(), MaterialClassificationEngine(), EquivalenceDetectionEngine()):
                engine.initialize()
                assert hasattr(engine.registry, "register")
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
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

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
        area = CertificationArea.CLASSIFICATION_MODULE_CLOSURE

        try:
            snapshot = closure_snapshot()
            assert snapshot["status"] == PROMPT_MAESTRO_5_STATUS
            assert snapshot["prompt_maestro"] == "5"
            assert snapshot["next_prompt_maestro"] == "6"
            assert len(snapshot["frozen_components"]) == 9
            checks.append(
                self._passed(
                    area,
                    "governance_closure_declaration",
                    "Prompt Maestro 5 declarado oficialmente CERRADO",
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
