"""Utilidades de normalización textual y construcción de conceptos normalizados."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from zovrake_motor.classification.concept_normalization.enums import (
    ConceptNormalizationStatus,
    NormalizedConceptCategory,
)
from zovrake_motor.classification.concept_normalization.gateway import (
    ClassificationCatalogView,
)
from zovrake_motor.classification.concept_normalization.models import (
    NormalizedConceptCatalog,
    NormalizedConceptRecord,
    NormalizedConceptTraceability,
    NormalizedModelReference,
)
from zovrake_motor.classification.material_classification.models import (
    MaterialRecord,
)
from zovrake_motor.classification.service_classification.models import (
    ServiceRecord,
)


def normalize_text(value: str) -> str:
    """
    Normaliza texto para comparación homogénea.

    Conserva el valor original en el registro; esta función solamente
    produce la representación normalizada del texto.
    """
    if not value:
        return ""

    text = value.strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(
        r"[^\w\s./-]",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def build_normalized_concept_id(
    model_id: str,
    sequence: int,
) -> str:
    return (
        f"cne://{model_id}/concept-{sequence:04d}"
    )


def _build_normalization_metadata(
    source_metadata: dict[str, Any] | None,
    additional_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Construye metadata para el concepto normalizado sin perder evidencia.

    La normalización trabaja sobre una copia de la metadata de origen.
    Nunca modifica el catálogo de materiales o servicios recibido.

    Si existen valores semánticos provenientes de una tabla PDF, se
    conservan tanto en su forma original como en una vista normalizada.
    """
    metadata = dict(
        source_metadata or {}
    )

    raw_semantic_values = metadata.get(
        "semantic_values"
    )

    if not isinstance(
        raw_semantic_values,
        dict,
    ):
        fields = metadata.get(
            "fields"
        )

        if isinstance(
            fields,
            dict,
        ):
            candidate_values = fields.get(
                "values"
            )

            if isinstance(
                candidate_values,
                dict,
            ):
                raw_semantic_values = candidate_values

    if isinstance(
        raw_semantic_values,
        dict,
    ):
        semantic_values = dict(
            raw_semantic_values
        )

        metadata["semantic_values"] = (
            semantic_values
        )

        metadata[
            "normalized_semantic_values"
        ] = {
            str(key): normalize_text(
                str(value)
            )
            for key, value
            in semantic_values.items()
            if str(key).strip()
        }

    semantic_columns = metadata.get(
        "semantic_columns"
    )

    if isinstance(
        semantic_columns,
        (list, tuple),
    ):
        metadata["semantic_columns"] = tuple(
            str(column).strip()
            for column in semantic_columns
            if str(column).strip()
        )

    metadata[
        "source_metadata_preserved"
    ] = True

    if additional_metadata:
        metadata.update(
            additional_metadata
        )

    return metadata


def _build_traceability_from_material(
    *,
    catalog_view: ClassificationCatalogView,
    material: MaterialRecord,
) -> NormalizedConceptTraceability:
    traceability = material.traceability

    return NormalizedConceptTraceability(
        process_id=traceability.process_id,
        document_id=traceability.document_id,
        model_id=traceability.model_id,
        concept_id=material.concept_id,
        source_material_catalog_id=(
            catalog_view.material_catalog_id
        ),
        source_service_catalog_id=(
            catalog_view.service_catalog_id
        ),
        document_reference=(
            traceability.document_reference
        ),
        canonical_reference=(
            traceability.canonical_reference
        ),
        extraction_reference=(
            traceability.extraction_reference
        ),
        source_reference=(
            traceability.source_reference
        ),
        adapter_name=traceability.adapter_name,
        format_type=traceability.format_type,
        original_preserved=(
            traceability.original_preserved
        ),
    )


def _build_traceability_from_service(
    *,
    catalog_view: ClassificationCatalogView,
    service: ServiceRecord,
) -> NormalizedConceptTraceability:
    traceability = service.traceability

    return NormalizedConceptTraceability(
        process_id=traceability.process_id,
        document_id=traceability.document_id,
        model_id=traceability.model_id,
        concept_id=service.concept_id,
        source_material_catalog_id=(
            catalog_view.material_catalog_id
        ),
        source_service_catalog_id=(
            catalog_view.service_catalog_id
        ),
        document_reference=(
            traceability.document_reference
        ),
        canonical_reference=(
            traceability.canonical_reference
        ),
        extraction_reference=(
            traceability.extraction_reference
        ),
        source_reference=(
            traceability.source_reference
        ),
        adapter_name=traceability.adapter_name,
        format_type=traceability.format_type,
        original_preserved=(
            traceability.original_preserved
        ),
    )


def build_normalized_concept_from_material(
    *,
    catalog_view: ClassificationCatalogView,
    material: MaterialRecord,
    concept_type: str,
    sequence: int,
    original_value: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> NormalizedConceptRecord:
    original = (
        original_value
        if original_value is not None
        else material.original_name
    )

    source_metadata = dict(
        material.metadata
    )

    if metadata:
        source_metadata.update(
            metadata
        )

    return NormalizedConceptRecord(
        normalized_concept_id=(
            build_normalized_concept_id(
                catalog_view.model_id,
                sequence,
            )
        ),
        original_value=original,
        normalized_value=normalize_text(
            original
        ),
        concept_type=concept_type,
        source_category=(
            NormalizedConceptCategory.MATERIAL.value
        ),
        concept_id=material.concept_id,
        model_reference=NormalizedModelReference(
            model_id=material.model_reference.model_id,
            document_id=material.model_reference.document_id,
            concept_id=material.concept_id,
            source_record_id=material.material_id,
            source_category=(
                NormalizedConceptCategory.MATERIAL.value
            ),
        ),
        traceability=(
            _build_traceability_from_material(
                catalog_view=catalog_view,
                material=material,
            )
        ),
        status=(
            ConceptNormalizationStatus.NORMALIZED
        ),
        metadata=_build_normalization_metadata(
            source_metadata
        ),
    )


def build_normalized_concept_from_service(
    *,
    catalog_view: ClassificationCatalogView,
    service: ServiceRecord,
    concept_type: str,
    sequence: int,
    original_value: str | None = None,
    source_category: str = (
        NormalizedConceptCategory.SERVICE.value
    ),
    metadata: dict[str, Any] | None = None,
) -> NormalizedConceptRecord:
    original = (
        original_value
        if original_value is not None
        else service.original_name
    )

    source_metadata = dict(
        service.metadata
    )

    if metadata:
        source_metadata.update(
            metadata
        )

    return NormalizedConceptRecord(
        normalized_concept_id=(
            build_normalized_concept_id(
                catalog_view.model_id,
                sequence,
            )
        ),
        original_value=original,
        normalized_value=normalize_text(
            original
        ),
        concept_type=concept_type,
        source_category=source_category,
        concept_id=service.concept_id,
        model_reference=NormalizedModelReference(
            model_id=service.model_reference.model_id,
            document_id=service.model_reference.document_id,
            concept_id=service.concept_id,
            source_record_id=service.service_id,
            source_category=(
                NormalizedConceptCategory.SERVICE.value
            ),
        ),
        traceability=(
            _build_traceability_from_service(
                catalog_view=catalog_view,
                service=service,
            )
        ),
        status=(
            ConceptNormalizationStatus.NORMALIZED
        ),
        metadata=_build_normalization_metadata(
            source_metadata
        ),
    )


def build_normalized_concept_catalog(
    *,
    catalog_view: ClassificationCatalogView,
    concepts: tuple[NormalizedConceptRecord, ...],
    equivalence_detection_prepared: bool,
    comparable_group_builder_prepared: bool,
) -> NormalizedConceptCatalog:
    return NormalizedConceptCatalog(
        catalog_id=(
            f"cne-catalog://{catalog_view.model_id}"
        ),
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_material_catalog_id=(
            catalog_view.material_catalog_id
        ),
        source_service_catalog_id=(
            catalog_view.service_catalog_id
        ),
        concepts=concepts,
        equivalence_detection_prepared=(
            equivalence_detection_prepared
        ),
        comparable_group_builder_prepared=(
            comparable_group_builder_prepared
        ),
    )