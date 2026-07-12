"""Auditores especializados del Comparative Quality Framework."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityCategory,
    ComparativeQualityValidatorStrategyType,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.gateway import (
    ComparativeQualityInputView,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityCheck,
    ComparativeQualityFinding,
    ComparativeQualityValidatorResult,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.port import (
    ComparativeQualityValidatorPort,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeQualityFrameworkSettings,
)

PM6_FUNCTIONAL_COMPONENTS = frozenset(
    {
        "comparative_structure_engine",
        "dynamic_column_builder",
        "dynamic_row_builder",
        "provider_organization_engine",
        "group_integrity_engine",
        "traceability_metadata_engine",
        "comparative_model_builder",
        "comparative_validation_framework",
    },
)

PM6_PIPELINE_PHASES = frozenset(
    {
        "estructura_comparativa",
        "construccion_columnas",
        "construccion_filas",
        "organizacion_proveedores",
        "integridad_grupos",
        "trazabilidad_metadatos",
        "modelo_comparativo",
        "validacion_comparativa",
    },
)


class ArchitecturalComplianceValidator(ComparativeQualityValidatorPort):
    """Verifica cumplimiento de Clean Architecture, SOLID y escalabilidad."""

    @property
    def validator_name(self) -> str:
        return "architectural_compliance_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Cumplimiento Arquitectónico"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.ARCHITECTURAL_COMPLIANCE

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        modular_ok = len(PM6_FUNCTIONAL_COMPONENTS) >= 8
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.ARCHITECTURAL,
                check_name="modular_components_defined",
                passed=modular_ok,
                message="Arquitectura modular con componentes especializados"
                if modular_ok
                else "Componentes modulares insuficientes",
                target_id=input_view.catalog_id,
            ),
        )

        scalability_ok = (
            settings.max_tables_per_process > 0
            and settings.max_groups_per_process > 0
            and settings.max_providers_per_process > 0
        )
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.ARCHITECTURAL,
                check_name="scalability_limits_configured",
                passed=scalability_ok,
                message="Límites de escalabilidad configurados centralmente"
                if scalability_ok
                else "Límites de escalabilidad no configurados",
                target_id=input_view.catalog_id,
            ),
        )
        if not scalability_ok:
            findings.append(
                ComparativeQualityFinding(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.ARCHITECTURAL,
                    message="Configuración de escalabilidad incompleta",
                    severity="error",
                    target_id=input_view.catalog_id,
                ),
            )

        config_ok = settings.enabled
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.ARCHITECTURAL,
                check_name="centralized_configuration_enabled",
                passed=config_ok,
                message="Configuración centralizada activa"
                if config_ok
                else "Configuración centralizada deshabilitada",
                target_id=input_view.catalog_id,
            ),
        )

        immutability_ok = settings.preserve_catalog_immutability
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.ARCHITECTURAL,
                check_name="non_destructive_audit",
                passed=immutability_ok,
                message="Auditoría no destructiva habilitada"
                if immutability_ok
                else "Preservación de catálogos deshabilitada",
                target_id=input_view.catalog_id,
            ),
        )

        extension_ok = settings.module_certification_prepared
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.ARCHITECTURAL,
                check_name="extension_points_prepared",
                passed=extension_ok,
                message="Puntos de extensión preparados para certificación"
                if extension_ok
                else "Puntos de extensión no preparados",
                target_id=input_view.catalog_id,
            ),
        )

        if input_view.pipeline_snapshot:
            component_names = [
                str(stage.get("component_name", ""))
                for stage in input_view.pipeline_snapshot
                if stage.get("component_name")
            ]
            unique_names = len(component_names) == len(set(component_names))
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.ARCHITECTURAL,
                    check_name="single_responsibility_components",
                    passed=unique_names,
                    message="Componentes con responsabilidad única"
                    if unique_names
                    else "Componentes con nombres duplicados detectados",
                    target_id=input_view.catalog_id,
                ),
            )
            if not unique_names:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.ARCHITECTURAL,
                        message="Duplicación de responsabilidades en componentes",
                        severity="warning",
                        target_id=input_view.catalog_id,
                    ),
                )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=("architectural_audit_completed",),
        )


class DefinitiveModelConsistencyValidator(ComparativeQualityValidatorPort):
    """Verifica consistencia estructural de los Modelos Comparativos Definitivos."""

    @property
    def validator_name(self) -> str:
        return "definitive_model_consistency_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Consistencia del Modelo Definitivo"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.DEFINITIVE_MODEL_CONSISTENCY

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        contract_ok = input_view.pm6_definitive_output_contract
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.CONSISTENCY,
                check_name="pm6_definitive_output_contract",
                passed=contract_ok,
                message="Contrato PM6 activo en catálogo"
                if contract_ok
                else "Contrato PM6 ausente",
                target_id=input_view.catalog_id,
            ),
        )

        pm7_ok = input_view.pm7_input_contract_prepared
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.CONSISTENCY,
                check_name="pm7_input_contract_prepared",
                passed=pm7_ok,
                message="Contrato PM7 preparado"
                if pm7_ok
                else "Contrato PM7 no preparado",
                target_id=input_view.catalog_id,
            ),
        )

        for model in input_view.models:
            model_id = str(model.get("definitive_model_id", "unknown"))
            group_id = str(model.get("group_id", ""))
            traceability = model.get("traceability", {})
            comparable_group = (
                traceability.get("comparable_group", {})
                if isinstance(traceability, dict)
                else {}
            )

            for field_name in PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS:
                value = model.get(field_name)
                passed = value is not None and value != "" and value != []
                checks.append(
                    ComparativeQualityCheck(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.CONSISTENCY,
                        check_name=f"model_field_{field_name}",
                        passed=passed,
                        message=f"Campo {field_name} presente"
                        if passed
                        else f"Campo {field_name} ausente",
                        target_id=model_id,
                    ),
                )
                if not passed:
                    findings.append(
                        ComparativeQualityFinding(
                            validator_name=self.validator_name,
                            category=ComparativeQualityCategory.CONSISTENCY,
                            message=f"Campo obligatorio ausente: {field_name}",
                            severity="error",
                            target_id=model_id,
                        ),
                    )

            group_match = str(comparable_group.get("group_id", "")) == group_id
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.CONSISTENCY,
                    check_name="group_id_traceability_match",
                    passed=group_match,
                    message="group_id coherente con trazabilidad"
                    if group_match
                    else "group_id no coincide con trazabilidad",
                    target_id=model_id,
                ),
            )
            if not group_match:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.CONSISTENCY,
                        message="Inconsistencia entre group_id y trazabilidad",
                        severity="error",
                        target_id=model_id,
                    ),
                )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"models_audited={len(input_view.models)}",),
        )


class ValidationReportIntegrityValidator(ComparativeQualityValidatorPort):
    """Verifica integridad del reporte de validación del CVF."""

    @property
    def validator_name(self) -> str:
        return "validation_report_integrity_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Integridad del Reporte de Validación"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.VALIDATION_REPORT_INTEGRITY

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        report_fields = (
            "report_id",
            "process_id",
            "model_id",
            "document_id",
            "traceability",
        )
        for field_name in report_fields:
            value = input_view.raw_validation_report.get(field_name)
            passed = bool(value)
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.INTEGRITY,
                    check_name=f"validation_report_{field_name}",
                    passed=passed,
                    message=f"Reporte con {field_name}"
                    if passed
                    else f"Reporte sin {field_name}",
                    target_id=input_view.validation_report_id,
                ),
            )
            if not passed:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.INTEGRITY,
                        message=f"Campo obligatorio ausente en reporte CVF: {field_name}",
                        severity="error",
                        target_id=input_view.validation_report_id,
                    ),
                )

        check_sets_ok = input_view.validation_check_sets_count > 0
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.INTEGRITY,
                check_name="validation_check_sets_present",
                passed=check_sets_ok,
                message="Conjuntos de validación presentes"
                if check_sets_ok
                else "Sin conjuntos de validación en reporte CVF",
                target_id=input_view.validation_report_id,
            ),
        )
        if not check_sets_ok and not settings.allow_empty_catalog_validation:
            findings.append(
                ComparativeQualityFinding(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.INTEGRITY,
                    message="Reporte de validación sin conjuntos de verificación",
                    severity="error",
                    target_id=input_view.validation_report_id,
                ),
            )

        prepared_ok = input_view.validation_report_prepared
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.INTEGRITY,
                check_name="quality_framework_prepared",
                passed=prepared_ok,
                message="Reporte preparado para auditoría de calidad"
                if prepared_ok
                else "Reporte no preparado para CQF",
                target_id=input_view.validation_report_id,
            ),
        )

        preserved_ok = bool(
            input_view.raw_validation_report.get("definitive_catalog_preserved", True),
        )
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.INTEGRITY,
                check_name="definitive_catalog_preserved",
                passed=preserved_ok,
                message="Catálogo definitivo preservado por CVF"
                if preserved_ok
                else "Catálogo definitivo no preservado",
                target_id=input_view.validation_report_id,
            ),
        )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(
                f"validation_findings_count={input_view.validation_findings_count}",
            ),
        )


class IdentifierUniquenessValidator(ComparativeQualityValidatorPort):
    """Verifica unicidad de identificadores en el catálogo definitivo."""

    @property
    def validator_name(self) -> str:
        return "identifier_uniqueness_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Unicidad de Identificadores"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.IDENTIFIER_UNIQUENESS

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        definitive_ids: list[str] = []
        table_ids: list[str] = []
        group_ids: list[str] = []

        for model in input_view.models:
            definitive_ids.append(str(model.get("definitive_model_id", "")))
            table_ids.append(str(model.get("comparative_table_id", "")))
            group_ids.append(str(model.get("group_id", "")))

        for label, values in (
            ("definitive_model_id", definitive_ids),
            ("comparative_table_id", table_ids),
            ("group_id", group_ids),
        ):
            non_empty = [value for value in values if value]
            unique = len(non_empty) == len(set(non_empty))
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.UNIQUENESS,
                    check_name=f"{label}_unique",
                    passed=unique,
                    message=f"Identificadores {label} únicos"
                    if unique
                    else f"Identificadores {label} duplicados",
                    target_id=input_view.catalog_id,
                ),
            )
            if not unique:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.UNIQUENESS,
                        message=f"Identificadores duplicados: {label}",
                        severity="error",
                        target_id=input_view.catalog_id,
                    ),
                )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"models_checked={len(input_view.models)}",),
        )


class TraceabilityChainValidator(ComparativeQualityValidatorPort):
    """Verifica cadena completa de trazabilidad documental."""

    @property
    def validator_name(self) -> str:
        return "traceability_chain_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Trazabilidad"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.TRACEABILITY_CHAIN

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        traceability_fields = (
            "document_evidence",
            "comparable_group",
            "domain_catalog_id",
            "source_structure_catalog_id",
            "source_column_catalog_id",
            "source_row_catalog_id",
            "source_provider_catalog_id",
            "lineage",
        )

        for model in input_view.models:
            model_id = str(model.get("definitive_model_id", "unknown"))
            traceability = model.get("traceability", {})
            if not isinstance(traceability, dict):
                traceability = {}

            for field_name in traceability_fields:
                value = traceability.get(field_name)
                passed = value is not None and value != "" and value != {}
                checks.append(
                    ComparativeQualityCheck(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.TRACEABILITY,
                        check_name=f"traceability_{field_name}",
                        passed=passed,
                        message=f"Trazabilidad {field_name} presente"
                        if passed
                        else f"Trazabilidad {field_name} ausente",
                        target_id=model_id,
                    ),
                )
                if not passed:
                    findings.append(
                        ComparativeQualityFinding(
                            validator_name=self.validator_name,
                            category=ComparativeQualityCategory.TRACEABILITY,
                            message=f"Referencia de trazabilidad ausente: {field_name}",
                            severity="warning",
                            target_id=model_id,
                        ),
                    )

            document_evidence = traceability.get("document_evidence", {})
            if isinstance(document_evidence, dict):
                for evidence_field in (
                    "document_id",
                    "document_representation_id",
                    "internal_document_model_id",
                ):
                    passed = bool(document_evidence.get(evidence_field))
                    checks.append(
                        ComparativeQualityCheck(
                            validator_name=self.validator_name,
                            category=ComparativeQualityCategory.TRACEABILITY,
                            check_name=f"document_evidence_{evidence_field}",
                            passed=passed,
                            message=f"Evidencia documental {evidence_field} presente"
                            if passed
                            else f"Evidencia documental {evidence_field} ausente",
                            target_id=model_id,
                        ),
                    )

            domain_ok = bool(traceability.get("domain_model_preserved", True))
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.TRACEABILITY,
                    check_name="domain_model_preserved",
                    passed=domain_ok,
                    message="Modelo de dominio preservado"
                    if domain_ok
                    else "Modelo de dominio no preservado",
                    target_id=model_id,
                ),
            )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(
                f"traceability_models_checked={len(input_view.models)}",
            ),
        )


class PipelineFlowValidator(ComparativeQualityValidatorPort):
    """Verifica continuidad del Pipeline PM6 de extremo a extremo."""

    @property
    def validator_name(self) -> str:
        return "pipeline_flow_validator"

    @property
    def validator_label(self) -> str:
        return "Auditor de Flujo del Pipeline"

    @property
    def validator_type(self) -> ComparativeQualityValidatorStrategyType:
        return ComparativeQualityValidatorStrategyType.PIPELINE_FLOW

    def validate(
        self,
        input_view: ComparativeQualityInputView,
        *,
        settings: ComparativeQualityFrameworkSettings,
    ) -> ComparativeQualityValidatorResult:
        checks: list[ComparativeQualityCheck] = []
        findings: list[ComparativeQualityFinding] = []

        if not input_view.pipeline_snapshot:
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.PIPELINE,
                    check_name="pipeline_snapshot_provided",
                    passed=not settings.require_pipeline_snapshot,
                    message="Snapshot del pipeline no proporcionado",
                    target_id=input_view.catalog_id,
                ),
            )
            if settings.require_pipeline_snapshot:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.PIPELINE,
                        message="Snapshot del pipeline requerido pero no proporcionado",
                        severity="warning",
                        target_id=input_view.catalog_id,
                    ),
                )
            return ComparativeQualityValidatorResult(
                validator_type=self.validator_type.value,
                validator_name=self.validator_name,
                checks=tuple(checks),
                findings=tuple(findings),
                technical_observations=("pipeline_snapshot_missing",),
            )

        ready_components = {
            str(stage.get("component_name"))
            for stage in input_view.pipeline_snapshot
            if stage.get("component_ready") is True and stage.get("component_name")
        }

        for component_name in PM6_FUNCTIONAL_COMPONENTS:
            passed = component_name in ready_components
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.PIPELINE,
                    check_name=f"pipeline_component_{component_name}",
                    passed=passed,
                    message=f"Componente {component_name} listo en pipeline"
                    if passed
                    else f"Componente {component_name} no listo en pipeline",
                    target_id=component_name,
                ),
            )
            if not passed:
                findings.append(
                    ComparativeQualityFinding(
                        validator_name=self.validator_name,
                        category=ComparativeQualityCategory.PIPELINE,
                        message=f"Componente del pipeline no listo: {component_name}",
                        severity="warning",
                        target_id=component_name,
                    ),
                )

        present_phases = {
            str(stage.get("phase"))
            for stage in input_view.pipeline_snapshot
            if stage.get("phase")
        }
        for phase in PM6_PIPELINE_PHASES:
            passed = phase in present_phases
            checks.append(
                ComparativeQualityCheck(
                    validator_name=self.validator_name,
                    category=ComparativeQualityCategory.PIPELINE,
                    check_name=f"pipeline_phase_{phase}",
                    passed=passed,
                    message=f"Fase {phase} registrada en pipeline"
                    if passed
                    else f"Fase {phase} ausente en pipeline",
                    target_id=phase,
                ),
            )

        validation_stage = next(
            (
                stage
                for stage in input_view.pipeline_snapshot
                if stage.get("phase") == "validacion_comparativa"
            ),
            None,
        )
        validation_ready = (
            validation_stage is not None
            and validation_stage.get("component_ready") is True
        )
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.PIPELINE,
                check_name="validation_stage_ready",
                passed=validation_ready,
                message="Etapa VALIDACION_COMPARATIVA lista"
                if validation_ready
                else "Etapa VALIDACION_COMPARATIVA no lista",
                target_id="validacion_comparativa",
            ),
        )

        phases = [
            str(stage.get("phase", ""))
            for stage in input_view.pipeline_snapshot
            if stage.get("phase")
        ]
        no_duplicate_phases = len(phases) == len(set(phases))
        checks.append(
            ComparativeQualityCheck(
                validator_name=self.validator_name,
                category=ComparativeQualityCategory.PIPELINE,
                check_name="no_duplicate_pipeline_phases",
                passed=no_duplicate_phases,
                message="Fases del pipeline sin duplicación"
                if no_duplicate_phases
                else "Fases duplicadas detectadas en pipeline",
                target_id=input_view.catalog_id,
            ),
        )

        return ComparativeQualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(
                f"pipeline_stages_checked={len(input_view.pipeline_snapshot)}",
            ),
        )
