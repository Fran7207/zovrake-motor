"""Validadores especializados del Classification Quality Framework."""

from __future__ import annotations

from zovrake_motor.classification.classification_quality.enums import (
    QualityValidationCategory,
    QualityValidatorStrategyType,
)
from zovrake_motor.classification.classification_quality.gateway import ComparativeDomainModelCatalogView
from zovrake_motor.classification.classification_quality.models import (
    QualityValidationCheck,
    QualityValidationFinding,
    QualityValidatorResult,
)
from zovrake_motor.classification.classification_quality.port import QualityValidatorPort
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings

VALID_GROUP_TYPES = frozenset({"material", "service"})
PM5_FUNCTIONAL_COMPONENTS = frozenset(
    {
        "concept_analysis_engine",
        "material_classification_engine",
        "service_classification_engine",
        "concept_normalization_engine",
        "equivalence_detection_engine",
        "comparable_group_builder",
        "context_association_engine",
        "comparative_domain_model_builder",
        "classification_quality_framework",
    },
)


class ModelConsistencyValidator(QualityValidatorPort):
    """Verifica consistencia interna del Modelo Comparativo."""

    @property
    def validator_name(self) -> str:
        return "model_consistency_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Consistencia del Modelo"

    @property
    def validator_type(self) -> QualityValidatorStrategyType:
        return QualityValidatorStrategyType.MODEL_CONSISTENCY

    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []

        contract_ok = catalog_view.pm6_output_contract
        checks.append(
            QualityValidationCheck(
                validator_name=self.validator_name,
                category=QualityValidationCategory.CONSISTENCY,
                check_name="pm6_output_contract",
                passed=contract_ok,
                message="Contrato PM6 activo en catálogo" if contract_ok else "Contrato PM6 ausente",
                target_id=catalog_view.catalog_id,
            ),
        )
        if not contract_ok:
            findings.append(
                QualityValidationFinding(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.CONSISTENCY,
                    message="El catálogo no declara contrato de salida PM6",
                    severity="error",
                    target_id=catalog_view.catalog_id,
                ),
            )

        for model in catalog_view.models:
            model_id = str(model.get("comparative_model_id", ""))
            group_type = str(model.get("group_type", ""))
            group_id = str(model.get("group_id", ""))
            traceability = model.get("traceability", {})
            related_context = model.get("related_context", {})

            type_ok = group_type in VALID_GROUP_TYPES
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.CONSISTENCY,
                    check_name="group_type_valid",
                    passed=type_ok,
                    message=f"Tipo de grupo válido: {group_type}" if type_ok else f"Tipo inválido: {group_type}",
                    target_id=model_id,
                ),
            )
            if not type_ok:
                findings.append(
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.CONSISTENCY,
                        message=f"Tipo de grupo inconsistente: {group_type}",
                        severity="error",
                        target_id=model_id,
                    ),
                )

            group_match = str(traceability.get("group_id", "")) == group_id
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.CONSISTENCY,
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
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.CONSISTENCY,
                        message="Inconsistencia entre group_id y trazabilidad",
                        severity="error",
                        target_id=model_id,
                    ),
                )

            context_ok = bool(related_context.get("description"))
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.CONSISTENCY,
                    check_name="related_context_present",
                    passed=context_ok,
                    message="Contexto relacionado presente"
                    if context_ok
                    else "Contexto relacionado ausente",
                    target_id=model_id,
                ),
            )
            if not context_ok and settings.require_related_context:
                findings.append(
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.CONSISTENCY,
                        message="Modelo sin contexto relacionado",
                        severity="warning",
                        target_id=model_id,
                    ),
                )

        return QualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"models_validated={len(catalog_view.models)}",),
        )


class DataIntegrityValidator(QualityValidatorPort):
    """Verifica integridad de identificadores, referencias y metadatos."""

    @property
    def validator_name(self) -> str:
        return "data_integrity_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Integridad de Datos"

    @property
    def validator_type(self) -> QualityValidatorStrategyType:
        return QualityValidatorStrategyType.DATA_INTEGRITY

    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []

        required_catalog_fields = (
            "catalog_id",
            "process_id",
            "model_id",
            "document_id",
            "source_context_association_catalog_id",
        )
        for field_name in required_catalog_fields:
            value = catalog_view.raw_catalog.get(field_name)
            passed = bool(value)
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.INTEGRITY,
                    check_name=f"catalog_field_{field_name}",
                    passed=passed,
                    message=f"Campo {field_name} presente" if passed else f"Campo {field_name} ausente",
                    target_id=catalog_view.catalog_id,
                ),
            )
            if not passed:
                findings.append(
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.INTEGRITY,
                        message=f"Campo obligatorio ausente en catálogo: {field_name}",
                        severity="error",
                        target_id=catalog_view.catalog_id,
                    ),
                )

        model_required = (
            "comparative_model_id",
            "group_id",
            "group_type",
            "primary_item",
            "equivalent_concepts",
            "traceability",
            "related_context",
        )
        for model in catalog_view.models:
            model_id = str(model.get("comparative_model_id", "unknown"))
            for field_name in model_required:
                value = model.get(field_name)
                passed = value is not None and value != "" and value != []
                checks.append(
                    QualityValidationCheck(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.INTEGRITY,
                        check_name=f"model_field_{field_name}",
                        passed=passed,
                        message=f"Campo {field_name} presente en modelo"
                        if passed
                        else f"Campo {field_name} ausente en modelo",
                        target_id=model_id,
                    ),
                )
                if not passed:
                    findings.append(
                        QualityValidationFinding(
                            validator_name=self.validator_name,
                            category=QualityValidationCategory.INTEGRITY,
                            message=f"Campo obligatorio ausente en modelo: {field_name}",
                            severity="error",
                            target_id=model_id,
                        ),
                    )

        preserved_ok = catalog_view.source_data_preserved
        checks.append(
            QualityValidationCheck(
                validator_name=self.validator_name,
                category=QualityValidationCategory.INTEGRITY,
                check_name="source_data_preserved",
                passed=preserved_ok,
                message="Datos de origen preservados" if preserved_ok else "Datos de origen no preservados",
                target_id=catalog_view.catalog_id,
            ),
        )

        return QualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=("integrity_checks_executed",),
        )


class IdentifierUniquenessValidator(QualityValidatorPort):
    """Verifica unicidad de identificadores y grupos."""

    @property
    def validator_name(self) -> str:
        return "identifier_uniqueness_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Unicidad de Identificadores"

    @property
    def validator_type(self) -> QualityValidatorStrategyType:
        return QualityValidatorStrategyType.IDENTIFIER_UNIQUENESS

    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []

        comparative_ids: list[str] = []
        internal_ids: list[str] = []
        group_ids: list[str] = []

        for model in catalog_view.models:
            comparative_ids.append(str(model.get("comparative_model_id", "")))
            internal_ids.append(str(model.get("internal_model_id", "")))
            group_ids.append(str(model.get("group_id", "")))

        for label, values in (
            ("comparative_model_id", comparative_ids),
            ("internal_model_id", internal_ids),
            ("group_id", group_ids),
        ):
            unique = len(values) == len(set(values))
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.UNIQUENESS,
                    check_name=f"{label}_unique",
                    passed=unique,
                    message=f"Identificadores {label} únicos"
                    if unique
                    else f"Identificadores {label} duplicados detectados",
                    target_id=catalog_view.catalog_id,
                ),
            )
            if not unique:
                findings.append(
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.UNIQUENESS,
                        message=f"Identificadores duplicados: {label}",
                        severity="error",
                        target_id=catalog_view.catalog_id,
                    ),
                )

        return QualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"models_checked={len(catalog_view.models)}",),
        )


class TraceabilityChainValidator(QualityValidatorPort):
    """Verifica cadena completa de trazabilidad."""

    @property
    def validator_name(self) -> str:
        return "traceability_chain_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Trazabilidad"

    @property
    def validator_type(self) -> QualityValidatorStrategyType:
        return QualityValidatorStrategyType.TRACEABILITY_CHAIN

    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []

        traceability_fields = (
            "source_context_association_catalog_id",
            "source_comparable_group_catalog_id",
            "document_reference",
            "canonical_reference",
            "equivalence_ids",
            "concept_ids",
            "normalized_concept_ids",
        )

        for model in catalog_view.models:
            model_id = str(model.get("comparative_model_id", "unknown"))
            traceability = model.get("traceability", {})

            for field_name in traceability_fields:
                value = traceability.get(field_name)
                passed = value is not None and value != "" and value != []
                checks.append(
                    QualityValidationCheck(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.TRACEABILITY,
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
                        QualityValidationFinding(
                            validator_name=self.validator_name,
                            category=QualityValidationCategory.TRACEABILITY,
                            message=f"Referencia de trazabilidad ausente: {field_name}",
                            severity="warning",
                            target_id=model_id,
                        ),
                    )

            original_ok = bool(traceability.get("original_preserved", False))
            context_ok = bool(traceability.get("context_preserved", False))
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.TRACEABILITY,
                    check_name="original_preserved",
                    passed=original_ok,
                    message="Original preservado" if original_ok else "Original no preservado",
                    target_id=model_id,
                ),
            )
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.TRACEABILITY,
                    check_name="context_preserved",
                    passed=context_ok,
                    message="Contexto preservado" if context_ok else "Contexto no preservado",
                    target_id=model_id,
                ),
            )

        return QualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"traceability_models_checked={len(catalog_view.models)}",),
        )


class PipelineFlowValidator(QualityValidatorPort):
    """Verifica que el flujo del Pipeline PM5 esté completo y coherente."""

    @property
    def validator_name(self) -> str:
        return "pipeline_flow_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Flujo del Pipeline"

    @property
    def validator_type(self) -> QualityValidatorStrategyType:
        return QualityValidatorStrategyType.PIPELINE_FLOW

    def validate(
        self,
        catalog_view: ComparativeDomainModelCatalogView,
        *,
        settings: ClassificationQualityFrameworkSettings,
    ) -> QualityValidatorResult:
        checks: list[QualityValidationCheck] = []
        findings: list[QualityValidationFinding] = []

        if not catalog_view.pipeline_snapshot:
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.PIPELINE,
                    check_name="pipeline_snapshot_provided",
                    passed=not settings.require_pipeline_snapshot,
                    message="Snapshot del pipeline no proporcionado",
                    target_id=catalog_view.catalog_id,
                ),
            )
            if settings.require_pipeline_snapshot:
                findings.append(
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.PIPELINE,
                        message="Snapshot del pipeline requerido pero no proporcionado",
                        severity="warning",
                        target_id=catalog_view.catalog_id,
                    ),
                )
            return QualityValidatorResult(
                validator_type=self.validator_type.value,
                validator_name=self.validator_name,
                checks=tuple(checks),
                findings=tuple(findings),
                technical_observations=("pipeline_snapshot_missing",),
            )

        ready_components = {
            str(stage.get("component_name"))
            for stage in catalog_view.pipeline_snapshot
            if stage.get("component_ready") is True and stage.get("component_name")
        }

        for component_name in PM5_FUNCTIONAL_COMPONENTS:
            if component_name == "classification_quality_framework":
                continue
            passed = component_name in ready_components
            checks.append(
                QualityValidationCheck(
                    validator_name=self.validator_name,
                    category=QualityValidationCategory.PIPELINE,
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
                    QualityValidationFinding(
                        validator_name=self.validator_name,
                        category=QualityValidationCategory.PIPELINE,
                        message=f"Componente del pipeline no listo: {component_name}",
                        severity="warning",
                        target_id=component_name,
                    ),
                )

        domain_stage = next(
            (
                stage
                for stage in catalog_view.pipeline_snapshot
                if stage.get("phase") == "modelo_dominio"
            ),
            None,
        )
        domain_ready = domain_stage is not None and domain_stage.get("component_ready") is True
        checks.append(
            QualityValidationCheck(
                validator_name=self.validator_name,
                category=QualityValidationCategory.PIPELINE,
                check_name="domain_model_stage_ready",
                passed=domain_ready,
                message="Etapa MODELO_DOMINIO lista" if domain_ready else "Etapa MODELO_DOMINIO no lista",
                target_id="modelo_dominio",
            ),
        )

        return QualityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            checks=tuple(checks),
            findings=tuple(findings),
            technical_observations=(f"pipeline_stages_checked={len(catalog_view.pipeline_snapshot)}",),
        )
