"""Gateway de consumo del catálogo definitivo y reporte de validación."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_CATALOG_REQUIRED_FIELDS,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.exceptions import (
    ComparativeQualityInputAccessError,
)


@dataclass(frozen=True)
class ComparativeQualityInputView:
    """Vista de solo lectura para auditoría de calidad del PM6."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    models: tuple[dict[str, Any], ...]
    pm6_definitive_output_contract: bool
    pm7_input_contract_prepared: bool
    domain_model_preserved: bool
    source_data_preserved: bool
    validation_report_id: str
    validation_status: str
    validation_check_sets_count: int
    validation_findings_count: int
    validation_report_prepared: bool
    raw_definitive_catalog: dict[str, Any]
    raw_validation_report: dict[str, Any]
    pipeline_snapshot: tuple[dict[str, Any], ...] = ()


class ComparativeQualityInputGateway:
    """
    Gateway de consumo para el CQF.

    Valida insumos sin acceder a documentos originales ni modificar datos.
    """

    CATALOG_REQUIRED: tuple[str, ...] = PM6_DEFINITIVE_CATALOG_REQUIRED_FIELDS
    REPORT_REQUIRED: tuple[str, ...] = (
        "report_id",
        "process_id",
        "model_id",
        "document_id",
    )

    def validate(
        self,
        definitive_catalog: dict[str, Any],
        validation_report: dict[str, Any],
        *,
        pipeline_snapshot: list[dict[str, Any]] | None = None,
    ) -> ComparativeQualityInputView:
        if not isinstance(definitive_catalog, dict):
            raise ComparativeQualityInputAccessError(
                "El catálogo de modelos definitivos debe ser un diccionario",
            )
        if not isinstance(validation_report, dict):
            raise ComparativeQualityInputAccessError(
                "El reporte de validación debe ser un diccionario",
            )

        missing_catalog = [
            field for field in self.CATALOG_REQUIRED if field not in definitive_catalog
        ]
        if missing_catalog:
            raise ComparativeQualityInputAccessError(
                "Campos obligatorios ausentes en catálogo definitivo: "
                + ", ".join(missing_catalog),
            )

        missing_report = [
            field for field in self.REPORT_REQUIRED if field not in validation_report
        ]
        if missing_report:
            raise ComparativeQualityInputAccessError(
                "Campos obligatorios ausentes en reporte de validación: "
                + ", ".join(missing_report),
            )

        if not bool(definitive_catalog.get("pm6_definitive_output_contract", False)):
            raise ComparativeQualityInputAccessError(
                "El catálogo no cumple el contrato oficial de salida del PM6",
            )

        if not bool(validation_report.get("comparative_quality_framework_prepared", True)):
            raise ComparativeQualityInputAccessError(
                "El reporte de validación no está preparado para auditoría de calidad",
            )

        models_raw = definitive_catalog.get("models", [])
        if not isinstance(models_raw, list):
            raise ComparativeQualityInputAccessError("models debe ser una lista")

        snapshot_tuple: tuple[dict[str, Any], ...] = ()
        if pipeline_snapshot is not None:
            if not isinstance(pipeline_snapshot, list):
                raise ComparativeQualityInputAccessError(
                    "pipeline_snapshot debe ser una lista",
                )
            snapshot_tuple = tuple(dict(item) for item in pipeline_snapshot)

        check_sets = validation_report.get("check_sets", [])
        global_findings = validation_report.get("global_findings", [])
        check_sets_count = int(
            validation_report.get("check_sets_count", len(check_sets)),
        )
        findings_count = int(
            validation_report.get("global_findings_count", len(global_findings)),
        )

        return ComparativeQualityInputView(
            catalog_id=str(definitive_catalog["catalog_id"]),
            process_id=UUID(str(definitive_catalog["process_id"])),
            model_id=str(definitive_catalog["model_id"]),
            document_id=str(definitive_catalog["document_id"]),
            models=tuple(dict(model) for model in models_raw),
            pm6_definitive_output_contract=True,
            pm7_input_contract_prepared=bool(
                definitive_catalog.get("pm7_input_contract_prepared", True),
            ),
            domain_model_preserved=bool(
                definitive_catalog.get("domain_model_preserved", True),
            ),
            source_data_preserved=bool(
                definitive_catalog.get("source_data_preserved", True),
            ),
            validation_report_id=str(validation_report["report_id"]),
            validation_status=str(validation_report.get("status", "validated")),
            validation_check_sets_count=check_sets_count,
            validation_findings_count=findings_count,
            validation_report_prepared=bool(
                validation_report.get("comparative_quality_framework_prepared", True),
            ),
            raw_definitive_catalog=definitive_catalog,
            raw_validation_report=validation_report,
            pipeline_snapshot=snapshot_tuple,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_definitive_catalog": False,
            "modifies_validation_report": False,
            "accesses_source_files": False,
            "required_catalog_fields": list(self.CATALOG_REQUIRED),
            "required_report_fields": list(self.REPORT_REQUIRED),
        }
