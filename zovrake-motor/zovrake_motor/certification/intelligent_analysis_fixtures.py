"""
Fixtures de certificación para el Módulo de Razonamiento Inteligente.

Construye el Modelo Comparativo Definitivo (entrada PM6) reutilizando
la cadena certificada del PM6 sin modificar motores funcionales.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.certification.comparative_tables_pipeline import (
    run_full_comparative_tables_pipeline,
)
from zovrake_motor.comparative_tables.service import ComparativeTablesService


def build_definitive_catalog_for_certification(
    *,
    process_id: UUID,
    document_id: str = "DOC-PM7-CERT",
    requirement_code: str = "REQ-PM7-CERT",
    certification_providers: tuple[str, ...] = ("PROV-001", "PROV-002"),
) -> tuple[dict[str, Any], str, str]:
    """
    Construye el Modelo Comparativo Definitivo certificado para PM7.

    Retorna (definitive_catalog, document_id, model_id).
    """
    service = ComparativeTablesService()
    service.initialize()
    result = run_full_comparative_tables_pipeline(
        service,
        process_id=process_id,
        document_id=document_id,
        requirement_code=requirement_code,
        certification_providers=certification_providers,
    )
    if not result.complete:
        raise RuntimeError("La cadena PM6 no produjo un Modelo Comparativo Definitivo certificado")

    definitive_catalog = result.definitive_catalog
    return (
        definitive_catalog,
        str(definitive_catalog.get("document_id", document_id)),
        str(definitive_catalog.get("model_id", "")),
    )
