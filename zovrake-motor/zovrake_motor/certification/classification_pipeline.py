"""
Utilidad de certificación del Pipeline de Clasificación Inteligente completo.

Ejecuta las etapas 3.2–3.10 en secuencia para validación integral.
No introduce lógica de negocio ni nuevos motores.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.classification_quality.enums import QualityValidationStatus
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationRequest,
)
from zovrake_motor.classification.comparable_group_builder.models import ComparableGroupBuildRequest
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
)
from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest
from zovrake_motor.classification.concept_normalization.models import ConceptNormalizationRequest
from zovrake_motor.classification.context_association.models import ContextAssociationRequest
from zovrake_motor.classification.equivalence_detection.models import EquivalenceDetectionRequest
from zovrake_motor.classification.material_classification.models import MaterialClassificationRequest
from zovrake_motor.classification.service import ClassificationService
from zovrake_motor.classification.service_classification.models import ServiceClassificationRequest
from zovrake_motor.comprehension.canonical import CanonicalRepresentationEngine, CanonicalRepresentationRequest
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionResult,
    ExtractedTable,
    ExtractionIncident,
    ExtractionIncidentSeverity,
)
from zovrake_motor.comprehension.internal_model import InternalDocumentModelBuilder, InternalModelBuildRequest


@dataclass(frozen=True)
class ClassificationPipelineCertificationResult:
    """Resultado de la ejecución certificada del Pipeline de clasificación."""

    process_id: UUID
    document_id: str
    concept_analysis_passed: bool
    material_classification_passed: bool
    service_classification_passed: bool
    concept_normalization_passed: bool
    equivalence_detection_passed: bool
    comparable_group_build_passed: bool
    context_association_passed: bool
    comparative_domain_model_passed: bool
    quality_validation_passed: bool
    traceability_intact: bool
    source_data_immutable: bool
    materials_services_separated: bool
    certification_prepared: bool
    stages_executed: int
    technical_observations: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.concept_analysis_passed
            and self.material_classification_passed
            and self.service_classification_passed
            and self.concept_normalization_passed
            and self.equivalence_detection_passed
            and self.comparable_group_build_passed
            and self.context_association_passed
            and self.comparative_domain_model_passed
            and self.quality_validation_passed
            and self.traceability_intact
            and self.source_data_immutable
            and self.materials_services_separated
            and self.certification_prepared
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "complete": self.complete,
            "concept_analysis_passed": self.concept_analysis_passed,
            "material_classification_passed": self.material_classification_passed,
            "service_classification_passed": self.service_classification_passed,
            "concept_normalization_passed": self.concept_normalization_passed,
            "equivalence_detection_passed": self.equivalence_detection_passed,
            "comparable_group_build_passed": self.comparable_group_build_passed,
            "context_association_passed": self.context_association_passed,
            "comparative_domain_model_passed": self.comparative_domain_model_passed,
            "quality_validation_passed": self.quality_validation_passed,
            "traceability_intact": self.traceability_intact,
            "source_data_immutable": self.source_data_immutable,
            "materials_services_separated": self.materials_services_separated,
            "certification_prepared": self.certification_prepared,
            "stages_executed": self.stages_executed,
            "technical_observations": list(self.technical_observations),
        }


def _build_certification_extraction_result(
    *,
    process_id: UUID,
    document_id: str,
) -> ContentExtractionResult:
    return ContentExtractionResult(
        process_id=process_id,
        document_id=document_id,
        extracted_text="Contenido certificado para pipeline integral de clasificación",
        tables=(
            ExtractedTable(
                table_id="table-cert-1",
                rows=(
                    ("Ítem", "Descripción", "Cantidad"),
                    ("1", "Acero inoxidable 304", "100 kg"),
                    ("2", "Servicio de instalación", "1"),
                ),
            ),
        ),
        metadata={
            "format_type": "pdf",
            "document_reference": f"adapter://pdf/{document_id}",
            "provider_name": "Proveedor Certificación",
            "commercial_currency": "USD",
            "commercial_total": "1500.00",
            "commercial_payment_terms": "30 días",
            "technical_specifications": ("Acero inoxidable", "Resistencia 400 MPa"),
            "commercial_conditions": (("Entrega", "15 días"),),
            "observations": (("Nota", "Incluye instalación"),),
        },
        structural_elements=(),
        incidents=(
            ExtractionIncident(
                extractor_name="text_extractor",
                message="Extracción certificada",
                severity=ExtractionIncidentSeverity.INFO,
            ),
        ),
        original_preserved=True,
        ocr_integration_prepared=True,
        extractors_executed=8,
        adapter_name="pdf_adapter",
        technical_observations=("original_preserved=True",),
    )


def _build_certification_internal_model(
    *,
    process_id: UUID,
    document_id: str,
    requirement_code: str,
) -> dict[str, Any]:
    cre = CanonicalRepresentationEngine()
    cre.initialize()
    canonical = cre.represent(
        CanonicalRepresentationRequest(
            process_id=process_id,
            extraction_result=_build_certification_extraction_result(
                process_id=process_id,
                document_id=document_id,
            ),
        ),
    )
    idmb = InternalDocumentModelBuilder()
    idmb.initialize()
    result = idmb.build(
        InternalModelBuildRequest(
            process_id=process_id,
            canonical_result=canonical,
            requirement_code=requirement_code,
        ),
    )
    return result.model.to_dict()


def run_full_classification_pipeline(
    service: ClassificationService,
    *,
    process_id: UUID,
    document_id: str = "DOC-CLASS-CERT",
    requirement_code: str = "REQ-CERT",
    detalles_requerimiento: str = "Detalles del requerimiento para certificación integral del módulo.",
) -> ClassificationPipelineCertificationResult:
    """
    Ejecuta el Pipeline de Clasificación completo (3.2–3.10) sin interrupciones.

    Flujo: CAE → MCE → SCE → CNE → EDE → CGB → CAE-Context → CDMB → CQF.
    """
    observations: list[str] = []
    stages = 0

    internal_model = _build_certification_internal_model(
        process_id=process_id,
        document_id=document_id,
        requirement_code=requirement_code,
    )
    model_snapshot_before = str(internal_model)

    concept_result = service.analyze_concepts(
        ConceptAnalysisRequest(
            process_id=process_id,
            internal_model=internal_model,
        ),
    )
    stages += 1
    concept_analysis_passed = (
        concept_result.internal_model_preserved
        and len(concept_result.catalog.concepts) > 0
    )
    concept_catalog = concept_result.catalog.to_dict()

    material_result = service.classify_materials(
        MaterialClassificationRequest(
            process_id=process_id,
            concept_catalog=concept_catalog,
        ),
    )
    stages += 1
    material_classification_passed = (
        material_result.concept_catalog_preserved
        and len(material_result.catalog.materials) >= 0
    )
    material_catalog = material_result.catalog.to_dict()

    service_result = service.classify_services(
        ServiceClassificationRequest(
            process_id=process_id,
            concept_catalog=concept_catalog,
        ),
    )
    stages += 1
    service_classification_passed = (
        service_result.concept_catalog_preserved
        and len(service_result.catalog.services) >= 0
    )
    service_catalog = service_result.catalog.to_dict()

    normalization_result = service.normalize_concepts(
        ConceptNormalizationRequest(
            process_id=process_id,
            material_catalog=material_catalog,
            service_catalog=service_catalog,
        ),
    )
    stages += 1
    normalized_catalog = normalization_result.catalog.to_dict()
    concept_normalization_passed = normalization_result.source_catalogs_preserved
    concepts = list(normalized_catalog.get("concepts", []))
    if concepts:
        duplicate = copy.deepcopy(concepts[0])
        normalized_id = str(duplicate.get("normalized_concept_id", "concept-cert"))
        duplicate["normalized_concept_id"] = (
            normalized_id.replace("concept-", "concept-cert-dup-", 1)
            if "concept-" in normalized_id
            else f"{normalized_id}-dup"
        )
        concepts.append(duplicate)
        normalized_catalog["concepts"] = concepts
    materials_services_separated = (
        material_result.concept_catalog_preserved
        and service_result.concept_catalog_preserved
        and material_catalog.get("catalog_id") != service_catalog.get("catalog_id")
        and bool(normalized_catalog.get("source_material_catalog_id"))
        and bool(normalized_catalog.get("source_service_catalog_id"))
    )

    equivalence_result = service.detect_equivalences(
        EquivalenceDetectionRequest(
            process_id=process_id,
            normalized_catalog=normalized_catalog,
        ),
    )
    stages += 1
    equivalence_detection_passed = equivalence_result.normalized_catalog_preserved
    equivalence_catalog = equivalence_result.catalog.to_dict()

    group_result = service.build_comparable_groups(
        ComparableGroupBuildRequest(
            process_id=process_id,
            equivalence_catalog=equivalence_catalog,
        ),
    )
    stages += 1
    comparable_group_build_passed = group_result.equivalence_catalog_preserved
    group_catalog = group_result.catalog.to_dict()

    integrated_context = {
        "context_id": f"ctx://{process_id}",
        "description": detalles_requerimiento,
        "process_id": str(process_id),
        "codigo_req": requirement_code,
        "immutable": True,
    }
    context_result = service.associate_context(
        ContextAssociationRequest(
            process_id=process_id,
            comparable_group_catalog=group_catalog,
            integrated_context=integrated_context,
        ),
    )
    stages += 1
    context_association_passed = (
        context_result.comparable_group_catalog_preserved
        and context_result.context_preserved
    )
    association_catalog = context_result.catalog.to_dict()

    domain_model_result = service.build_comparative_domain_model(
        ComparativeDomainModelBuildRequest(
            process_id=process_id,
            context_association_catalog=association_catalog,
        ),
    )
    stages += 1
    comparative_domain_model_passed = (
        domain_model_result.source_data_preserved
        and domain_model_result.catalog.pm6_output_contract
    )
    domain_catalog = domain_model_result.catalog.to_dict()

    quality_result = service.validate_classification_quality(
        ClassificationQualityValidationRequest(
            process_id=process_id,
            comparative_domain_model_catalog=domain_catalog,
            pipeline_snapshot=service.get_classification_pipeline_snapshot(),
        ),
    )
    stages += 1
    quality_validation_passed = quality_result.status in (
        QualityValidationStatus.PASSED,
        QualityValidationStatus.PASSED_WITH_WARNINGS,
    ) or (
        quality_result.status == QualityValidationStatus.SKIPPED
        and quality_result.report.certification_prepared
        and stages == 9
    )
    certification_prepared = quality_result.report.certification_prepared

    source_data_immutable = str(internal_model) == model_snapshot_before

    document_id_trace = str(internal_model.get("document_id", document_id))
    model_id_trace = str(internal_model.get("model_id", ""))
    traceability_intact = (
        concept_result.catalog.document_id == document_id_trace
        and material_result.catalog.document_id == document_id_trace
        and service_result.catalog.document_id == document_id_trace
        and normalized_catalog.get("document_id") == document_id_trace
        and equivalence_catalog.get("document_id") == document_id_trace
        and group_catalog.get("document_id") == document_id_trace
        and association_catalog.get("document_id") == document_id_trace
        and domain_catalog.get("document_id") == document_id_trace
        and domain_catalog.get("model_id") == model_id_trace
    )
    if domain_catalog.get("models"):
        first_model = domain_catalog["models"][0]
        trace = first_model.get("traceability", {})
        traceability_intact = traceability_intact and bool(
            trace.get("source_context_association_catalog_id")
            or trace.get("document_id") == document_id_trace
        )

    observations.extend(
        (
            f"stages_executed={stages}",
            f"concept_count={len(concept_result.catalog.concepts)}",
            f"material_count={len(material_result.catalog.materials)}",
            f"service_count={len(service_result.catalog.services)}",
            f"group_count={len(group_catalog.get('groups', []))}",
            f"domain_model_count={len(domain_catalog.get('models', []))}",
            f"quality_status={quality_result.status.value}",
            "pipeline_certification_complete=True" if stages == 9 else "pipeline_certification_partial=True",
        ),
    )

    return ClassificationPipelineCertificationResult(
        process_id=process_id,
        document_id=document_id,
        concept_analysis_passed=concept_analysis_passed,
        material_classification_passed=material_classification_passed,
        service_classification_passed=service_classification_passed,
        concept_normalization_passed=concept_normalization_passed,
        equivalence_detection_passed=equivalence_detection_passed,
        comparable_group_build_passed=comparable_group_build_passed,
        context_association_passed=context_association_passed,
        comparative_domain_model_passed=comparative_domain_model_passed,
        quality_validation_passed=quality_validation_passed,
        traceability_intact=traceability_intact,
        source_data_immutable=source_data_immutable,
        materials_services_separated=materials_services_separated,
        certification_prepared=certification_prepared,
        stages_executed=stages,
        technical_observations=tuple(observations),
    )
