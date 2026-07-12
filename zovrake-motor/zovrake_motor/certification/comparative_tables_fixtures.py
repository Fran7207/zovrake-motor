"""
Fixtures de certificación para el Módulo de Generación de Cuadros Comparativos.

Construye el Modelo Comparativo de Dominio (entrada PM5) sin modificar motores.
Reutiliza la cadena certificada del PM5 para garantizar grupos comparables válidos.
"""

from __future__ import annotations

import copy
from typing import Any
from uuid import UUID

from zovrake_motor.certification.classification_pipeline import _build_certification_internal_model
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


def _inject_certification_duplicate_concept(normalized_catalog: dict[str, Any]) -> dict[str, Any]:
    """Replica la inyección certificada del PM5 para generar equivalencias comparables."""
    catalog = copy.deepcopy(normalized_catalog)
    concepts = list(catalog.get("concepts", []))
    if not concepts:
        return catalog

    duplicate = copy.deepcopy(concepts[0])
    normalized_id = str(duplicate.get("normalized_concept_id", "concept-cert"))
    duplicate["normalized_concept_id"] = (
        normalized_id.replace("concept-", "concept-cert-dup-", 1)
        if "concept-" in normalized_id
        else f"{normalized_id}-dup"
    )
    concepts.append(duplicate)
    catalog["concepts"] = concepts
    return catalog


def build_domain_model_catalog_for_certification(
    *,
    process_id: UUID,
    document_id: str = "DOC-PM6-CERT",
    requirement_code: str = "REQ-PM6-CERT",
    detalles_requerimiento: str = "Detalles del requerimiento para certificación integral PM6.",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Construye el Modelo Comparativo de Dominio y devuelve también el IDMB de referencia.

    Retorna (domain_catalog, internal_model_snapshot).
    """
    internal_model = _build_certification_internal_model(
        process_id=process_id,
        document_id=document_id,
        requirement_code=requirement_code,
    )

    service = ClassificationService()
    service.initialize()

    concept_result = service.analyze_concepts(
        ConceptAnalysisRequest(process_id=process_id, internal_model=internal_model),
    )
    concept_catalog = concept_result.catalog.to_dict()

    material_result = service.classify_materials(
        MaterialClassificationRequest(process_id=process_id, concept_catalog=concept_catalog),
    )
    material_catalog = material_result.catalog.to_dict()

    service_result = service.classify_services(
        ServiceClassificationRequest(process_id=process_id, concept_catalog=concept_catalog),
    )
    service_catalog = service_result.catalog.to_dict()

    normalization_result = service.normalize_concepts(
        ConceptNormalizationRequest(
            process_id=process_id,
            material_catalog=material_catalog,
            service_catalog=service_catalog,
        ),
    )
    normalized_catalog = _inject_certification_duplicate_concept(
        normalization_result.catalog.to_dict(),
    )

    equivalence_result = service.detect_equivalences(
        EquivalenceDetectionRequest(
            process_id=process_id,
            normalized_catalog=normalized_catalog,
        ),
    )
    equivalence_catalog = equivalence_result.catalog.to_dict()

    group_result = service.build_comparable_groups(
        ComparableGroupBuildRequest(
            process_id=process_id,
            equivalence_catalog=equivalence_catalog,
        ),
    )
    group_catalog = group_result.catalog.to_dict()

    context_result = service.associate_context(
        ContextAssociationRequest(
            process_id=process_id,
            comparable_group_catalog=group_catalog,
            integrated_context={
                "context_id": f"ctx://{process_id}",
                "description": detalles_requerimiento,
                "process_id": str(process_id),
                "codigo_req": requirement_code,
                "immutable": True,
            },
        ),
    )
    association_catalog = context_result.catalog.to_dict()

    domain_result = service.build_comparative_domain_model(
        ComparativeDomainModelBuildRequest(
            process_id=process_id,
            context_association_catalog=association_catalog,
        ),
    )
    return domain_result.catalog.to_dict(), internal_model
