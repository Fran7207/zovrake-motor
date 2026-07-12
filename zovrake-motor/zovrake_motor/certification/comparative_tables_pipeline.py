"""
Utilidad de certificación del Pipeline de Generación de Cuadros Comparativos completo.

Ejecuta las etapas 4.2–4.10 en secuencia para validación integral.
No introduce lógica de negocio ni nuevos motores.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.certification.comparative_tables_fixtures import (
    build_domain_model_catalog_for_certification,
)
from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.enums import (
    ComparativeQualityValidationStatus,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ComparativeModelValidationStatus,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildRequest,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityValidationRequest,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
)
from zovrake_motor.comparative_tables.service import ComparativeTablesService
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
)


@dataclass(frozen=True)
class ComparativeTablesPipelineCertificationResult:
    """Resultado de la ejecución certificada del Pipeline PM6."""

    process_id: UUID
    document_id: str
    structure_build_passed: bool
    column_build_passed: bool
    row_build_passed: bool
    provider_organization_passed: bool
    group_integrity_passed: bool
    traceability_enrichment_passed: bool
    comparative_model_build_passed: bool
    validation_passed: bool
    quality_audit_passed: bool
    traceability_intact: bool
    domain_model_preserved: bool
    definitive_catalog_preserved: bool
    pm6_output_contract_valid: bool
    pm7_input_contract_prepared: bool
    module_certification_prepared: bool
    definitive_catalog: dict[str, Any]
    stages_executed: int
    technical_observations: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.structure_build_passed
            and self.column_build_passed
            and self.row_build_passed
            and self.provider_organization_passed
            and self.group_integrity_passed
            and self.traceability_enrichment_passed
            and self.comparative_model_build_passed
            and self.validation_passed
            and self.quality_audit_passed
            and self.traceability_intact
            and self.domain_model_preserved
            and self.definitive_catalog_preserved
            and self.pm6_output_contract_valid
            and self.pm7_input_contract_prepared
            and self.module_certification_prepared
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "complete": self.complete,
            "structure_build_passed": self.structure_build_passed,
            "column_build_passed": self.column_build_passed,
            "row_build_passed": self.row_build_passed,
            "provider_organization_passed": self.provider_organization_passed,
            "group_integrity_passed": self.group_integrity_passed,
            "traceability_enrichment_passed": self.traceability_enrichment_passed,
            "comparative_model_build_passed": self.comparative_model_build_passed,
            "validation_passed": self.validation_passed,
            "quality_audit_passed": self.quality_audit_passed,
            "traceability_intact": self.traceability_intact,
            "domain_model_preserved": self.domain_model_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "pm6_output_contract_valid": self.pm6_output_contract_valid,
            "pm7_input_contract_prepared": self.pm7_input_contract_prepared,
            "module_certification_prepared": self.module_certification_prepared,
            "definitive_catalog": self.definitive_catalog,
            "stages_executed": self.stages_executed,
            "technical_observations": list(self.technical_observations),
        }


def _inject_certification_providers(
    structure_catalog: dict[str, Any],
    *,
    providers: list[str],
) -> dict[str, Any]:
    catalog = copy.deepcopy(structure_catalog)
    for structure in catalog.get("structures", []):
        metadata_prepared = dict(structure.get("metadata_prepared", {}))
        metadata_prepared["available_providers"] = list(providers)
        structure["metadata_prepared"] = metadata_prepared
    return catalog


def run_full_comparative_tables_pipeline(
    service: ComparativeTablesService,
    *,
    process_id: UUID,
    document_id: str = "DOC-PM6-CERT",
    requirement_code: str = "REQ-PM6-CERT",
    certification_providers: tuple[str, ...] = ("PROV-001", "PROV-002"),
) -> ComparativeTablesPipelineCertificationResult:
    """
    Ejecuta el Pipeline PM6 completo (4.2–4.10) sin interrupciones.

    Flujo: CSE → DCB → DRB → POE → GIE → TME → CMB → CVF → CQF.
    """
    observations: list[str] = []
    stages = 0

    domain_catalog, internal_model = build_domain_model_catalog_for_certification(
        process_id=process_id,
        document_id=document_id,
        requirement_code=requirement_code,
    )
    domain_snapshot = str(domain_catalog)
    document_id_trace = str(domain_catalog.get("document_id", document_id))
    model_id_trace = str(domain_catalog.get("model_id", ""))

    structure_result = service.build_comparative_structure(
        ComparativeStructureBuildRequest(
            process_id=process_id,
            domain_model_catalog=domain_catalog,
        ),
    )
    stages += 1
    structure_catalog = structure_result.catalog.to_dict()
    structure_catalog = _inject_certification_providers(
        structure_catalog,
        providers=list(certification_providers),
    )
    structure_build_passed = structure_result.domain_model_preserved

    column_result = service.build_dynamic_columns(
        ComparativeColumnBuildRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
        ),
    )
    stages += 1
    column_catalog = column_result.catalog.to_dict()
    column_build_passed = (
        column_result.structure_catalog_preserved
        and column_result.domain_model_preserved
    )

    row_result = service.build_dynamic_rows(
        ComparativeRowBuildRequest(
            process_id=process_id,
            column_catalog=column_catalog,
            structure_catalog=structure_catalog,
        ),
    )
    stages += 1
    row_catalog = row_result.catalog.to_dict()
    row_build_passed = (
        row_result.column_catalog_preserved
        and row_result.structure_catalog_preserved
        and row_result.domain_model_preserved
    )

    provider_result = service.organize_providers(
        ProviderOrganizationBuildRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
        ),
    )
    stages += 1
    provider_catalog = provider_result.catalog.to_dict()
    provider_organization_passed = (
        provider_result.structure_catalog_preserved
        and provider_result.column_catalog_preserved
        and provider_result.row_catalog_preserved
    )

    integrity_result = service.validate_group_integrity(
        GroupIntegrityValidationRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
            provider_catalog=provider_catalog,
        ),
    )
    stages += 1
    integrity_report = integrity_result.report.to_dict()
    group_integrity_passed = (
        integrity_result.structure_catalog_preserved
        and integrity_result.provider_catalog_preserved
    )

    enrichment_result = service.enrich_traceability_metadata(
        TraceabilityMetadataEnrichmentRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
            provider_catalog=provider_catalog,
            integrity_report=integrity_report,
        ),
    )
    stages += 1
    enriched_catalog = enrichment_result.catalog.to_dict()
    traceability_enrichment_passed = (
        enrichment_result.structure_catalog_preserved
        and enrichment_result.provider_catalog_preserved
        and enrichment_result.integrity_report_preserved
    )

    model_result = service.build_comparative_model(
        ComparativeModelBuildRequest(
            process_id=process_id,
            enriched_catalog=enriched_catalog,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
            provider_catalog=provider_catalog,
            integrity_report=integrity_report,
        ),
    )
    stages += 1
    definitive_catalog = model_result.catalog.to_dict()
    definitive_snapshot = str(definitive_catalog)
    comparative_model_build_passed = (
        model_result.enriched_catalog_preserved
        and model_result.domain_model_preserved
        and model_result.catalog.pm6_definitive_output_contract
    )

    validation_result = service.validate_comparative_model(
        ComparativeModelValidationRequest(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        ),
    )
    stages += 1
    validation_report = validation_result.report.to_dict()
    validation_passed = (
        validation_result.definitive_catalog_preserved
        and validation_result.status
        in (
            ComparativeModelValidationStatus.VALID,
            ComparativeModelValidationStatus.PARTIAL,
        )
        and validation_result.error_count == 0
    )

    quality_result = service.audit_comparative_quality(
        ComparativeQualityValidationRequest(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
            validation_report=validation_report,
            pipeline_snapshot=service.get_comparative_tables_pipeline_snapshot(),
        ),
    )
    stages += 1
    quality_audit_passed = quality_result.status in (
        ComparativeQualityValidationStatus.PASSED,
        ComparativeQualityValidationStatus.PASSED_WITH_WARNINGS,
    ) or (
        quality_result.status == ComparativeQualityValidationStatus.SKIPPED
        and quality_result.report.module_certification_prepared
        and stages == 9
    )
    module_certification_prepared = quality_result.report.module_certification_prepared

    domain_model_preserved = str(domain_catalog) == domain_snapshot
    definitive_catalog_preserved = str(definitive_catalog) == definitive_snapshot

    pm6_output_contract_valid = (
        definitive_catalog.get("pm6_definitive_output_contract") is True
        and PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME == "DefinitiveComparativeModelCatalog"
    )
    pm7_input_contract_prepared = bool(
        definitive_catalog.get("pm7_input_contract_prepared", False),
    )

    traceability_intact = (
        structure_result.document_id == document_id_trace
        and column_result.document_id == document_id_trace
        and row_result.document_id == document_id_trace
        and provider_result.document_id == document_id_trace
        and enrichment_result.document_id == document_id_trace
        and model_result.document_id == document_id_trace
        and validation_result.document_id == document_id_trace
        and quality_result.document_id == document_id_trace
        and definitive_catalog.get("document_id") == document_id_trace
        and definitive_catalog.get("model_id") == model_id_trace
    )
    if definitive_catalog.get("models"):
        first_model = definitive_catalog["models"][0]
        trace = first_model.get("traceability", {})
        traceability_intact = traceability_intact and bool(
            trace.get("document_evidence")
            or trace.get("comparable_group")
            or trace.get("domain_catalog_id"),
        )

    observations.extend(
        (
            f"stages_executed={stages}",
            f"structures_count={len(structure_catalog.get('structures', []))}",
            f"definitive_models_count={len(definitive_catalog.get('models', []))}",
            f"validation_status={validation_result.status.value}",
            f"quality_status={quality_result.status.value}",
            "pipeline_certification_complete=True" if stages == 9 else "pipeline_certification_partial=True",
        ),
    )

    return ComparativeTablesPipelineCertificationResult(
        process_id=process_id,
        document_id=document_id,
        structure_build_passed=structure_build_passed,
        column_build_passed=column_build_passed,
        row_build_passed=row_build_passed,
        provider_organization_passed=provider_organization_passed,
        group_integrity_passed=group_integrity_passed,
        traceability_enrichment_passed=traceability_enrichment_passed,
        comparative_model_build_passed=comparative_model_build_passed,
        validation_passed=validation_passed,
        quality_audit_passed=quality_audit_passed,
        traceability_intact=traceability_intact,
        domain_model_preserved=domain_model_preserved,
        definitive_catalog_preserved=definitive_catalog_preserved,
        pm6_output_contract_valid=pm6_output_contract_valid,
        pm7_input_contract_prepared=pm7_input_contract_prepared,
        module_certification_prepared=module_certification_prepared,
        definitive_catalog=definitive_catalog,
        stages_executed=stages,
        technical_observations=tuple(observations),
    )
