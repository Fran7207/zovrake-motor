"""Gateway de consumo de catálogos del MCE y SCE para normalización."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_normalization.exceptions import ClassificationCatalogAccessError
from zovrake_motor.classification.material_classification.enums import MaterialClassificationStatus
from zovrake_motor.classification.material_classification.models import (
    MaterialCatalog,
    MaterialCommercialInformation,
    MaterialModelReference,
    MaterialRecord,
    MaterialTechnicalInformation,
    MaterialTraceability,
)
from zovrake_motor.classification.service_classification.enums import ServiceClassificationStatus
from zovrake_motor.classification.service_classification.models import (
    ServiceCatalog,
    ServiceCommercialInformation,
    ServiceModelReference,
    ServiceRecord,
    ServiceTechnicalInformation,
    ServiceTraceability,
)


@dataclass(frozen=True)
class ClassificationCatalogView:
    """Vista de solo lectura de catálogos de materiales y servicios."""

    material_catalog_id: str
    service_catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    materials: tuple[MaterialRecord, ...]
    services: tuple[ServiceRecord, ...]
    raw_material_catalog: dict[str, Any]
    raw_service_catalog: dict[str, Any]


class ClassificationCatalogGateway:
    """
    Gateway de consumo de catálogos clasificados para el CNE.

    Valida preparación para normalización sin acceder al documento original.
    """

    MATERIAL_REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "materials",
    )
    SERVICE_REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "services",
    )

    def validate(
        self,
        material_catalog_dict: dict[str, Any],
        service_catalog_dict: dict[str, Any],
    ) -> ClassificationCatalogView:
        material_catalog = self._validate_material_catalog(material_catalog_dict)
        service_catalog = self._validate_service_catalog(service_catalog_dict)

        if material_catalog.process_id != service_catalog.process_id:
            raise ClassificationCatalogAccessError(
                "Los catálogos de materiales y servicios deben pertenecer al mismo proceso",
            )
        if material_catalog.model_id != service_catalog.model_id:
            raise ClassificationCatalogAccessError(
                "Los catálogos de materiales y servicios deben pertenecer al mismo modelo",
            )

        return ClassificationCatalogView(
            material_catalog_id=material_catalog.catalog_id,
            service_catalog_id=service_catalog.catalog_id,
            process_id=material_catalog.process_id,
            model_id=material_catalog.model_id,
            document_id=material_catalog.document_id,
            materials=material_catalog.materials,
            services=service_catalog.services,
            raw_material_catalog=material_catalog_dict,
            raw_service_catalog=service_catalog_dict,
        )

    def _validate_material_catalog(self, catalog_dict: dict[str, Any]) -> MaterialCatalog:
        if not isinstance(catalog_dict, dict):
            raise ClassificationCatalogAccessError("El catálogo de materiales debe ser un diccionario")

        missing = [field for field in self.MATERIAL_REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ClassificationCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo de materiales: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("normalization_prepared", True)):
            raise ClassificationCatalogAccessError(
                "El catálogo de materiales no está preparado para normalización",
            )

        materials_raw = catalog_dict.get("materials", [])
        if not isinstance(materials_raw, list):
            raise ClassificationCatalogAccessError("materials debe ser una lista")

        materials = tuple(self._parse_material(item) for item in materials_raw)
        return MaterialCatalog(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_concept_catalog_id=str(catalog_dict.get("source_concept_catalog_id", "")),
            materials=materials,
            normalization_prepared=True,
        )

    def _validate_service_catalog(self, catalog_dict: dict[str, Any]) -> ServiceCatalog:
        if not isinstance(catalog_dict, dict):
            raise ClassificationCatalogAccessError("El catálogo de servicios debe ser un diccionario")

        missing = [field for field in self.SERVICE_REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ClassificationCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo de servicios: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("normalization_prepared", True)):
            raise ClassificationCatalogAccessError(
                "El catálogo de servicios no está preparado para normalización",
            )

        services_raw = catalog_dict.get("services", [])
        if not isinstance(services_raw, list):
            raise ClassificationCatalogAccessError("services debe ser una lista")

        services = tuple(self._parse_service(item) for item in services_raw)
        return ServiceCatalog(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_concept_catalog_id=str(catalog_dict.get("source_concept_catalog_id", "")),
            services=services,
            normalization_prepared=True,
        )

    def _parse_material(self, payload: dict[str, Any]) -> MaterialRecord:
        if not isinstance(payload, dict):
            raise ClassificationCatalogAccessError("Cada material debe ser un diccionario")

        commercial_raw = payload.get("commercial_information", {})
        technical_raw = payload.get("technical_information", {})
        model_ref_raw = payload.get("model_reference", {})
        traceability_raw = payload.get("traceability", {})

        return MaterialRecord(
            material_id=str(payload["material_id"]),
            concept_id=str(payload["concept_id"]),
            original_name=str(payload.get("original_name", "")),
            description=str(payload.get("description", "")),
            unit=str(payload.get("unit", "")),
            quantity=str(payload.get("quantity", "")),
            commercial_information=MaterialCommercialInformation(
                unit_price=str(commercial_raw.get("unit_price", "")),
                currency=str(commercial_raw.get("currency", "")),
                fields=dict(commercial_raw.get("fields", {})),
            ),
            technical_information=MaterialTechnicalInformation(
                specifications=tuple(technical_raw.get("specifications", [])),
                fields=dict(technical_raw.get("fields", {})),
            ),
            model_reference=MaterialModelReference(
                model_id=str(model_ref_raw.get("model_id", "")),
                document_id=str(model_ref_raw.get("document_id", "")),
                concept_id=str(model_ref_raw.get("concept_id", "")),
            ),
            traceability=MaterialTraceability(
                process_id=UUID(str(traceability_raw["process_id"])),
                document_id=str(traceability_raw.get("document_id", "")),
                model_id=str(traceability_raw.get("model_id", "")),
                concept_id=str(traceability_raw.get("concept_id", "")),
                document_reference=str(traceability_raw.get("document_reference", "")),
                canonical_reference=str(traceability_raw.get("canonical_reference", "")),
                extraction_reference=str(traceability_raw.get("extraction_reference", "")),
                source_reference=str(traceability_raw.get("source_reference", "")),
                adapter_name=str(traceability_raw.get("adapter_name", "")),
                format_type=str(traceability_raw.get("format_type", "")),
                original_preserved=bool(traceability_raw.get("original_preserved", True)),
            ),
            concept_kind=str(payload.get("concept_kind", "")),
            status=MaterialClassificationStatus(str(payload.get("status", "classified"))),
            metadata=dict(payload.get("metadata", {})),
        )

    def _parse_service(self, payload: dict[str, Any]) -> ServiceRecord:
        if not isinstance(payload, dict):
            raise ClassificationCatalogAccessError("Cada servicio debe ser un diccionario")

        commercial_raw = payload.get("commercial_information", {})
        technical_raw = payload.get("technical_information", {})
        model_ref_raw = payload.get("model_reference", {})
        traceability_raw = payload.get("traceability", {})

        return ServiceRecord(
            service_id=str(payload["service_id"]),
            concept_id=str(payload["concept_id"]),
            original_name=str(payload.get("original_name", "")),
            description=str(payload.get("description", "")),
            service_scope=str(payload.get("service_scope", "")),
            unit=str(payload.get("unit", "")),
            quantity=str(payload.get("quantity", "")),
            commercial_information=ServiceCommercialInformation(
                unit_price=str(commercial_raw.get("unit_price", "")),
                currency=str(commercial_raw.get("currency", "")),
                fields=dict(commercial_raw.get("fields", {})),
            ),
            technical_information=ServiceTechnicalInformation(
                specifications=tuple(technical_raw.get("specifications", [])),
                fields=dict(technical_raw.get("fields", {})),
            ),
            model_reference=ServiceModelReference(
                model_id=str(model_ref_raw.get("model_id", "")),
                document_id=str(model_ref_raw.get("document_id", "")),
                concept_id=str(model_ref_raw.get("concept_id", "")),
            ),
            traceability=ServiceTraceability(
                process_id=UUID(str(traceability_raw["process_id"])),
                document_id=str(traceability_raw.get("document_id", "")),
                model_id=str(traceability_raw.get("model_id", "")),
                concept_id=str(traceability_raw.get("concept_id", "")),
                document_reference=str(traceability_raw.get("document_reference", "")),
                canonical_reference=str(traceability_raw.get("canonical_reference", "")),
                extraction_reference=str(traceability_raw.get("extraction_reference", "")),
                source_reference=str(traceability_raw.get("source_reference", "")),
                adapter_name=str(traceability_raw.get("adapter_name", "")),
                format_type=str(traceability_raw.get("format_type", "")),
                original_preserved=bool(traceability_raw.get("original_preserved", True)),
            ),
            concept_kind=str(payload.get("concept_kind", "")),
            status=ServiceClassificationStatus(str(payload.get("status", "classified"))),
            metadata=dict(payload.get("metadata", {})),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_source_catalogs": False,
            "accesses_original_documents": False,
            "material_required_fields": list(self.MATERIAL_REQUIRED_FIELDS),
            "service_required_fields": list(self.SERVICE_REQUIRED_FIELDS),
        }
