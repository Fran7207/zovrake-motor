"""
Utilidad de certificación del Pipeline documental completo.

Ejecuta las etapas 2.1–2.9 en secuencia para validación integral.
No introduce lógica de negocio ni nuevos motores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest
from zovrake_motor.comprehension.extraction.models import AdapterDocumentContext
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest
from zovrake_motor.comprehension.service import ComprehensionService


@dataclass(frozen=True)
class ComprehensionPipelineCertificationResult:
    """Resultado de la ejecución certificada del Pipeline documental."""

    process_id: UUID
    document_id: str
    validation_passed: bool
    recognition_passed: bool
    extraction_passed: bool
    canonical_passed: bool
    internal_model_passed: bool
    indexing_passed: bool
    context_integration_passed: bool
    traceability_intact: bool
    document_unmodified: bool
    context_associated: bool
    stages_executed: int
    technical_observations: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.validation_passed
            and self.recognition_passed
            and self.extraction_passed
            and self.canonical_passed
            and self.internal_model_passed
            and self.indexing_passed
            and self.context_integration_passed
            and self.traceability_intact
            and self.document_unmodified
            and self.context_associated
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "complete": self.complete,
            "validation_passed": self.validation_passed,
            "recognition_passed": self.recognition_passed,
            "extraction_passed": self.extraction_passed,
            "canonical_passed": self.canonical_passed,
            "internal_model_passed": self.internal_model_passed,
            "indexing_passed": self.indexing_passed,
            "context_integration_passed": self.context_integration_passed,
            "traceability_intact": self.traceability_intact,
            "document_unmodified": self.document_unmodified,
            "context_associated": self.context_associated,
            "stages_executed": self.stages_executed,
            "technical_observations": list(self.technical_observations),
        }


def run_full_comprehension_pipeline(
    service: ComprehensionService,
    *,
    process_id: UUID,
    document_id: str = "DOC-CERT",
    detalles_requerimiento: str = "Detalles del requerimiento para certificación integral del módulo.",
    requirement_code: str = "REQ-CERT",
) -> ComprehensionPipelineCertificationResult:
    """
    Ejecuta el Pipeline documental completo (2.1–2.9) sin interrupciones.

    Flujo: Validación → Reconocimiento → Extracción → Canónica →
    Modelo Interno → Indexación → Integración de Contexto.
    """
    observations: list[str] = []
    stages = 0

    validation = service.validate_document(
        DocumentValidationRequest(
            process_id=process_id,
            document_id=document_id,
            format_type="pdf",
            file_size_bytes=2048,
        ),
    )
    stages += 1
    validation_passed = validation.status.value == "passed"

    recognition = service.recognize_document(
        DocumentRecognitionRequest(
            process_id=process_id,
            document_id=document_id,
            file_name=f"{document_id.lower()}.pdf",
        ),
    )
    stages += 1
    recognition_passed = recognition.recognized

    adapter_name = recognition.suggested_adapter or "pdf_adapter"
    adapter_context = AdapterDocumentContext(
        process_id=process_id,
        document_id=document_id,
        adapter_name=adapter_name,
        format_type=recognition.identified_format.value if recognition.identified_format else "pdf",
        document_reference=f"adapter://{adapter_name}/{document_id}",
        original_preserved=True,
        metadata={
            "text_content": "Contenido certificado para pipeline integral",
            "format_type": "pdf",
            "provider_name": "Proveedor Certificación",
            "commercial_currency": "USD",
        },
    )

    extraction = service.extract_content(
        ContentExtractionRequest(
            process_id=process_id,
            document_id=document_id,
            adapter_context=adapter_context,
        ),
    )
    stages += 1
    extraction_passed = extraction.original_preserved and len(extraction.extracted_text) > 0

    canonical = service.build_canonical_representation(
        CanonicalRepresentationRequest(
            process_id=process_id,
            extraction_result=extraction,
        ),
    )
    stages += 1
    canonical_passed = canonical.representation.immutable and canonical.original_preserved
    model_snapshot_before = None

    model_result = service.build_internal_model(
        InternalModelBuildRequest(
            process_id=process_id,
            canonical_result=canonical,
            requirement_code=requirement_code,
        ),
    )
    stages += 1
    model_snapshot_before = model_result.model.to_dict()
    internal_model_passed = model_result.model.immutable and model_result.original_preserved

    index_result = service.index_document(
        DocumentIndexRequest(
            process_id=process_id,
            model_result=model_result,
            validation_reference=f"dvf://{document_id}",
        ),
    )
    stages += 1
    indexing_passed = index_result.index_id.startswith("dki://")

    context_result = service.integrate_context(
        ContextIntegrationRequest(
            process_id=process_id,
            detalles_requerimiento=detalles_requerimiento,
            index_result=index_result,
            model_result=model_result,
            requirement_code=requirement_code,
        ),
    )
    stages += 1
    context_integration_passed = context_result.document_unmodified
    context_associated = (
        context_result.association.traceability.index_id == index_result.index_id
    )

    document_unmodified = model_result.model.to_dict() == model_snapshot_before

    trace = context_result.association.traceability
    model_trace = model_result.model.traceability
    traceability_intact = (
        trace.document_id == model_trace.document_id
        and trace.model_id == model_trace.model_id
        and trace.canonical_reference_id == model_trace.canonical_reference_id
        and trace.extraction_reference_id == model_trace.extraction_reference_id
        and trace.document_reference == model_trace.document_reference
        and index_result.entry.traceability.model_id == model_trace.model_id
    )

    observations.extend(
        (
            f"stages_executed={stages}",
            f"validation_status={validation.status.value}",
            f"recognition_format={recognition.identified_format}",
            f"index_id={index_result.index_id}",
            f"context_id={context_result.context_id}",
            "pipeline_certification_complete=True" if stages == 7 else "pipeline_certification_partial=True",
        ),
    )

    return ComprehensionPipelineCertificationResult(
        process_id=process_id,
        document_id=document_id,
        validation_passed=validation_passed,
        recognition_passed=recognition_passed,
        extraction_passed=extraction_passed,
        canonical_passed=canonical_passed,
        internal_model_passed=internal_model_passed,
        indexing_passed=indexing_passed,
        context_integration_passed=context_integration_passed,
        traceability_intact=traceability_intact,
        document_unmodified=document_unmodified,
        context_associated=context_associated,
        stages_executed=stages,
        technical_observations=tuple(observations),
    )
